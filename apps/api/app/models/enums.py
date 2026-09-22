from enum import Enum

class EnvironmentType(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    OTHER = "OTHER"

class ResourceType(str, Enum):
    HOST = "HOST"
    VM = "VM"
    CONTAINER = "CONTAINER"
    SERVICE = "SERVICE"
    DATABASE = "DATABASE"
    KUBERNETES_CLUSTER = "KUBERNETES_CLUSTER"
    KUBERNETES_NODE = "KUBERNETES_NODE"
    KUBERNETES_WORKLOAD = "KUBERNETES_WORKLOAD"
    NETWORK = "NETWORK"
    LOAD_BALANCER = "LOAD_BALANCER"
    STORAGE = "STORAGE"

class ResourceStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    MAINTENANCE = "MAINTENANCE"

class RelationshipType(str, Enum):
    CONTAINS = "CONTAINS"
    RUNS = "RUNS"
    DEPENDS_ON = "DEPENDS_ON"
    HOSTS = "HOSTS"
    PART_OF = "PART_OF"
    ROUTES_TO = "ROUTES_TO"
    CONNECTS_TO = "CONNECTS_TO"

# This is an enum representing recognized providers.
# It is used for standardization, but the system may technically accept strings
# if we decide not to strictly validate at the DB layer, though API layer will validate.
class ProviderType(str, Enum):
    MANUAL = "manual"
    PROMETHEUS = "prometheus"
    NAGIOS = "nagios"
    GRAFANA = "grafana"
    LOKI = "loki"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    PUPPET = "puppet"
    TEST_PROVIDER = "test_provider"

class IntegrationStatus(str, Enum):
    CONFIGURED = "CONFIGURED"
    VALIDATING = "VALIDATING"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DISABLED = "DISABLED"
    ERROR = "ERROR"

class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    DIAGNOSED = "DIAGNOSED"
    REMEDIATING = "REMEDIATING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    SUPPRESSED = "SUPPRESSED"

class IncidentPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"

class IncidentEventType(str, Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    ALERT_ATTACHED = "ALERT_ATTACHED"
    ALERT_DETACHED = "ALERT_DETACHED"
    STATUS_CHANGED = "STATUS_CHANGED"
    SEVERITY_CHANGED = "SEVERITY_CHANGED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"
    ASSIGNED = "ASSIGNED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DIAGNOSIS_STARTED = "DIAGNOSIS_STARTED"
    DIAGNOSIS_COMPLETED = "DIAGNOSIS_COMPLETED"
    REMEDIATION_STARTED = "REMEDIATION_STARTED"
    REMEDIATION_COMPLETED = "REMEDIATION_COMPLETED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"
    INCIDENT_CLOSED = "INCIDENT_CLOSED"

class RawEventProcessingStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"
