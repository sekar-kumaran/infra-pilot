import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from app.database.session import get_session_factory
from app.models.workflow import OperationWorkflow, WorkflowStep
from app.models.enums import ResourceType

def seed_templates():
    db = get_session_factory()()
    
    templates = [
        {
            "name": "High CPU Remediation - Kubernetes Scale",
            "description": "Automatically scales a Kubernetes deployment when a High CPU alert triggers.",
            "trigger_type": "event",
            "trigger_conditions": [
                {
                    "provider": "prometheus",
                    "severity": "CRITICAL",
                    "resource_type": ResourceType.KUBERNETES_DEPLOYMENT.value,
                    "alert_name": ".*HighCPU.*"
                },
                {
                    "provider": "grafana",
                    "severity": "CRITICAL",
                    "resource_type": ResourceType.KUBERNETES_DEPLOYMENT.value,
                    "alert_name": ".*High CPU.*"
                }
            ],
            "steps": [
                {
                    "sequence": 1,
                    "action": "kubernetes_scale_deployment",
                    "capability": "kubernetes_mutation",
                    "approval_requirement": True,
                    "timeout": 300,
                    "parameters": {"replicas": 3},
                    "verification_strategy": {
                        "type": "provider_metric",
                        "provider": "prometheus",
                        "metric": "kube_deployment_status_replicas_available",
                        "expected_value": 3
                    }
                }
            ]
        },
        {
            "name": "Docker Container Recovery",
            "description": "Restarts a failed Docker container based on Nagios/Prometheus/Grafana alerts.",
            "trigger_type": "event",
            "trigger_conditions": [
                {
                    "severity": "CRITICAL",
                    "resource_type": ResourceType.CONTAINER.value
                }
            ],
            "steps": [
                {
                    "sequence": 1,
                    "action": "docker_restart_container",
                    "capability": "docker_mutation",
                    "approval_requirement": False,
                    "timeout": 120,
                    "verification_strategy": {
                        "type": "native"
                    }
                }
            ]
        },
        {
            "name": "AWS EC2 Recovery",
            "description": "Reboots an unresponsive EC2 instance.",
            "trigger_type": "event",
            "trigger_conditions": [
                {
                    "provider": "aws",
                    "severity": "CRITICAL",
                    "resource_type": ResourceType.CLOUD_INSTANCE.value
                }
            ],
            "steps": [
                {
                    "sequence": 1,
                    "action": "aws_reboot_instance",
                    "capability": "aws_mutation",
                    "approval_requirement": True,
                    "timeout": 600,
                    "verification_strategy": {
                        "type": "native"
                    }
                }
            ]
        }
    ]
    
    for tpl in templates:
        existing = db.query(OperationWorkflow).filter(OperationWorkflow.name == tpl["name"]).first()
        if existing:
            print(f"Skipping {tpl['name']} (already exists)")
            continue
            
        workflow = OperationWorkflow(
            name=tpl["name"],
            description=tpl["description"],
            trigger_type=tpl["trigger_type"],
            trigger_conditions=tpl.get("trigger_conditions", []),
        )
        db.add(workflow)
        db.flush()
        
        for step_data in tpl.get("steps", []):
            step = WorkflowStep(
                workflow_id=workflow.id,
                **step_data
            )
            db.add(step)
            
        db.commit()
        print(f"Seeded template: {tpl['name']}")
        
    db.close()

if __name__ == "__main__":
    seed_templates()
