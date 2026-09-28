from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import UUID4

from app.database.session import get_db
from app.models.application import Application
from app.models.resource import InfrastructureResource
from app.models.incidents import Incident, IncidentEvent
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.schemas.inventory import InfrastructureResourceResponse

router = APIRouter()

@router.get("/", response_model=List[ApplicationResponse])
def list_applications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    apps = db.query(Application).offset(skip).limit(limit).all()
    
    # Simple manual population for counts
    # In a real heavy app, this would be a subquery or joined load
    result = []
    for app in apps:
        resource_count = db.query(InfrastructureResource).filter(InfrastructureResource.application_id == app.id).count()
        # count incidents on resources of this app
        incident_count = db.query(Incident).join(
            InfrastructureResource, 
            InfrastructureResource.id == Incident.primary_resource_id
        ).filter(InfrastructureResource.application_id == app.id).count()
        
        # We assume one incident event per resource per incident roughly for this demo
        app_resp = ApplicationResponse.model_validate(app)
        app_resp.resource_count = resource_count
        app_resp.incidents_count = incident_count
        result.append(app_resp)
        
    return result

@router.post("/", response_model=ApplicationResponse, status_code=201)
def create_application(
    app_in: ApplicationCreate,
    db: Session = Depends(get_db)
):
    db_app = Application(**app_in.model_dump())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    
    app_resp = ApplicationResponse.model_validate(db_app)
    app_resp.resource_count = 0
    app_resp.incidents_count = 0
    return app_resp

@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(
    app_id: UUID4,
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    resource_count = db.query(InfrastructureResource).filter(InfrastructureResource.application_id == app.id).count()
    app_resp = ApplicationResponse.model_validate(app)
    app_resp.resource_count = resource_count
    app_resp.incidents_count = 0
    return app_resp

@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: UUID4,
    app_in: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    update_data = app_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(app, key, value)
        
    db.commit()
    db.refresh(app)
    
    resource_count = db.query(InfrastructureResource).filter(InfrastructureResource.application_id == app.id).count()
    app_resp = ApplicationResponse.model_validate(app)
    app_resp.resource_count = resource_count
    return app_resp

@router.delete("/{app_id}", status_code=204)
def delete_application(
    app_id: UUID4,
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    # resources are SET NULL automatically by DB constraint
    db.delete(app)
    db.commit()

@router.get("/{app_id}/resources", response_model=List[InfrastructureResourceResponse])
def get_application_resources(
    app_id: UUID4,
    db: Session = Depends(get_db)
):
    resources = db.query(InfrastructureResource).filter(InfrastructureResource.application_id == app_id).all()
    return resources
