"""
RegWatch API — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import dashboard, alerts, regulations, policies, checks, precheck, audit, events

app = FastAPI(
    title="RegWatch API",
    description="Regulatory compliance monitoring platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/v1", tags=["Dashboard"])
app.include_router(alerts.router, prefix="/v1", tags=["Alerts"])
app.include_router(regulations.router, prefix="/v1", tags=["Regulations"])
app.include_router(policies.router, prefix="/v1", tags=["Policies"])
app.include_router(checks.router, prefix="/v1", tags=["Compliance Checks"])
app.include_router(precheck.router, prefix="/v1", tags=["Pre-Check"])
app.include_router(audit.router, prefix="/v1", tags=["Audit"])
app.include_router(events.router, prefix="/v1", tags=["Audit Events"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "regwatch-api"}
