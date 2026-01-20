from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import datetime
from .. import models, schemas
from ..dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/tds",
    tags=["TDS Reports"]
)

@router.get("/summary", response_model=schemas.APIResponse)
async def tds_summary(
    month: int = Query(datetime.now().month),
    year: int = Query(datetime.now().year),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # TDS Deducted on Purchases
    tds_data = db.query(
        models.Billing.vendor_id,
        func.sum(models.Billing.tds_amount).label('total_tds'),
        func.sum(models.Billing.base_amount).label('total_base')
    ).filter(
        extract('month', models.Billing.bill_date) == month,
        extract('year', models.Billing.bill_date) == year,
        models.Billing.tds_applicable == True
    ).group_by(models.Billing.vendor_id).all()
    
    # Resolve vendor names
    result = []
    total_liability = 0.0
    
    for row in tds_data:
        vendor = db.query(models.Company).filter(models.Company.id == row.vendor_id).first()
        result.append({
            "vendor_name": vendor.name if vendor else "Unknown",
            "pan": vendor.pan_number if vendor else None,
            "base_amount": row.total_base,
            "tds_deducted": row.total_tds
        })
        total_liability += row.total_tds
        
    return {
        "success": True,
        "data": {
            "liability": total_liability,
            "details": result
        },
        "message": "TDS Summary"
    }
