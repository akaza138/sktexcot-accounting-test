from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .. import models, schemas, audit
from ..dependencies import get_db, get_current_active_user, RoleChecker
from ..models import UserRole, TransactionType, PaymentStatus

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

allow_write = RoleChecker([UserRole.OWNER, UserRole.ACCOUNTANT])
allow_delete = RoleChecker([UserRole.OWNER])

@router.post("/", response_model=schemas.PaymentOut, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: schemas.PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_write)
):
    # Validate company
    company = db.query(models.Company).filter(models.Company.id == payment.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Save payment record
    payment_data = payment.dict()
    payment_data["created_by"] = current_user.id
    
    db_payment = models.Payment(**payment_data)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Update Ledger
    ledger_debit = 0.0
    ledger_credit = 0.0
    
    if payment.payment_type == TransactionType.RECEIPT:
        # We received money -> Credit Company (reduce receivable)
        ledger_credit = payment.amount
        narration = f"Receipt #{db_payment.id}"
    else:
        # We paid money -> Debit Company (reduce payable)
        ledger_debit = payment.amount
        narration = f"Payment #{db_payment.id}"
        
    if payment.notes:
        narration += f" - {payment.notes}"
        
    ledger_entry = models.Ledger(
        company_id=payment.company_id,
        transaction_date=payment.payment_date,
        transaction_type=payment.payment_type,
        reference_id=db_payment.id,
        reference_model="Payment",
        debit_amount=ledger_debit,
        credit_amount=ledger_credit,
        narration=narration
    )
    db.add(ledger_entry)
    
    # Handle Invoice Linking (Sales)
    if payment.sales_id:
        sale = db.query(models.Sales).filter(models.Sales.id == payment.sales_id).first()
        if sale:
            sale.amount_paid += payment.amount
            sale.amount_due = sale.total_amount - sale.amount_paid
            if sale.amount_due <= 0:
                sale.payment_status = PaymentStatus.PAID
                sale.amount_due = 0 # Prevent negative
            elif sale.amount_paid > 0:
                sale.payment_status = PaymentStatus.PARTIAL
            else:
                sale.payment_status = PaymentStatus.UNPAID
            
            # If payment date is later than current sale payment date, update it? 
            # Or keep last payment date.
            sale.payment_date = payment.payment_date
            sale.payment_mode = payment.payment_mode
            
            db.add(sale)
            
    # Handle Bill Linking (Billing)
    if payment.billing_id:
        bill = db.query(models.Billing).filter(models.Billing.id == payment.billing_id).first()
        if bill:
            bill.amount_paid += payment.amount
            bill.amount_due = bill.total_amount - bill.amount_paid
            if bill.amount_due <= 0:
                bill.payment_status = PaymentStatus.PAID
                bill.amount_due = 0
            elif bill.amount_paid > 0:
                bill.payment_status = PaymentStatus.PARTIAL
            else:
                bill.payment_status = PaymentStatus.UNPAID
            
            bill.payment_date = payment.payment_date
            bill.payment_mode = payment.payment_mode
            db.add(bill)
            
    db.commit()
    
    audit.log_action(db, current_user.id, "create", "payments", db_payment.id, None, payment_data)
    
    return db_payment

@router.get("/", response_model=schemas.APIResponse)
async def read_payments(
    skip: int = 0, 
    limit: int = 20, 
    company_id: Optional[int] = None,
    payment_type: Optional[TransactionType] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.Payment)
    if company_id:
        query = query.filter(models.Payment.company_id == company_id)
    if payment_type:
        query = query.filter(models.Payment.payment_type == payment_type)
        
    query = query.order_by(models.Payment.payment_date.desc())
    payments = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [schemas.PaymentOut.from_orm(p) for p in payments],
        "message": "Payments retrieved successfully"
    }

@router.put("/{payment_id}", response_model=schemas.PaymentOut)
async def update_payment(
    payment_id: int,
    payment_update: schemas.PaymentCreate, # reusing create schema for simplicity
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_write)
):
    # Updating payment is complex because we need to revert previous ledger/sales effects.
    # For MVP/Task, we'll allow updating basic fields (Amount requires complex reversion logic).
    # If amount changes, we block it for now or assume user knows to fixing it.
    # Let's focus on non-amount fields first or full logic.
    # Full logic:
    # 1. Revert old amount from Sales/Billing.
    # 2. Revert old Ledger.
    # 3. Apply new amount.
    
    db_payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    old_amount = db_payment.amount
    new_amount = payment_update.amount
    
    diff = new_amount - old_amount
    
    if diff != 0:
        # Update Sales if linked
        if db_payment.sales_id:
            sale = db.query(models.Sales).filter(models.Sales.id == db_payment.sales_id).first()
            if sale:
                sale.amount_paid += diff
                sale.amount_due = sale.total_amount - sale.amount_paid
                # recalculate status
                if sale.amount_due <= 0:
                    sale.payment_status = PaymentStatus.PAID
                    sale.amount_due = 0
                elif sale.amount_paid > 0:
                    sale.payment_status = PaymentStatus.PARTIAL
                else:
                    sale.payment_status = PaymentStatus.UNPAID
        
        # Update Billing if linked
        if db_payment.billing_id:
             bill = db.query(models.Billing).filter(models.Billing.id == db_payment.billing_id).first()
             if bill:
                bill.amount_paid += diff
                bill.amount_due = bill.total_amount - bill.amount_paid
                if bill.amount_due <= 0:
                    bill.payment_status = PaymentStatus.PAID
                    bill.amount_due = 0
                elif bill.amount_paid > 0:
                    bill.payment_status = PaymentStatus.PARTIAL
                else:
                    bill.payment_status = PaymentStatus.UNPAID
                    
        # Update Ledger
        ledger = db.query(models.Ledger).filter(
            models.Ledger.reference_id == payment_id,
            models.Ledger.reference_model == "Payment"
        ).first()
        
        if ledger:
            if db_payment.payment_type == TransactionType.RECEIPT:
                ledger.credit_amount = new_amount
            else:
                ledger.debit_amount = new_amount
            
            ledger.transaction_date = payment_update.payment_date
            # update narration if needed for date/mode
            
    # Update payment record
    for key, value in payment_update.dict().items():
        setattr(db_payment, key, value)
        
    db.commit()
    db.refresh(db_payment)
    
    audit.log_action(db, current_user.id, "update", "payments", payment_id, {"amount": old_amount}, payment_update.dict())
    
    return db_payment
