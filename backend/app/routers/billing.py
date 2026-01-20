from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .. import models, schemas, audit
from ..dependencies import get_db, get_current_active_user, RoleChecker
from ..models import UserRole, GSTType, TransactionType

router = APIRouter(
    prefix="/billing",
    tags=["Billing/Purchase"]
)

allow_write = RoleChecker([UserRole.OWNER, UserRole.ACCOUNTANT])
allow_delete = RoleChecker([UserRole.OWNER, UserRole.ACCOUNTANT])

@router.post("/", response_model=schemas.BillingOut, status_code=status.HTTP_201_CREATED)
async def create_bill(
    bill: schemas.BillingCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_write)
):
    vendor = db.query(models.Company).filter(models.Company.id == bill.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Calculate amounts
    base_amount = bill.quantity * bill.rate
    gst_amount = base_amount * (bill.gst_rate / 100)
    
    tds_amount = 0.0
    if bill.tds_applicable:
        tds_amount = base_amount * (bill.tds_rate / 100)
        
    total_amount = base_amount + gst_amount - tds_amount
    
    bill_data = bill.dict()
    bill_data["base_amount"] = base_amount
    bill_data["gst_amount"] = gst_amount
    bill_data["tds_amount"] = tds_amount
    bill_data["total_amount"] = total_amount
    bill_data["amount_due"] = total_amount - bill.amount_paid
    bill_data["created_by"] = current_user.id
    
    db_bill = models.Billing(**bill_data)
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    
    # Ledger Entry (Credit Vendor - Payable)
    # When we license a bill, we OWE money. So Credit the Vendor.
    ledger_entry = models.Ledger(
        company_id=bill.vendor_id,
        transaction_date=bill.bill_date,
        transaction_type=TransactionType.PURCHASE,
        reference_id=db_bill.id,
        reference_model="Billing",
        debit_amount=0.0,
        credit_amount=total_amount,
        narration=f"Bill #{db_bill.bill_number} - {bill.item_description or ''}"
    )
    db.add(ledger_entry)
    
    # If amount paid > 0, record Payment (Debit Vendor)
    if bill.amount_paid > 0:
        payment = models.Payment(
            payment_date=bill.payment_date or bill.bill_date,
            payment_type=TransactionType.PAYMENT, # We are Paying
            company_id=bill.vendor_id,
            billing_id=db_bill.id,
            amount=bill.amount_paid,
            payment_mode=bill.payment_mode,
            notes="Auto-created from Billing entry",
            created_by=current_user.id
        )
        db.add(payment)
        
        db.commit()
        db.refresh(payment)
        
        ledger_payment = models.Ledger(
            company_id=bill.vendor_id,
            transaction_date=bill.payment_date or bill.bill_date,
            transaction_type=TransactionType.PAYMENT,
            reference_id=payment.id,
            reference_model="Payment",
            debit_amount=bill.amount_paid,
            credit_amount=0.0,
            narration=f"Payment for Bill #{db_bill.bill_number}"
        )
        db.add(ledger_payment)
        
    db.commit()
    
    audit.log_action(db, current_user.id, "create", "billing", db_bill.id, None, bill_data)
    
    return db_bill

@router.get("/", response_model=schemas.APIResponse)
async def read_bills(
    skip: int = 0, 
    limit: int = 20, 
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.Billing)
    if vendor_id:
        query = query.filter(models.Billing.vendor_id == vendor_id)
        
    query = query.order_by(models.Billing.bill_date.desc())
    bills = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [schemas.BillingOut.from_orm(b) for b in bills],
        "message": "Bills retrieved successfully"
    }

