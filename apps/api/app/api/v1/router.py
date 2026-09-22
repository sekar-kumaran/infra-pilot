from fastapi import APIRouter
from app.api.v1.endpoints import system, auth, roles, audit, environments, resources, integrations, events, alerts, incidents

api_router = APIRouter()
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(environments.router, prefix="/environments", tags=["environments"])
api_router.include_router(resources.router, prefix="/resources", tags=["Resources"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
