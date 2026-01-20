from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from .. import models, schemas, audit
from ..dependencies import get_db, get_current_active_user, RoleChecker
from ..models import UserRole, GSTType, TransactionType

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)

allow_write = RoleChecker([UserRole.OWNER, UserRole.ACCOUNTANT, UserRole.MERCHANDISER])
allow_delete = RoleChecker([UserRole.OWNER, UserRole.ACCOUNTANT])

def generate_invoice_number(db: Session, date_obj):
    year = date_obj.year
    # Find last invoice for this year
    # Pattern SK/YYYY/XXXX
    prefix = f"SK/{year}/"
    last_sale = db.query(models.Sales).filter(models.Sales.invoice_number.like(f"{prefix}%")).order_by(models.Sales.id.desc()).first()
    
    if last_sale:
        try:
            last_seq = int(last_sale.invoice_number.split("/")[-1])
            new_seq = last_seq + 1
        except:
            new_seq = 1
    else:
        new_seq = 1
        
    return f"{prefix}{new_seq:04d}"

@router.post("/", response_model=schemas.SalesOut, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: schemas.SalesCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_write)
):
    # validate company
    company = db.query(models.Company).filter(models.Company.id == sale.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Calculate amounts
    base_amount = sale.quantity * sale.rate
    gst_amount = base_amount * (sale.gst_rate / 100)
    
    sale_data = sale.dict()
    sale_data["base_amount"] = base_amount
    
    if sale.gst_type == GSTType.INTRA_STATE:
        sale_data["cgst_amount"] = gst_amount / 2
        sale_data["sgst_amount"] = gst_amount / 2
        sale_data["igst_amount"] = 0.0
    else:
        sale_data["cgst_amount"] = 0.0
        sale_data["sgst_amount"] = 0.0
        sale_data["igst_amount"] = gst_amount
        
    total_amount = base_amount + gst_amount + sale.tcs_amount
    sale_data["total_amount"] = total_amount
    sale_data["amount_due"] = total_amount - sale.amount_paid
    
    # Generate Invoice Number
    sale_data["invoice_number"] = generate_invoice_number(db, sale.invoice_date)
    sale_data["created_by"] = current_user.id
    
    db_sale = models.Sales(**sale_data)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    # Ledger Entry (Debit Customer)
    ledger_entry = models.Ledger(
        company_id=sale.company_id,
        transaction_date=sale.invoice_date,
        transaction_type=TransactionType.SALE,
        reference_id=db_sale.id,
        reference_model="Sales",
        debit_amount=total_amount,
        credit_amount=0.0,
        narration=f"invoice #{db_sale.invoice_number} - {sale.item_description or ''}"
    )
    db.add(ledger_entry)

    # If amount paid > 0, we should record a receipt in ledger too?
    # For simplicity, if they enter amount paid here, we treat it as a receipt
    if sale.amount_paid > 0:
        # Create Payment record (auto)
        payment = models.Payment(
            payment_date=sale.payment_date or sale.invoice_date,
            payment_type=TransactionType.RECEIPT,
            company_id=sale.company_id,
            sales_id=db_sale.id,
            amount=sale.amount_paid,
            payment_mode=sale.payment_mode,
            notes="Auto-created from Sales entry",
            created_by=current_user.id
        )
        db.add(payment)
        
        # Ledger Entry (Credit Customer)
        ledger_payment = models.Ledger(
            company_id=sale.company_id,
            transaction_date=sale.payment_date or sale.invoice_date,
            transaction_type=TransactionType.RECEIPT,
            reference_id=db_sale.id, # Using Sale ID as reference or new Payment ID? ideally payment id, but we don't have it yet.
            # We can commit payment first.
            reference_model="Payment", # Will update ref id after commit if needed, or just link to sales
            debit_amount=0.0,
            credit_amount=sale.amount_paid,
            narration=f"Payment for Invoice #{db_sale.invoice_number}"
        )
        # We need payment ID.
        db.commit()
        db.refresh(payment)
        ledger_payment.reference_id = payment.id
        db.add(ledger_payment)
    
    db.commit()
    
    # Update company opening balance? No, opening balance is static.
    # Current balance is calculated from ledger.
    
    audit.log_action(db, current_user.id, "create", "sales", db_sale.id, None, sale_data)
    
    return db_sale

@router.get("/", response_model=schemas.APIResponse)
async def read_sales(
    skip: int = 0, 
    limit: int = 20, 
    company_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.Sales)
    
    if company_id:
        query = query.filter(models.Sales.company_id == company_id)
    if start_date:
        query = query.filter(models.Sales.invoice_date >= start_date)
    if end_date:
        query = query.filter(models.Sales.invoice_date <= end_date)
        
    query = query.order_by(models.Sales.invoice_date.desc())
        
    total = query.count()
    sales = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [schemas.SalesOut.from_orm(s) for s in sales],
        "message": "Sales retrieved successfully"
    }

