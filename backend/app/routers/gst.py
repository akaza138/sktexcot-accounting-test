from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import datetime
from .. import models, schemas
from ..dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/gst",
    tags=["GST Reports"]
)

@router.get("/summary", response_model=schemas.APIResponse)
async def gst_summary(
    month: int = Query(datetime.now().month),
    year: int = Query(datetime.now().year),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Output GST components
    sales_gst = db.query(
        func.sum(models.Sales.cgst_amount).label('cgst'),
        func.sum(models.Sales.sgst_amount).label('sgst'),
        func.sum(models.Sales.igst_amount).label('igst')
    ).filter(
        extract('month', models.Sales.invoice_date) == month,
        extract('year', models.Sales.invoice_date) == year
    ).first()

    # Input GST components (Billing table stores total gst_amount, if split needed we need type)
    # Billing model has gst_type and gst_amount. We can derive split.
    # Logic:
    # If gst_type == INTRA_STATE: cgst = gst/2, sgst = gst/2
    # If gst_type == INTER_STATE: igst = gst
    
    input_intra = db.query(func.sum(models.Billing.gst_amount)).filter(
        extract('month', models.Billing.bill_date) == month,
        extract('year', models.Billing.bill_date) == year,
        models.Billing.gst_type == models.GSTType.INTRA_STATE
    ).scalar() or 0.0
    
    input_inter = db.query(func.sum(models.Billing.gst_amount)).filter(
        extract('month', models.Billing.bill_date) == month,
        extract('year', models.Billing.bill_date) == year,
        models.Billing.gst_type == models.GSTType.INTER_STATE
    ).scalar() or 0.0
    
    output_data = {
        "cgst": sales_gst.cgst or 0.0,
        "sgst": sales_gst.sgst or 0.0,
        "igst": sales_gst.igst or 0.0,
        "total": (sales_gst.cgst or 0.0) + (sales_gst.sgst or 0.0) + (sales_gst.igst or 0.0)
    }
    
    input_data = {
        "cgst": input_intra / 2,
        "sgst": input_intra / 2,
        "igst": input_inter,
        "total": input_intra + input_inter
    }
    
    return {
        "success": True,
        "data": {
            "output_gst": output_data,
            "input_gst": input_data,
            "net_payable": output_data["total"] - input_data["total"]
        },
        "message": "GST Summary"
    }
