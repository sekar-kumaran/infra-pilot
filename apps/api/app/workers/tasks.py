from uuid import UUID
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json

from app.workers.celery_app import celery_app
from app.database.session import get_session_factory
from app.models.events import RawEvent
from app.models.enums import RawEventProcessingStatus, FailedEventStatus
from app.models.failed_events import FailedEvent
from app.services.correlation import CorrelationService

logger = logging.getLogger(__name__)

@celery_app.task(
    name="process_raw_event_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300
)
def process_raw_event_task(self, raw_event_id: str):
    logger.info(f"Starting processing for raw event {raw_event_id}")
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        raw_event = db.query(RawEvent).filter(RawEvent.id == UUID(raw_event_id)).first()
        if not raw_event:
            logger.error(f"RawEvent {raw_event_id} not found.")
            return

        if raw_event.processing_status != RawEventProcessingStatus.RECEIVED.value:
            logger.warning(f"RawEvent {raw_event_id} already processed or in progress. Status: {raw_event.processing_status}")
            return
            
        raw_event.processing_status = RawEventProcessingStatus.PROCESSING.value
        db.commit()

        correlation_service = CorrelationService(db)
        
        # 1. Normalize
        alert = correlation_service.normalize_event(raw_event)
        
        # 2. Correlate
        incident = correlation_service.correlate_alert(alert)

        # 3. Evaluate Event Triggers
        from app.services.event_trigger import EventTriggerService
        trigger_service = EventTriggerService(db)
        trigger_service.evaluate_and_trigger(incident)

        # 4. Mark Processed
        raw_event.processing_status = RawEventProcessingStatus.PROCESSED.value
        db.commit()
        logger.info(f"Successfully processed raw event {raw_event_id}. Incident: {incident.id}")

    except Exception as e:
        db.rollback()
        
        # If we have reached the max retries, this is a terminal failure.
        # Check if the task is going to retry
        if self.request.retries < self.max_retries:
            logger.warning(f"Retrying raw event {raw_event_id} due to error: {str(e)}")
            db.close()
            raise e
        
        # Terminal failure
        logger.error(f"Permanent failure processing raw event {raw_event_id} after {self.request.retries} retries: {str(e)}")
        
        # Mark raw event as failed
        if raw_event:
            raw_event.processing_status = RawEventProcessingStatus.FAILED.value
        
        # Create FailedEvent
        failed_event = FailedEvent(
            raw_event_id=raw_event_id,
            task_name=self.name,
            failure_type=type(e).__name__,
            failure_message=str(e),
            retry_count=self.request.retries,
            status=FailedEventStatus.FAILED.value,
            payload_reference=raw_event.payload if raw_event else None
        )
        db.add(failed_event)
        
        try:
            db.commit()
        except SQLAlchemyError as commit_err:
            logger.critical(f"Failed to persist FailedEvent for {raw_event_id}: {str(commit_err)}")
            
        # We do not raise here because it's a permanent failure, we don't want to retry indefinitely.
        return
    finally:
        db.close()


