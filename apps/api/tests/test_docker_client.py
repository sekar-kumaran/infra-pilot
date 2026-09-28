"""
Unit tests for DockerClient.
Tests cover: connection, health check, authentication failure, timeout, 404, resource listing.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests

from app.integrations.providers.docker.client import DockerClient
from app.integrations.providers.docker.schemas import DockerIntegrationConfig, DockerIntegrationSecrets
from app.integrations.providers.docker.errors import (
    DockerConnectionError, DockerAuthenticationError, DockerNotFoundError,
    DockerAPIError, DockerTimeoutError
)


@pytest.fixture
def client():
    config = DockerIntegrationConfig(base_url="http://docker-test:2375", timeout_seconds=5)
    return DockerClient(config=config, secrets=DockerIntegrationSecrets())


def _mock_response(status_code=200, json_data=None, text="OK", content_type=None):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    if json_data is not None:
        mock_resp.json.return_value = json_data
        mock_resp.text = ""
        mock_resp.headers = {"Content-Type": content_type or "application/json"}
    else:
        mock_resp.json.side_effect = Exception("No JSON")
        mock_resp.text = text
        mock_resp.headers = {"Content-Type": content_type or "text/plain"}
    return mock_resp


class TestDockerHealthCheck:
    def test_healthy(self, client):
        with patch.object(client.session, "get", return_value=_mock_response(200, text="OK")):
            assert client.check_health() is True

    def test_unhealthy_connection_error(self, client):
        with patch.object(client.session, "get", side_effect=requests.exceptions.ConnectionError("refused")):
            assert client.check_health() is False

    def test_unhealthy_401(self, client):
        with patch.object(client.session, "get", return_value=_mock_response(401, text="Unauthorized")):
            assert client.check_health() is False


class TestDockerContainerListing:
    def test_list_containers(self, client):
        containers = [{"Id": "abc123", "Names": ["/web"], "State": "running", "Status": "Up", "Image": "nginx"}]
        with patch.object(client.session, "get", return_value=_mock_response(200, json_data=containers)):
            result = client.list_containers()
        assert len(result) == 1
        assert result[0]["Id"] == "abc123"

    def test_list_containers_authentication_failure(self, client):
        with patch.object(client.session, "get", return_value=_mock_response(401, text="Unauthorized")):
            with pytest.raises(DockerAuthenticationError):
                client.list_containers()

    def test_list_containers_not_found(self, client):
        with patch.object(client.session, "get", return_value=_mock_response(404, text="Not Found")):
            with pytest.raises(DockerNotFoundError):
                client.list_containers()

    def test_list_containers_timeout(self, client):
        with patch.object(client.session, "get", side_effect=requests.exceptions.Timeout()):
            with pytest.raises(DockerTimeoutError):
                client.list_containers()

    def test_list_containers_connection_error(self, client):
        with patch.object(client.session, "get", side_effect=requests.exceptions.ConnectionError("refused")):
            with pytest.raises(DockerConnectionError):
                client.list_containers()


class TestDockerMutations:
    def test_restart_container(self, client):
        with patch.object(client.session, "post", return_value=_mock_response(204, text="")):
            # Should not raise
            client.restart_container("abc123")

    def test_start_container_500(self, client):
        with patch.object(client.session, "post", return_value=_mock_response(500, text="server error")):
            with pytest.raises(DockerAPIError):
                client.start_container("abc123")

    def test_stop_container_not_found(self, client):
        with patch.object(client.session, "post", return_value=_mock_response(404, text="Not Found")):
            with pytest.raises(DockerNotFoundError):
                client.stop_container("abc123")


class TestDockerLogs:
    def test_bounded_log_retrieval(self, client):
        with patch.object(client.session, "get", return_value=_mock_response(200, text="log line\nanother line")):
            logs = client.get_container_logs("abc123", max_lines=50)
        assert "log line" in logs

    def test_logs_timeout(self, client):
        with patch.object(client.session, "get", side_effect=requests.exceptions.Timeout()):
            with pytest.raises(DockerTimeoutError):
                client.get_container_logs("abc123")
