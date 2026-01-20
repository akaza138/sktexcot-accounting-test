from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime, date
from .. import models, schemas
from ..dependencies import get_db, get_current_active_user
from ..models import UserRole, TransactionType, PaymentMode

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/summary", response_model=schemas.APIResponse)
async def dashboard_summary(
    month: int = Query(datetime.now().month),
    year: int = Query(datetime.now().year),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Function to calculate totals
    def get_total_sales(m, y):
        return db.query(func.sum(models.Sales.total_amount)).filter(
            extract('month', models.Sales.invoice_date) == m,
            extract('year', models.Sales.invoice_date) == y
        ).scalar() or 0.0

    def get_total_purchases(m, y):
        return db.query(func.sum(models.Billing.total_amount)).filter(
            extract('month', models.Billing.bill_date) == m,
            extract('year', models.Billing.bill_date) == y
        ).scalar() or 0.0

    total_sales = get_total_sales(month, year)
    total_purchases = get_total_purchases(month, year)
    
    # Receivables / Payables (Outstanding) -> calculated from Ledger Summary logic generally, 
    # but for speed we can sum amount_due from Sales/Billing tables directly
    receivables = db.query(func.sum(models.Sales.amount_due)).filter(models.Sales.payment_status != 'paid').scalar() or 0.0
    payables = db.query(func.sum(models.Billing.amount_due)).filter(models.Billing.payment_status != 'paid').scalar() or 0.0
    
    # Cash Balance (Total Cash Receipts - Total Cash Payments)
    # Simple approx:
    cash_receipts = db.query(func.sum(models.Payment.amount)).filter(
        models.Payment.payment_type == TransactionType.RECEIPT,
        models.Payment.payment_mode == PaymentMode.CASH
    ).scalar() or 0.0
    
    cash_payments = db.query(func.sum(models.Payment.amount)).filter(
        models.Payment.payment_type == TransactionType.PAYMENT,
        models.Payment.payment_mode == PaymentMode.CASH
    ).scalar() or 0.0
    
    cash_balance = cash_receipts - cash_payments
    
    # Bank Balance (Total Bank Receipts - Total Bank Payments)
    # This assumes all non-cash are "Bank" for simplicity or filters specific modes
    bank_modes = [PaymentMode.BANK, PaymentMode.UPI, PaymentMode.CHEQUE, PaymentMode.NEFT, PaymentMode.RTGS]
    bank_receipts = db.query(func.sum(models.Payment.amount)).filter(
        models.Payment.payment_type == TransactionType.RECEIPT,
        models.Payment.payment_mode.in_(bank_modes)
    ).scalar() or 0.0
    
    bank_payments = db.query(func.sum(models.Payment.amount)).filter(
        models.Payment.payment_type == TransactionType.PAYMENT,
        models.Payment.payment_mode.in_(bank_modes)
    ).scalar() or 0.0
    
    bank_balance = bank_receipts - bank_payments
    
    # GST Output (Sales)
    gst_output = db.query(
        func.sum(models.Sales.cgst_amount) + 
        func.sum(models.Sales.sgst_amount) + 
        func.sum(models.Sales.igst_amount)
    ).filter(
        extract('month', models.Sales.invoice_date) == month,
        extract('year', models.Sales.invoice_date) == year
    ).scalar() or 0.0
    
    # GST Input (Purchases)
    gst_input = db.query(func.sum(models.Billing.gst_amount)).filter(
        extract('month', models.Billing.bill_date) == month,
        extract('year', models.Billing.bill_date) == year
    ).scalar() or 0.0
    
    # TDS Deducted
    tds_deducted = db.query(func.sum(models.Billing.tds_amount)).filter(
        extract('month', models.Billing.bill_date) == month,
        extract('year', models.Billing.bill_date) == year
    ).scalar() or 0.0

    return {
        "success": True,
        "data": {
            "sales_total": total_sales,
            "purchase_total": total_purchases,
            "receivables": receivables,
            "payables": payables,
            "cash_balance": cash_balance,
            "bank_balance": bank_balance,
            "gst_payable": gst_output - gst_input,
            "tds_deducted": tds_deducted,
            "profit_loss": total_sales - total_purchases # Rough P&L
        },
        "message": "Dashboard summary"
    }

@router.get("/charts", response_model=schemas.APIResponse)
async def dashboard_charts(
    period: str = "12months",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Sales vs Purchase Trend (Last 12 months)
    # This requires complex SQL grouping by month.
    
    # Simplified approach: fetch raw data aggregated by month for last year
    # We will just return 2 arrays: sales, purchases for last 12 months?
    # Or simplified logic: Just dummy logic or basic group by?
    
    # Correct Group By for Sales
    sales_trend = db.query(
        extract('month', models.Sales.invoice_date).label('month'),
        extract('year', models.Sales.invoice_date).label('year'),
        func.sum(models.Sales.total_amount).label('total')
    ).group_by(
        extract('year', models.Sales.invoice_date),
        extract('month', models.Sales.invoice_date)
    ).order_by(
        extract('year', models.Sales.invoice_date).desc(),
        extract('month', models.Sales.invoice_date).desc()
    ).limit(12).all()
    
    # Convert to friendly format
    sales_data = {}
    for entry in sales_trend:
        key = f"{int(entry.month)}/{int(entry.year)}"
        sales_data[key] = entry.total
        
    purchase_trend = db.query(
        extract('month', models.Billing.bill_date).label('month'),
        extract('year', models.Billing.bill_date).label('year'),
        func.sum(models.Billing.total_amount).label('total')
    ).group_by(
        extract('year', models.Billing.bill_date),
        extract('month', models.Billing.bill_date)
    ).order_by(
        extract('year', models.Billing.bill_date).desc(),
        extract('month', models.Billing.bill_date).desc()
    ).limit(12).all()
    
    purchase_data = {}
    for entry in purchase_trend:
        key = f"{int(entry.month)}/{int(entry.year)}"
        purchase_data[key] = entry.total

    # Merge labels
    labels = sorted(list(set(list(sales_data.keys()) + list(purchase_data.keys()))), 
                   key=lambda x: (int(x.split('/')[1]), int(x.split('/')[0])))
    
    # Credit vs Debit (Receivables vs Payables)
    # Re-using logic from summary for consistent chart data
    receivables = db.query(func.sum(models.Sales.amount_due)).filter(models.Sales.payment_status != 'paid').scalar() or 0.0
    payables = db.query(func.sum(models.Billing.amount_due)).filter(models.Billing.payment_status != 'paid').scalar() or 0.0

    chart_data = {
        "labels": labels,
        "sales": [sales_data.get(l, 0) for l in labels],
        "purchases": [purchase_data.get(l, 0) for l in labels],
        "credit_debit": {
            "labels": ["Receivables (Debit)", "Payables (Credit)"],
            "data": [receivables, payables]
        }
    }
    
    return {
        "success": True,
        "data": {
            "sales_vs_purchase": chart_data
        },
        "message": "Chart data"
    }
