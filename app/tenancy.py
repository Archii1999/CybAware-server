from __future__ import annotations
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Organization

def _extract_subdomain(host: str, base_domeain: str) -> Optional[str]:
    host = (host or "").split(":")[0].lower().strip()
    base_domeain = base_domeain.lower().strip()
    if not host.endswith(base_domeain):
        return None
    
    left = host[: -len(base_domeain)].rstrip(".")
    if not left:
        return None
    
    return left.split(".")[-1] if left else None

class TenantMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app: ASGIApp, base_domain: str):
                 super().__init__(app)
                 self.base_domain = base_domain

    async def dispatch(self, request: Request, call_next):
          host = request.headers.get("X-forwarded-host") or request.headers.get("host") or ""
          sub = _extract_subdomain(host, self.base_domain)

          org_id: Optional[int] = None
          db: Session | None = None

          try:
                if sub:
                      db = SessionLocal()
                      org = db.query(Organization).filter(Organization.slug == sub).first()
                      if org:
                            org_id = org.id
                
                if org_id is None:
                      x_org = request.headers.get("x-org-id")
                      if x_org and x_org.isdigit():
                            org_id = int(x_org)
                
                request.state.org_id = org_id
                response = await call_next(request)
                return response
          finally:
                if db:
                      db.close()

    
