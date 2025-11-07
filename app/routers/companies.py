from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.database import get_db
from app.models import Company, Role           # ✅ importeer Role Enum
from app.schemas.companies import CompanyCreate, CompanyOut, CompanyUpdate
from app.deps import require_role

# ✅ Zet ADMIN-dependency op router-niveau voor alle endpoints
router = APIRouter(
    prefix="/companies",
    tags=["companies"],
    dependencies=[Depends(require_role(Role.ADMIN))],  # ⬅️ Enum, geen string
)

# CREATE
@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bedrijfsnaam bestaat al.")
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

# LIST (met zoek/paginatie/sort)
@router.get("/", response_model=List[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Zoek in name/sector/domain"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", description="name|sector|created_at|updated_at"),
    order: str = Query("desc", description="asc|desc"),
):
    query = db.query(Company)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Company.name.ilike(like)) |
            (Company.sector.ilike(like)) |
            (Company.email_domain.ilike(like))
        )

    sort_map = {
        "name": Company.name,
        "sector": Company.sector,
        "created_at": Company.created_at,
        "updated_at": Company.updated_at,
    }
    sort_col = sort_map.get(sort, Company.created_at)
    query = query.order_by(asc(sort_col) if order == "asc" else desc(sort_col))

    return query.offset(skip).limit(limit).all()

# READ (detail)
@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company niet gevonden.")
    return company

# UPDATE
@router.put("/{company_id}", response_model=CompanyOut)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(Company).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company niet gevonden.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

# DELETE
@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company niet gevonden.")
    db.delete(company)
    db.commit()
    return None
