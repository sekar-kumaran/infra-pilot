import pytest
import uuid
from sqlalchemy.orm import Session
from app.services.remediation_executor import RemediationExecutionService
from app.models.remediation import RemediationPlan
from app.models.enums import ApprovalStatus, AutomationExecutionStatus

def test_remediation_execution_rejected_if_not_approved(mocker):
    # Mock DB session
    mock_db = mocker.MagicMock(spec=Session)
    
    # Create a plan that requires approval but is not approved
    plan = RemediationPlan(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        strategy="restart_instance",
        target_resource_id=uuid.uuid4(),
        provider="aws",
        selected_action="aws_reboot_instance",
        requires_approval=True,
        approval_status=ApprovalStatus.PENDING.value,
        execution_status=AutomationExecutionStatus.PENDING.value
    )
    
    # Setup mock query chain
    mock_query = mocker.MagicMock()
    mock_filter = mocker.MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = plan
    
    # Init service
    service = RemediationExecutionService(mock_db)
    
    # Execute should raise ValueError
    with pytest.raises(ValueError, match="Remediation requires approval but status is PENDING"):
        service.execute_remediation_plan(plan.id)

def test_remediation_execution_proceeds_if_approved(mocker):
    # Mock DB session
    mock_db = mocker.MagicMock(spec=Session)
    
    # Create a plan that requires approval and is approved
    plan = RemediationPlan(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        strategy="restart_instance",
        target_resource_id=uuid.uuid4(),
        provider="aws",
        selected_action="aws_reboot_instance",
        requires_approval=True,
        approval_status=ApprovalStatus.APPROVED.value,
        execution_status=AutomationExecutionStatus.PENDING.value
    )
    
    # Mock dependencies
    mock_incident = mocker.MagicMock()
    mock_incident.status = "OPEN"
    mock_resource = mocker.MagicMock()
    
    # Setup mock query chain to return plan, then incident, then resource
    mock_query = mocker.MagicMock()
    mock_filter = mocker.MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    
    # filter.first() is called three times
    mock_filter.first.side_effect = [plan, mock_incident, mock_resource]
    
    # Mock ProviderResolver
    mocker.patch('app.services.remediation_executor.ProviderResolver.resolve_provider_for_strategy', return_value=mocker.MagicMock(executor="MockExecutor", action="mock_action"))
    
    # Mock ExecutorFactory
    mock_executor = mocker.MagicMock()
    mock_executor.execute.return_value = (True, {}, "")
    mock_executor.verify.return_value = (True, {}, "")
    mocker.patch('app.services.remediation_executor.ExecutorFactory.get_executor', return_value=mock_executor)
    
    # Init service
    service = RemediationExecutionService(mock_db)
    
    # Execute should return True
    success = service.execute_remediation_plan(plan.id)
    assert success is True
    
    # Verify execution was called
    mock_executor.execute.assert_called_once()
