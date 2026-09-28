import os
import time
import random
from fastapi import FastAPI, Response, Request
from prometheus_client import generate_latest, Counter, Histogram
from pydantic import BaseModel

app = FastAPI(title="InfraPilot DevOps Lab")

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration)
    
    return response

@app.get("/")
def read_root():
    return {"message": "InfraPilot DevOps Lab Backend"}

@app.get("/health")
def health_check():
    return {"status": "ok", "db": "connected"}

class Item(BaseModel):
    name: str
    description: str

items = []

@app.get("/api/items")
def get_items():
    # Simulate some latency
    time.sleep(random.uniform(0.01, 0.1))
    return items

@app.post("/api/items")
def create_item(item: Item):
    items.append(item.dict())
    return {"status": "created", "item": item}

@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(), media_type="text/plain")
