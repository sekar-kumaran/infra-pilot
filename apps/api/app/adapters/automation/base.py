from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class AutomationExecutor(ABC):
    
    @abstractmethod
    def validate(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate if the executor can handle this action and if parameters are valid."""
        pass
        
    @abstractmethod
    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Execute the action. 
        Returns (success, output, error_message)
        """
        pass
        
    @abstractmethod
    def cancel(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Attempt to cancel an ongoing action."""
        pass
        
    @abstractmethod
    def verify(self, action_name: str, expected_state: Any, parameters: Dict[str, Any]) -> Tuple[bool, Any, str]:
        """
        Verify if the action achieved the expected state.
        Returns (success, observed_state, message)
        """
        pass
