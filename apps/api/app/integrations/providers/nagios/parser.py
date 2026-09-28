import re
import logging
from typing import List, Dict, Any, Tuple
from .schemas import NagiosHostStatus, NagiosServiceStatus
from .errors import NagiosParserError

logger = logging.getLogger(__name__)

class NagiosStatusParser:
    """
    Parses Nagios Core status.dat or similar plain text files.
    """
    
    @classmethod
    def parse(cls, content: str) -> Tuple[List[NagiosHostStatus], List[NagiosServiceStatus]]:
        if not content or not isinstance(content, str):
            raise NagiosParserError("Received empty or invalid status data")
            
        hosts = []
        services = []
        
        # We need to extract blocks like:
        # hoststatus {
        #   host_name=...
        #   ...
        # }
        
        # Simple finite state machine for parsing blocks
        in_block = False
        block_type = None
        current_block_data = {}
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if not in_block:
                if line.endswith('{'):
                    block_type = line.split('{')[0].strip()
                    in_block = True
                    current_block_data = {}
            else:
                if line == '}':
                    # End of block
                    if block_type == 'hoststatus':
                        host = cls._parse_host(current_block_data)
                        if host:
                            hosts.append(host)
                    elif block_type == 'servicestatus':
                        service = cls._parse_service(current_block_data)
                        if service:
                            services.append(service)
                            
                    in_block = False
                    block_type = None
                    current_block_data = {}
                else:
                    # Inside a block, lines are key=value
                    if '=' in line:
                        parts = line.split('=', 1)
                        key = parts[0].strip()
                        value = parts[1].strip()
                        current_block_data[key] = value

        return hosts, services

    @classmethod
    def _parse_host(cls, data: Dict[str, str]) -> NagiosHostStatus:
        try:
            return NagiosHostStatus(
                host_name=data.get("host_name", ""),
                current_state=int(data.get("current_state", 0)),
                plugin_output=data.get("plugin_output", ""),
                last_check=int(data.get("last_check", 0)),
                last_state_change=int(data.get("last_state_change", 0)),
                current_attempt=int(data.get("current_attempt", 1)),
                max_attempts=int(data.get("max_attempts", 1)),
                problem_has_been_acknowledged=int(data.get("problem_has_been_acknowledged", 0)),
                notifications_enabled=int(data.get("notifications_enabled", 1))
            )
        except Exception as e:
            logger.warning(f"Failed to parse hoststatus block: {e}")
            return None

    @classmethod
    def _parse_service(cls, data: Dict[str, str]) -> NagiosServiceStatus:
        try:
            return NagiosServiceStatus(
                host_name=data.get("host_name", ""),
                service_description=data.get("service_description", ""),
                current_state=int(data.get("current_state", 0)),
                plugin_output=data.get("plugin_output", ""),
                last_check=int(data.get("last_check", 0)),
                last_state_change=int(data.get("last_state_change", 0)),
                current_attempt=int(data.get("current_attempt", 1)),
                max_attempts=int(data.get("max_attempts", 1)),
                problem_has_been_acknowledged=int(data.get("problem_has_been_acknowledged", 0)),
                notifications_enabled=int(data.get("notifications_enabled", 1))
            )
        except Exception as e:
            logger.warning(f"Failed to parse servicestatus block: {e}")
            return None
