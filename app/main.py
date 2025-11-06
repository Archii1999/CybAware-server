from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

import os

from app.database import Base, engine
from app import models
from app.tenancy import TenantMiddleware
from app.db import engine

app=FastAPI(title="CybAware API", version="0.1.0")

Base.metadata.create_all(bind=engine)
app.include_router(users_router)
app.include_router(auth_router)

class HealthOut(BaseModel):
    ok: bool
    env: str

#basis staat
@app.get("/health", response_model=HealthOut, tags=["meta"])
def healthcheck() -> HealthOut:
    env = os.getenv("ENV", "development")
    return HealthOut(ok=True, env=env)

#leeft die nog?!
@app.get("/live", tags=["meta"])
def liveness():
    return {"status": "alive"}

@app.get("/ready", tags=["meta"])
def readiness():
    if os.getenv("READY", "true").lower() != "true":
        raise HTTPException(status_code=503, detail="Not ready")
    return ("status:", "ready")

def create_app() -> FastAPI:
    app = FastAPI(title="CybAware API")
    Base.metadata.create_all(bind=engine)

    app.add_middleware(TenantMiddleware, base_domain="cybaware.nl")

    from app.routers import auth, users
    app.include_router(auth_router)
    app.include_router(users_router)
    return app

app = create_app()
