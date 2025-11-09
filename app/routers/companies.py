from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.deps import get_db, get_current_user, require_role   # let op: uit deps importeren
from app import models
from app.schemas.companies import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(
    prefix="/organizations/{slug}/companies",
    tags=["companies"],
    # MANAGER of hoger mag company-endpoints gebruiken
    dependencies=[Depends(require_role("MANAGER"))],  # eenvoud: strings; kan ook met Enum als je deps dat ondersteunt
)

def _get_org_or_404(db: Session, slug: str) -> models.Organization:
    org = db.query(models.Organization).filter(models.Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisatie niet gevonden")
    return org

def _get_company_in_org_or_404(db: Session, org_id: int, company_id: int) -> models.Company:
    comp = db.query(models.Company).filter(
        models.Company.id == company_id,
        models.Company.org_id == org_id
    ).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Company niet gevonden binnen deze organisatie")
    return comp

# CREATE
@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    slug: str,
    payload: CompanyCreate,
    db: Session = Depends(get_db),
):
    org = _get_org_or_404(db, slug)

    # unieke naam per org
    exists = db.query(models.Company).filter(
        models.Company.org_id == org.id,
        models.Company.name == payload.name
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Bedrijfsnaam bestaat al binnen deze organisatie.")

    company = models.Company(org_id=org.id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

# LIST (zoek/paginatie/sort), gescope’d op org
@router.get("/", response_model=List[CompanyOut])
def list_companies(
    slug: str,
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Zoek in name/sector/domain"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", description="name|sector|created_at|updated_at"),
    order: str = Query("desc", description="asc|desc"),
):
    org = _get_org_or_404(db, slug)
    query = db.query(models.Company).filter(models.Company.org_id == org.id)

    if q:
        like = f"%{q}%"
        # ILIKE wordt geëmuleerd waar nodig; bij MySQL is de collation vaak al case-insensitive
        query = query.filter(
            (models.Company.name.ilike(like)) |
            (models.Company.sector.ilike(like)) |
            (models.Company.email_domain.ilike(like))
        )

    sort_map = {
        "name": models.Company.name,
        "sector": models.Company.sector,
        "created_at": models.Company.created_at,
        "updated_at": models.Company.updated_at,
    }
    sort_col = sort_map.get(sort, models.Company.created_at)
    query = query.order_by(asc(sort_col) if order.lower() == "asc" else desc(sort_col))

    return query.offset(skip).limit(limit).all()

# READ (detail)
@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    slug: str,
    company_id: int,
    db: Session = Depends(get_db)
):
    org = _get_org_or_404(db, slug)
    return _get_company_in_org_or_404(db, org.id, company_id)

# UPDATE
@router.put("/{company_id}", response_model=CompanyOut)
def update_company(
    slug: str,
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
):
    org = _get_org_or_404(db, slug)
    company = _get_company_in_org_or_404(db, org.id, company_id)

    # naam-wijziging: check uniek binnen org
    data = payload.model_dump(exclude_unset=True)
    new_name = data.get("name")
    if new_name and new_name != company.name:
        clash = db.query(models.Company).filter(
            models.Company.org_id == org.id,
            models.Company.name == new_name,
            models.Company.id != company.id
        ).first()
        if clash:
            raise HTTPException(status_code=400, detail="Bedrijfsnaam bestaat al binnen deze organisatie.")

    for k, v in data.items():
        setattr(company, k, v)

    db.add(company)
    db.commit()
    db.refresh(company)
    return company

# DELETE (alleen ADMIN of hoger? → optioneel extra check)
@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    slug: str,
    company_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    org = _get_org_or_404(db, slug)
    company = _get_company_in_org_or_404(db, org.id, company_id)

    # Optioneel: strengere rol voor delete
    # if not user_is_admin_in_org(db, current.id, org.id):
    #     raise HTTPException(status_code=403, detail="Alleen ADMIN mag verwijderen")

    db.delete(company)
    db.commit()
    return None