@router.get("/{bill_id}", response_model=schemas.APIResponse)
async def read_bill(
    bill_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    bill = db.query(models.Billing).filter(models.Billing.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {
        "success": True,
        "data": schemas.BillingOut.from_orm(bill),
        "message": "Bill retrieved successfully"
    }

@router.delete("/{bill_id}")
async def delete_bill(
    bill_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_delete)
):
    bill = db.query(models.Billing).filter(models.Billing.id == bill_id).first()
    if not bill:
         raise HTTPException(status_code=404, detail="Bill not found")
    
    # 1. Delete all payments linked to this bill
    payments = db.query(models.Payment).filter(models.Payment.billing_id == bill_id).all()
    for payment in payments:
        # 1.1 Delete ledger entries for each payment
        db.query(models.Ledger).filter(
            models.Ledger.reference_id == payment.id,
            models.Ledger.reference_model == "Payment"
        ).delete()
        # 1.2 Delete the payment itself
        db.delete(payment)
         
    # 2. Delete main ledger entry for the bill
    db.query(models.Ledger).filter(
        models.Ledger.reference_id == bill_id,
        models.Ledger.reference_model == "Billing"
    ).delete()
    
    # 3. Delete the bill
    db.delete(bill)
    db.commit()
    
    audit.log_action(db, current_user.id, "delete", "billing", bill_id)
    
    return {"message": "Bill deleted successfully"}

@router.put("/{bill_id}", response_model=schemas.BillingOut)
async def update_bill(
    bill_id: int, 
    bill_update: schemas.BillingUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_write)
):
    db_bill = db.query(models.Billing).filter(models.Billing.id == bill_id).first()
    if not db_bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    old_data = schemas.BillingOut.from_orm(db_bill).dict()
    update_data = bill_update.dict(exclude_unset=True)
    
    # Update fields
    for key, value in update_data.items():
        setattr(db_bill, key, value)
        
    # Recalculate totals if any financial field changed
    recalc_fields = ["quantity", "rate", "gst_rate", "tds_applicable", "tds_rate", "amount_paid"]
    if any(field in update_data for field in recalc_fields):
        base_amount = db_bill.quantity * db_bill.rate
        gst_amount = base_amount * (db_bill.gst_rate / 100)
        tds_amount = 0.0
        if db_bill.tds_applicable:
            tds_amount = base_amount * (db_bill.tds_rate / 100)
            
        total_amount = base_amount + gst_amount - tds_amount
        
        db_bill.base_amount = base_amount
        db_bill.gst_amount = gst_amount
        db_bill.tds_amount = tds_amount
        db_bill.total_amount = total_amount
        db_bill.amount_due = total_amount - db_bill.amount_paid
        
        # Update Ledger for Bill (Purchase)
        ledger_entry = db.query(models.Ledger).filter(
            models.Ledger.reference_id == bill_id,
            models.Ledger.reference_model == "Billing",
            models.Ledger.transaction_type == TransactionType.PURCHASE
        ).first()
        
        if ledger_entry:
            ledger_entry.credit_amount = total_amount
            ledger_entry.transaction_date = db_bill.bill_date
            ledger_entry.narration = f"Bill #{db_bill.bill_number} (Updated) - {db_bill.item_description or ''}"

        # Update Payment Ledger if amount_paid changed
        # Note: If there are multiple separate payments, this single 'amount_paid' field model is limiting.
        # But assuming 1-to-1 for now as per current create logic.
        if "amount_paid" in update_data:
            # Find associated initial payment
            payment = db.query(models.Payment).filter(models.Payment.billing_id == bill_id).first()
            if payment:
                if db_bill.amount_paid > 0:
                    payment.amount = db_bill.amount_paid
                    payment.payment_mode = db_bill.payment_mode
                    payment.payment_date = db_bill.payment_date or db_bill.bill_date
                    
                    # Update its ledger
                    ledger_pay = db.query(models.Ledger).filter(
                        models.Ledger.reference_id == payment.id,
                        models.Ledger.reference_model == "Payment"
                    ).first()
                    if ledger_pay:
                        ledger_pay.debit_amount = db_bill.amount_paid
                        ledger_pay.transaction_date = payment.payment_date
                else:
                    # If changed to 0, maybe delete payment? Or keep as 0? 
                    # Simpler to set to 0.
                    payment.amount = 0
                    ledger_pay = db.query(models.Ledger).filter(
                        models.Ledger.reference_id == payment.id,
                        models.Ledger.reference_model == "Payment"
                    ).first()
                    if ledger_pay:
                        ledger_pay.debit_amount = 0
            
            # If no existing payment but now paid > 0, create it (complexity: duplicate payments? handling simplistically)
            elif db_bill.amount_paid > 0:
                payment = models.Payment(
                    payment_date=db_bill.payment_date or db_bill.bill_date,
                    payment_type=TransactionType.PAYMENT,
                    company_id=db_bill.vendor_id,
                    billing_id=db_bill.id,
                    amount=db_bill.amount_paid,
                    payment_mode=db_bill.payment_mode,
                    notes="Auto-created from Billing update",
                    created_by=current_user.id
                )
                db.add(payment)
                db.commit() # Need ID
                db.refresh(payment)
                
                ledger_payment = models.Ledger(
                    company_id=db_bill.vendor_id,
                    transaction_date=payment.payment_date,
                    transaction_type=TransactionType.PAYMENT,
                    reference_id=payment.id,
                    reference_model="Payment",
                    debit_amount=db_bill.amount_paid,
                    credit_amount=0.0,
                    narration=f"Payment for Bill #{db_bill.bill_number}"
                )
                db.add(ledger_payment)

    db.commit()
    db.refresh(db_bill)
    
    audit.log_action(db, current_user.id, "update", "billing", bill_id, old_data, update_data)
    
    return db_bill
