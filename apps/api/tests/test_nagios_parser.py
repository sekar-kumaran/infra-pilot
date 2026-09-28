import pytest
from app.integrations.providers.nagios.parser import NagiosStatusParser
from app.integrations.providers.nagios.errors import NagiosParserError

def test_parse_valid_status_dat():
    content = """
    hoststatus {
        host_name=server01
        current_state=0
        plugin_output=PING OK
        last_check=1672531200
        last_state_change=1672531200
    }
    servicestatus {
        host_name=server01
        service_description=HTTP
        current_state=2
        plugin_output=HTTP CRITICAL
        last_state_change=1672531300
    }
    """
    hosts, services = NagiosStatusParser.parse(content)
    
    assert len(hosts) == 1
    assert hosts[0].host_name == "server01"
    assert hosts[0].current_state == 0
    assert hosts[0].plugin_output == "PING OK"
    
    assert len(services) == 1
    assert services[0].service_description == "HTTP"
    assert services[0].current_state == 2
    assert services[0].plugin_output == "HTTP CRITICAL"

def test_parse_empty_content():
    with pytest.raises(NagiosParserError):
        NagiosStatusParser.parse("")

def test_parse_malformed_ignores_invalid_blocks():
    content = """
    hoststatus {
        host_name=server02
    """
    hosts, services = NagiosStatusParser.parse(content)
    # Shouldn't crash, just returns empty because block wasn't closed properly or couldn't parse
    assert len(hosts) == 0
    assert len(services) == 0

def test_parse_tolerates_missing_optional_fields():
    content = """
    hoststatus {
        host_name=server03
    }
    """
    hosts, services = NagiosStatusParser.parse(content)
    assert len(hosts) == 1
    assert hosts[0].host_name == "server03"
    assert hosts[0].current_state == 0 # default
