from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, audit
from ..dependencies import get_db, get_current_user, get_current_active_user, RoleChecker
from ..models import UserRole

router = APIRouter(
    prefix="/company",
    tags=["Company Master"]
)

# Permissions
allow_create_edit = RoleChecker([UserRole.OWNER, UserRole.ACCOUNTANT])
allow_delete = RoleChecker([UserRole.OWNER])

@router.post("/", response_model=schemas.CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    company: schemas.CompanyCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_create_edit)
):
    # Normalize empty strings to None for unique fields
    if company.gst_number == "": company.gst_number = None
    if company.pan_number == "": company.pan_number = None

    # Check duplicate
    if db.query(models.Company).filter(models.Company.name == company.name).first():
        raise HTTPException(status_code=400, detail="Company with this name already exists")
    
    # Check GST duplicate only if it has a value
    if company.gst_number and db.query(models.Company).filter(models.Company.gst_number == company.gst_number).first():
         raise HTTPException(status_code=400, detail="Company with this GST already exists")
    
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    audit.log_action(db, current_user.id, "create", "companies", db_company.id, None, company.dict())
    
    return db_company

@router.get("/", response_model=schemas.APIResponse)
async def read_companies(
    skip: int = 0, 
    limit: int = 100, 
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.Company).filter(models.Company.is_active == True)
    
    if q:
        search = f"%{q}%"
        query = query.filter(
            (models.Company.name.ilike(search)) | 
            (models.Company.gst_number.ilike(search)) |
            (models.Company.phone.ilike(search))
        )
    
    # Order by ID descending (newest first) to ensure stable order
    query = query.order_by(models.Company.id.desc())
    
    total = query.count()
    companies = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [schemas.CompanyOut.from_orm(c) for c in companies],
        "message": "Companies retrieved successfully",
        # "pagination": {"skip": skip, "limit": limit, "total": total} # Can add this to response schema
    }

@router.get("/{company_id}", response_model=schemas.APIResponse)
async def read_company(
    company_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return {
        "success": True,
        "data": schemas.CompanyOut.from_orm(company),
        "message": "Company retrieved successfully"
    }

@router.put("/{company_id}", response_model=schemas.CompanyOut)
async def update_company(
    company_id: int, 
    company_update: schemas.CompanyUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_create_edit)
):
    db_company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    
    old_data = schemas.CompanyOut.from_orm(db_company).dict()
    update_data = company_update.dict(exclude_unset=True)
    
    # Normalize empty strings to None for unique fields
    if "gst_number" in update_data and update_data["gst_number"] == "":
        update_data["gst_number"] = None
    if "pan_number" in update_data and update_data["pan_number"] == "":
        update_data["pan_number"] = None
    
    # Check duplicates if name or gst changed
    if "name" in update_data:
        existing = db.query(models.Company).filter(models.Company.name == update_data["name"]).first()
        if existing and existing.id != company_id:
            raise HTTPException(status_code=400, detail="Company name already exists")
    
    if "gst_number" in update_data and update_data["gst_number"] is not None:
        existing = db.query(models.Company).filter(models.Company.gst_number == update_data["gst_number"]).first()
        if existing and existing.id != company_id:
            raise HTTPException(status_code=400, detail="Company with this GST already exists")
            
    for key, value in update_data.items():
        setattr(db_company, key, value)
    
    db.commit()
    db.refresh(db_company)
    
    audit.log_action(db, current_user.id, "update", "companies", company_id, old_data, update_data)
    
    return db_company

@router.delete("/{company_id}")
async def delete_company(
    company_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_delete)
):
    db_company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if db_company is None:
         raise HTTPException(status_code=404, detail="Company not found")
    
    # Soft delete
    db_company.is_active = False
    db.commit()
    
    audit.log_action(db, current_user.id, "delete", "companies", company_id)
    
    return {"message": "Company deleted successfully (soft delete)"}
