import os
import json
import time
import subprocess
import logging
from typing import Dict, Any

from .errors import AnsibleExecutionError, AnsibleTimeoutError
from .models import AnsibleExecutionResult
from .sanitizer import redact_sensitive_data

logger = logging.getLogger(__name__)

class AnsibleClient:
    """
    Executes Ansible playbooks securely.
    """
    
    def __init__(self, executable_path: str = "ansible-playbook"):
        self.executable_path = executable_path
        
    def execute_playbook(self, 
                         playbook_path: str, 
                         inventory_path: str, 
                         target_host: str, 
                         extra_vars: Dict[str, Any],
                         timeout_seconds: int = 300) -> AnsibleExecutionResult:
        """
        Runs `ansible-playbook` via subprocess, capturing structured output.
        """
        # Validate paths basically
        if not os.path.exists(playbook_path):
            raise AnsibleExecutionError(f"Playbook path does not exist: {playbook_path}")
        if not os.path.exists(inventory_path):
            logger.warning(f"Inventory path does not exist: {inventory_path}. Proceeding, but Ansible may fail.")
            
        args = [
            self.executable_path,
            playbook_path,
            "-i", inventory_path,
            "--limit", target_host,
            "--extra-vars", json.dumps(extra_vars)
        ]
        
        # Pull any credentials from env if real provider configs are set
        # This allows test_real_ansible to pass them in securely.
        env = os.environ.copy()
        env["HOME"] = "/tmp"
        env["ANSIBLE_LOCAL_TEMP"] = "/tmp"
        env["ANSIBLE_REMOTE_TEMP"] = "/tmp"
        
        # To avoid unbounded stdout accumulation and for easier parsing, we could ask for JSON stdout.
        # But for safety and generic support, we capture as text.
        
        logger.info(f"Executing ansible playbook {os.path.basename(playbook_path)} against {target_host}")
        
        start_time = time.time()
        try:
            # We strictly avoid shell=True
            process = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
                check=False
            )
            
            duration = time.time() - start_time
            
            # Scrub output
            safe_stdout = redact_sensitive_data(process.stdout)
            safe_stderr = redact_sensitive_data(process.stderr)
            
            success = process.returncode == 0
            
            return AnsibleExecutionResult(
                success=success,
                return_code=process.returncode,
                stdout=safe_stdout,
                stderr=safe_stderr,
                duration_seconds=duration,
                error_message=None if success else "Ansible execution returned non-zero exit code"
            )
            
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            logger.error(f"Ansible execution timed out after {duration} seconds")
            
            safe_stdout = redact_sensitive_data(e.stdout.decode('utf-8') if e.stdout else "")
            safe_stderr = redact_sensitive_data(e.stderr.decode('utf-8') if e.stderr else "")
            
            raise AnsibleTimeoutError(f"Execution timed out after {timeout_seconds}s")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Ansible subprocess failed: {str(e)}")
            raise AnsibleExecutionError(f"Subprocess failure: {str(e)}")
