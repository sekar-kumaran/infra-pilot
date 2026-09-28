from typing import Optional
from app.adapters.automation.base import AutomationExecutor
from app.adapters.automation.kubernetes.executor import KubernetesAutomationExecutor
from app.adapters.automation.aws.executor import AWSAutomationExecutor
from app.adapters.automation.docker.executor import DockerAutomationExecutor
from app.adapters.automation.ansible.executor import AnsibleAutomationExecutor

class ExecutorFactory:
    @staticmethod
    def get_executor(executor_name: str) -> Optional[AutomationExecutor]:
        if executor_name == "KubernetesAutomationExecutor":
            return KubernetesAutomationExecutor()
        elif executor_name == "AWSAutomationExecutor":
            return AWSAutomationExecutor()
        elif executor_name == "DockerAutomationExecutor":
            return DockerAutomationExecutor()
        elif executor_name == "AnsibleAutomationExecutor":
            return AnsibleAutomationExecutor()
        return None