@celery_app.task(
    name="evaluate_automation_policy_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def evaluate_automation_policy_task(self, execution_id: str):
    logger.info(f"Evaluating policy for automation execution {execution_id}")
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        from app.models.automation import AutomationExecution
        from app.services.automation import process_policy_decision
        from app.services.policy_engine import evaluate_automation_policy

        execution = db.query(AutomationExecution).filter(AutomationExecution.id == UUID(execution_id)).first()
        if not execution:
            logger.error(f"AutomationExecution {execution_id} not found.")
            return

        decision, reason = evaluate_automation_policy(db, execution)
        process_policy_decision(db, execution, decision, reason)

        logger.info(f"Policy evaluated for {execution_id}. Decision: {decision.value}. Reason: {reason}")
        
        # If policy APPROVED, we could queue execution
        from app.models.enums import AutomationExecutionStatus
        if execution.status == AutomationExecutionStatus.APPROVED.value:
            execute_automation_task.delay(execution_id)

    except Exception as e:
        logger.error(f"Error evaluating policy for {execution_id}: {str(e)}")
        raise e
    finally:
        db.close()

@celery_app.task(
    name="execute_automation_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def execute_automation_task(self, execution_id: str):
    logger.info(f"Executing automation {execution_id}")
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        from app.models.automation import AutomationExecution
        from app.models.enums import AutomationExecutionStatus, AutomationStepStatus, VerificationStatus
        from app.services.action_registry import ActionRegistry
        import importlib
        import datetime

        execution = db.query(AutomationExecution).filter(AutomationExecution.id == UUID(execution_id)).first()
        if not execution:
            return

        if execution.status not in [AutomationExecutionStatus.APPROVED.value, AutomationExecutionStatus.RUNNING.value]:
            logger.error(f"Cannot execute automation {execution_id} in state {execution.status}")
            return

        execution.status = AutomationExecutionStatus.RUNNING.value
        if not execution.started_at:
            execution.started_at = datetime.datetime.utcnow()
        db.commit()

        # Run steps in order
        steps = execution.step_executions
        # Note: in a real implementation we'd probably spawn child tasks for each step to handle long execution
        # But for Phase 1.10 we will run them synchronously inside this task.
        all_success = True
        
        for step_exec in steps:
            if step_exec.status != AutomationStepStatus.PENDING.value:
                continue

            step_exec.status = AutomationStepStatus.RUNNING.value
            step_exec.started_at = datetime.datetime.utcnow()
            db.commit()

            step = step_exec.playbook_step
            action_def = ActionRegistry.get_action(step.action_name)
            
            if not action_def:
                step_exec.status = AutomationStepStatus.FAILED.value
                step_exec.error_message = f"Unknown action: {step.action_name}"
                step_exec.completed_at = datetime.datetime.utcnow()
                db.commit()
                all_success = False
                if not step.continue_on_failure:
                    break
                continue
            
            try:
                # Instantiate executor
                if action_def.executor_name == "test_executor":
                    from app.adapters.automation.test_executor import TestAutomationExecutor
                    executor = TestAutomationExecutor()
                elif action_def.executor_name == "ansible":
                    from app.adapters.automation.ansible import AnsibleAutomationExecutor
                    executor = AnsibleAutomationExecutor()
                elif action_def.executor_name == "kubernetes":
                    from app.adapters.automation.kubernetes import KubernetesAutomationExecutor
                    executor = KubernetesAutomationExecutor(db)
                elif action_def.executor_name == "docker":
                    from app.adapters.automation.docker import DockerAutomationExecutor
                    executor = DockerAutomationExecutor(db)
                elif action_def.executor_name == "aws":
                    from app.adapters.automation.aws import AWSAutomationExecutor
                    executor = AWSAutomationExecutor()
                else:
                    raise ValueError(f"Unknown executor: {action_def.executor_name}")
                
                # Inject resource if needed
                params = step.parameters.copy() if step.parameters else {}
                if execution.resource_id:
                    from app.models.resources import InfrastructureResource
                    resource = db.query(InfrastructureResource).filter(InfrastructureResource.id == execution.resource_id).first()
                    if resource:
                        params["resource"] = resource
                
                success, output, err = executor.execute(step.action_name, params)
                
                step_exec.completed_at = datetime.datetime.utcnow()
                if success:
                    step_exec.status = AutomationStepStatus.SUCCEEDED.value
                    step_exec.output = output
                else:
                    step_exec.status = AutomationStepStatus.FAILED.value
                    step_exec.error_message = err
                    all_success = False
                    
            except Exception as e:
                step_exec.status = AutomationStepStatus.FAILED.value
                step_exec.error_message = str(e)
                step_exec.completed_at = datetime.datetime.utcnow()
                all_success = False
                
            db.commit()
            
            # Request Verification if configured
            if step_exec.status == AutomationStepStatus.SUCCEEDED.value and step.verification_config:
                from app.models.automation import VerificationResult
                vr = VerificationResult(
                    execution_id=execution.id,
                    step_execution_id=step_exec.id,
                    status=VerificationStatus.PENDING.value,
                    expected_state=step.verification_config
                )
                db.add(vr)
                db.commit()
                
                # trigger verify async
                verify_automation_task.delay(execution.id, str(vr.id))

            if not all_success and not step.continue_on_failure:
                break

        # Finalize Execution
        execution.completed_at = datetime.datetime.utcnow()
        if all_success:
            # We wait for VERIFICATION if there are pending verifications
            from app.models.automation import VerificationResult
            pending_verifs = db.query(VerificationResult).filter(
                VerificationResult.execution_id == execution.id,
                VerificationResult.status == VerificationStatus.PENDING.value
            ).count()
            
            if pending_verifs > 0:
                execution.status = AutomationExecutionStatus.VERIFYING.value
            else:
                execution.status = AutomationExecutionStatus.SUCCEEDED.value
        else:
            execution.status = AutomationExecutionStatus.FAILED.value
            execution.error_message = "One or more steps failed."

        db.commit()
        
        # Incident Timeline update
        if execution.incident_id:
            from app.repositories.incidents import IncidentRepository
            from app.models.enums import IncidentEventType
            
            repo = IncidentRepository(db)
            if execution.status == AutomationExecutionStatus.SUCCEEDED.value:
                repo.create_incident_event({
                    "incident_id": execution.incident_id,
                    "event_type": IncidentEventType.REMEDIATION_COMPLETED.value,
                    "source": "automation",
                    "message": f"Automation {execution.id} succeeded",
                    "event_metadata": {}
                })
            elif execution.status == AutomationExecutionStatus.FAILED.value:
                repo.create_incident_event({
                    "incident_id": execution.incident_id,
                    "event_type": IncidentEventType.REMEDIATION_COMPLETED.value,
                    "source": "automation",
                    "message": f"Automation {execution.id} failed",
                    "event_metadata": {}
                })

    except Exception as e:
        logger.error(f"Error executing automation {execution_id}: {str(e)}")
        raise e
    finally:
        db.close()


@celery_app.task(
    name="verify_automation_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def verify_automation_task(self, execution_id: str, verification_id: str):
    logger.info(f"Verifying automation execution {execution_id}, verification {verification_id}")
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        from app.models.automation import AutomationExecution, VerificationResult
        from app.models.enums import VerificationStatus, AutomationExecutionStatus
        from app.services.action_registry import ActionRegistry

        execution = db.query(AutomationExecution).filter(AutomationExecution.id == UUID(execution_id)).first()
        if not execution:
            return
            
        vr = db.query(VerificationResult).filter(VerificationResult.id == UUID(verification_id)).first()
        if not vr or vr.status != VerificationStatus.PENDING.value:
            return
            
        step_exec = vr.step_execution
        step = step_exec.playbook_step
        action_def = ActionRegistry.get_action(step.action_name)
        
        if not action_def or not action_def.verification_strategy:
            vr.status = VerificationStatus.UNKNOWN.value
            vr.message = "No verification strategy defined for action"
        else:
            try:
                if action_def.executor_name == "test_executor":
                    from app.adapters.automation.test_executor import TestAutomationExecutor
                    executor = TestAutomationExecutor()
                elif action_def.executor_name == "ansible":
                    from app.adapters.automation.ansible import AnsibleAutomationExecutor
                    executor = AnsibleAutomationExecutor()
                elif action_def.executor_name == "kubernetes":
                    from app.adapters.automation.kubernetes import KubernetesAutomationExecutor
                    executor = KubernetesAutomationExecutor(db)
                elif action_def.executor_name == "docker":
                    from app.adapters.automation.docker import DockerAutomationExecutor
                    executor = DockerAutomationExecutor(db)
                elif action_def.executor_name == "aws":
                    from app.adapters.automation.aws import AWSAutomationExecutor
                    executor = AWSAutomationExecutor()
                else:
                    raise ValueError(f"Unknown executor: {action_def.executor_name}")
                    
                # Inject resource if needed
                params = step.parameters.copy() if step.parameters else {}
                if execution.resource_id:
                    from app.models.resources import InfrastructureResource
                    resource = db.query(InfrastructureResource).filter(InfrastructureResource.id == execution.resource_id).first()
                    if resource:
                        params["resource"] = resource
                    
                success, observed, msg = executor.verify(step.action_name, vr.expected_state, params)
                vr.observed_state = observed
                vr.message = msg
                vr.status = VerificationStatus.PASSED.value if success else VerificationStatus.FAILED.value
                
            except Exception as e:
                vr.status = VerificationStatus.FAILED.value
                vr.message = f"Verification error: {str(e)}"
                
        db.commit()
        
        # Check if all verifications for this execution are done
        pending_verifs = db.query(VerificationResult).filter(
            VerificationResult.execution_id == execution.id,
            VerificationResult.status == VerificationStatus.PENDING.value
        ).count()
        
        if pending_verifs == 0 and execution.status == AutomationExecutionStatus.VERIFYING.value:
            # Check if any verification failed
            failed_verifs = db.query(VerificationResult).filter(
                VerificationResult.execution_id == execution.id,
                VerificationResult.status == VerificationStatus.FAILED.value
            ).count()
            
            if failed_verifs > 0:
                execution.status = AutomationExecutionStatus.FAILED.value
                execution.error_message = "Verification failed."
            else:
                execution.status = AutomationExecutionStatus.SUCCEEDED.value
            
            db.commit()
            
            if execution.incident_id:
                from app.repositories.incidents import IncidentRepository
                from app.models.enums import IncidentEventType
                
                repo = IncidentRepository(db)
                if execution.status == AutomationExecutionStatus.SUCCEEDED.value:
                    repo.create_incident_event({
                        "incident_id": execution.incident_id,
                        "event_type": IncidentEventType.VERIFICATION_COMPLETED.value,
                        "source": "automation",
                        "message": f"Automation {execution.id} succeeded and verified",
                        "event_metadata": {}
                    })
                else:
                    repo.create_incident_event({
                        "incident_id": execution.incident_id,
                        "event_type": IncidentEventType.VERIFICATION_COMPLETED.value,
                        "source": "automation",
                        "message": f"Automation {execution.id} verification failed",
                        "event_metadata": {}
                    })
            
    except Exception as e:
        logger.error(f"Error verifying {execution_id}: {str(e)}")
        raise e
    finally:
        db.close()


@celery_app.task(
    name="execute_remediation_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def execute_remediation_task(self, remediation_plan_id: str):
    logger.info(f"Executing remediation plan {remediation_plan_id}")
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    try:
        from app.services.remediation_executor import RemediationExecutionService
        service = RemediationExecutionService(db)
        success = service.execute_remediation_plan(UUID(remediation_plan_id))
        return success
    except Exception as e:
        logger.error(f"Failed to execute remediation plan {remediation_plan_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    name="execute_workflow_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def execute_workflow_task(self, workflow_execution_id: str):
    logger.info(f"Executing workflow {workflow_execution_id}")
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    try:
        from app.services.workflow_engine import WorkflowEngine
        engine = WorkflowEngine(db)
        success = engine.start_execution(UUID(workflow_execution_id))
        return success
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_execution_id}: {str(e)}")
        raise
    finally:
        db.close()

import datetime
from sqlalchemy import or_

@celery_app.task(name="recover_stale_workflows_task")
def recover_stale_workflows_task():
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        from app.models.workflow import WorkflowExecution, WorkflowStepExecution
        from app.models.enums import WorkflowExecutionStatus, WorkflowStepStatus
        from app.services.workflow_engine import WorkflowEngine
        
        # Find executions that have been RUNNING or VERIFYING for more than 10 minutes
        threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
        
        stale_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.status.in_([WorkflowExecutionStatus.RUNNING.value, WorkflowExecutionStatus.VERIFYING.value]),
            WorkflowExecution.updated_at < threshold
        ).all()
        
        engine = WorkflowEngine(db)
        
        for execution in stale_executions:
            # We assume the worker crashed.
            # We can re-trigger the workflow engine which will lock, check state, and resume.
            # But wait, start_execution just picks up current_step_id.
            # Let's transition it to TIMED_OUT or try to resume.
            # For phase 1.23, marking TIMED_OUT is safest.
            
            # Lock the row
            locked_exec = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution.id).with_for_update().first()
            if not locked_exec or locked_exec.status not in [WorkflowExecutionStatus.RUNNING.value, WorkflowExecutionStatus.VERIFYING.value]:
                continue
                
            engine._transition_state(locked_exec, WorkflowExecutionStatus.TIMED_OUT.value)
            locked_exec.failure_reason = "Execution timed out (stale)"
            
            # Mark current step as TIMED_OUT
            if locked_exec.current_step_id:
                step_exec = db.query(WorkflowStepExecution).filter(
                    WorkflowStepExecution.execution_id == locked_exec.id,
                    WorkflowStepExecution.step_id == locked_exec.current_step_id,
                    WorkflowStepExecution.status == WorkflowStepStatus.RUNNING.value
                ).first()
                if step_exec:
                    step_exec.status = WorkflowStepStatus.TIMED_OUT.value
                    step_exec.error = "Step execution timed out"
            db.commit()
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to recover stale workflows: {str(e)}")
    finally:
        db.close()