@router.get("/{sales_id}", response_model=schemas.APIResponse)
async def read_sale(
    sales_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    sale = db.query(models.Sales).filter(models.Sales.id == sales_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "success": True,
        "data": schemas.SalesOut.from_orm(sale),
        "message": "Sale retrieved successfully"
    }

@router.put("/{sales_id}", response_model=schemas.SalesOut)
async def update_sale(
    sales_id: int, 
    sale_update: schemas.SalesUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_write)
):
    db_sale = db.query(models.Sales).filter(models.Sales.id == sales_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    old_data = schemas.SalesOut.from_orm(db_sale).dict()
    update_data = sale_update.dict(exclude_unset=True)
    
    # Update fields
    for key, value in update_data.items():
        setattr(db_sale, key, value)
        
    # Recalculate totals if financial fields changed
    recalc_fields = ["quantity", "rate", "gst_rate", "gst_type", "tcs_amount", "amount_paid"]
    if any(field in update_data for field in recalc_fields):
        base_amount = db_sale.quantity * db_sale.rate
        gst_amount = base_amount * (db_sale.gst_rate / 100)
        
        db_sale.base_amount = base_amount
        
        if db_sale.gst_type == GSTType.INTRA_STATE:
            db_sale.cgst_amount = gst_amount / 2
            db_sale.sgst_amount = gst_amount / 2
            db_sale.igst_amount = 0.0
        else:
            db_sale.cgst_amount = 0.0
            db_sale.sgst_amount = 0.0
            db_sale.igst_amount = gst_amount
            
        total_amount = base_amount + gst_amount + (db_sale.tcs_amount or 0)
        db_sale.total_amount = total_amount
        db_sale.amount_due = total_amount - (db_sale.amount_paid or 0)
        
        # Update Ledger for Sale
        ledger_entry = db.query(models.Ledger).filter(
            models.Ledger.reference_id == sales_id,
            models.Ledger.reference_model == "Sales",
            models.Ledger.transaction_type == TransactionType.SALE
        ).first()
        
        if ledger_entry:
            ledger_entry.debit_amount = total_amount
            ledger_entry.transaction_date = db_sale.invoice_date
            ledger_entry.narration = f"Invoice #{db_sale.invoice_number} (Updated) - {db_sale.item_description or ''}"
            
        # Update Payment & Payment Ledger if amount_paid changed
        if "amount_paid" in update_data:
            payment = db.query(models.Payment).filter(models.Payment.sales_id == sales_id).first()
            
            if payment:
                if (db_sale.amount_paid or 0) > 0:
                    payment.amount = db_sale.amount_paid
                    payment.payment_mode = db_sale.payment_mode
                    payment.payment_date = db_sale.payment_date or db_sale.invoice_date
                    
                    ledger_pay = db.query(models.Ledger).filter(
                        models.Ledger.reference_id == payment.id,
                        models.Ledger.reference_model == "Payment"
                    ).first()
                    if ledger_pay:
                        ledger_pay.credit_amount = db_sale.amount_paid
                        ledger_pay.transaction_date = payment.payment_date
                else:
                    # Set to 0 if removed
                    payment.amount = 0
                    ledger_pay = db.query(models.Ledger).filter(
                        models.Ledger.reference_id == payment.id,
                        models.Ledger.reference_model == "Payment"
                    ).first()
                    if ledger_pay:
                        ledger_pay.credit_amount = 0

            elif (db_sale.amount_paid or 0) > 0:
                # Create new payment if didn't exist
                payment = models.Payment(
                    payment_date=db_sale.payment_date or db_sale.invoice_date,
                    payment_type=TransactionType.RECEIPT,
                    company_id=db_sale.company_id,
                    sales_id=db_sale.id,
                    amount=db_sale.amount_paid,
                    payment_mode=db_sale.payment_mode,
                    notes="Auto-created from Sales update",
                    created_by=current_user.id
                )
                db.add(payment)
                db.commit()
                db.refresh(payment)
                
                ledger_payment = models.Ledger(
                    company_id=db_sale.company_id,
                    transaction_date=payment.payment_date,
                    transaction_type=TransactionType.RECEIPT,
                    reference_id=payment.id,
                    reference_model="Payment",
                    debit_amount=0.0,
                    credit_amount=db_sale.amount_paid,
                    narration=f"Payment for Invoice #{db_sale.invoice_number}"
                )
                db.add(ledger_payment)

    db.commit()
    db.refresh(db_sale)
    audit.log_action(db, current_user.id, "update", "sales", sales_id, old_data, update_data)
    
    return db_sale

@router.delete("/{sales_id}")
async def delete_sale(
    sales_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_delete)
):
    sale = db.query(models.Sales).filter(models.Sales.id == sales_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # 1. Delete all payments linked to this sale
    payments = db.query(models.Payment).filter(models.Payment.sales_id == sales_id).all()
    for payment in payments:
        # 1.1 Delete ledger entries for each payment
        db.query(models.Ledger).filter(
            models.Ledger.reference_id == payment.id,
            models.Ledger.reference_model == "Payment"
        ).delete()
        # 1.2 Delete the payment itself
        db.delete(payment)
        
    # 2. Delete main ledger entries for the sale
    db.query(models.Ledger).filter(
        models.Ledger.reference_id == sales_id, 
        models.Ledger.reference_model == "Sales"
    ).delete()
    
    # 3. Delete the sale
    db.delete(sale)
    db.commit()
    
    audit.log_action(db, current_user.id, "delete", "sales", sales_id)
    
    return {"message": "Invoice deleted successfully"}
