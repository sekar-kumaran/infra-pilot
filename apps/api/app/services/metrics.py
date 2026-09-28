from prometheus_client import Counter, Histogram, Gauge

# Ingestion
EVENTS_RECEIVED_TOTAL = Counter('events_received_total', 'Total number of raw events received', ['provider', 'integration_id'])
EVENTS_REJECTED_TOTAL = Counter('events_rejected_total', 'Total number of raw events rejected', ['provider'])
EVENTS_DEDUPLICATED_TOTAL = Counter('events_deduplicated_total', 'Total number of raw events deduplicated (idempotent)', ['provider'])

# Processing
EVENTS_PROCESSED_TOTAL = Counter('events_processed_total', 'Total number of raw events successfully processed', ['provider'])
EVENTS_FAILED_TOTAL = Counter('events_failed_total', 'Total number of raw events that failed processing', ['provider'])
EVENT_PROCESSING_DURATION = Histogram('event_processing_duration_seconds', 'Time spent processing a raw event', ['provider'])

# Alerts
ALERTS_CREATED_TOTAL = Counter('alerts_created_total', 'Total number of alerts created', ['provider', 'severity'])
ALERTS_DEDUPLICATED_TOTAL = Counter('alerts_deduplicated_total', 'Total number of alerts deduplicated', ['provider'])
ALERTS_RESOLVED_TOTAL = Counter('alerts_resolved_total', 'Total number of alerts resolved', ['provider'])

# Incidents
INCIDENTS_CREATED_TOTAL = Counter('incidents_created_total', 'Total number of incidents created', ['severity'])
INCIDENTS_RESOLVED_TOTAL = Counter('incidents_resolved_total', 'Total number of incidents resolved', ['severity'])
INCIDENTS_ESCALATED_TOTAL = Counter('incidents_escalated_total', 'Total number of incidents where severity was escalated')
INCIDENT_PROCESSING_DURATION = Histogram('incident_processing_duration_seconds', 'Time spent updating incident state', ['action'])

# Celery
TASK_SUCCESS_TOTAL = Counter('task_success_total', 'Total number of celery tasks successfully completed', ['task_name'])
TASK_FAILURE_TOTAL = Counter('task_failure_total', 'Total number of celery task permanent failures', ['task_name'])
TASK_RETRY_TOTAL = Counter('task_retry_total', 'Total number of celery task retries', ['task_name'])
TASK_DURATION = Histogram('task_duration_seconds', 'Time spent executing a celery task', ['task_name'])

# System gauges
ACTIVE_ALERTS_GAUGE = Gauge('active_alerts_total', 'Current number of active alerts')
OPEN_INCIDENTS_GAUGE = Gauge('open_incidents_total', 'Current number of open incidents')
CRITICAL_INCIDENTS_GAUGE = Gauge('critical_incidents_total', 'Current number of open critical incidents')
