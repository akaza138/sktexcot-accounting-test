from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from .. import models, schemas, audit
from ..dependencies import get_db, get_current_active_user, RoleChecker
from ..models import UserRole, BalanceType

router = APIRouter(
    prefix="/ledger",
    tags=["Ledger"]
)

@router.get("/company/{company_id}", response_model=schemas.APIResponse)
async def read_ledger(
    company_id: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get Opening Balance
    opening_debit = 0.0
    opening_credit = 0.0
    
    if company.balance_type == BalanceType.DEBIT:
        opening_debit = company.opening_balance
    else:
        opening_credit = company.opening_balance

    # Query Ledger Entries
    query = db.query(models.Ledger).filter(models.Ledger.company_id == company_id)
    
    if from_date:
        query = query.filter(models.Ledger.transaction_date >= from_date)
        # We need to calculate balance BEFORE from_date to provide "Brought Forward"
        # Logic: Sum all transactions BEFORE from_date
        bf_query = db.query(
            func.sum(models.Ledger.debit_amount), 
            func.sum(models.Ledger.credit_amount)
        ).filter(
            models.Ledger.company_id == company_id,
            models.Ledger.transaction_date < from_date
        )
        bf_debit, bf_credit = bf_query.first()
        opening_debit += (bf_debit or 0.0)
        opening_credit += (bf_credit or 0.0)

    if to_date:
        query = query.filter(models.Ledger.transaction_date <= to_date)
        
    entries = query.order_by(models.Ledger.transaction_date.asc(), models.Ledger.id.asc()).all()
    
    # Calculate Running Balance
    formatted_entries = []
    
    # Initial running balance
    # Net Balance = Debit - Credit
    current_balance = opening_debit - opening_credit
    
    # Add Opening Entry row if from_date is not set or we want to show it
    # Ideally frontend handles "Opening Balance" row, but we can return it as first item or separate field.
    # Let's return it as a list of entries including a virtual "Opening" row if filtered?
    # Or just return current_balance as starting point.
    
    # Let's iterate and populate running_balance
    
    for entry in entries:
        current_balance += (entry.debit_amount - entry.credit_amount)
        
        entry_dict = schemas.LedgerOut.from_orm(entry).dict()
        entry_dict["running_balance"] = current_balance
        formatted_entries.append(entry_dict)
        
    return {
        "success": True,
        "data": {
            "company": schemas.CompanyOut.from_orm(company),
            "opening_balance": {
                "debit": opening_debit,
                "credit": opening_credit,
                "net": opening_debit - opening_credit
            },
            "entries": formatted_entries,
            "closing_balance": current_balance
        },
        "message": "Ledger retrieved successfully"
    }

@router.get("/summary", response_model=schemas.APIResponse)
async def read_ledger_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Summary of all companies: Total Receivable, Total Payable
    companies = db.query(models.Company).filter(models.Company.is_active == True).all()
    
    summary_data = []
    
    total_receivable = 0.0
    total_payable = 0.0
    
    for comp in companies:
        # Calculate balance
        # Optimization: group by query if dataset large, but loop ok for small
        
        # Opening
        balance = comp.opening_balance if comp.balance_type == BalanceType.DEBIT else -comp.opening_balance
        
        # Transactions
        sums = db.query(
            func.sum(models.Ledger.debit_amount),
            func.sum(models.Ledger.credit_amount)
        ).filter(models.Ledger.company_id == comp.id).first()
        
        debits = sums[0] or 0.0
        credits = sums[1] or 0.0
        
        balance += (debits - credits)
        
        if balance > 0:
            total_receivable += balance
        else:
            total_payable += abs(balance)
            
        summary_data.append({
            "company_name": comp.name,
            "balance": balance,
            "status": "Receivable" if balance > 0 else "Payable"
        })
        
    return {
        "success": True,
        "data": {
            "total_receivable": total_receivable,
            "total_payable": total_payable,
            "details": summary_data
        },
        "message": "Ledger summary retrieved"
    }
