from app.integrations.models import IntegrationCapability

AWS_CAPABILITIES = IntegrationCapability(
    resource_discovery=True,
    resource_read=True,
    health_check=True,
    metrics_read=False,
    logs_read=False,
    alerts_read=False
)
