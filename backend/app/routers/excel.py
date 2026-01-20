from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io
from datetime import datetime
from .. import models, schemas, audit
from ..dependencies import get_db, get_current_active_user, RoleChecker
from ..models import UserRole, ProcessType, GSTType, PaymentStatus

router = APIRouter(
    prefix="/excel",
    tags=["Excel Upload"]
)

allow_import = RoleChecker([UserRole.OWNER, UserRole.ACCOUNTANT])

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    current_user: models.User = Depends(allow_import)
):
    # Accept both .xlsx and .csv files
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload .xlsx or .csv")
    
    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            # Read CSV file
            df = pd.read_csv(io.BytesIO(contents))
            # Create a dict with the dataframe
            xls = {'Sales': df}  # Assume single sheet named Sales
        else:
            # Read Excel file
            xls = pd.ExcelFile(io.BytesIO(contents))
            xls = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
    preview_data = {}
    errors = []
    companies_found = []
    
    # For Excel files, check required sheets
    if isinstance(xls, dict):
        sheet_names = list(xls.keys())
    else:
        sheet_names = xls.sheet_names
    
    # Parse Sales/Main sheet
    sales_sheet_name = None
    for name in ['Sales', 'sales', 'Sheet1']:
        if name in sheet_names:
            sales_sheet_name = name
            break
    
    if sales_sheet_name:
        if isinstance(xls, dict):
            sales_df = xls[sales_sheet_name]
        else:
            sales_df = pd.read_excel(xls, sales_sheet_name)
            
        # Extract unique companies (assuming column named "Party" or "Company")
        company_col = None
        # Add 'Name' and 'name' to the list of potential company columns
        possible_cols = ['party', 'company', 'customer', 'vendor', 'name', 'company name', 'party name']
        for col in sales_df.columns:
            if col.lower() in possible_cols:
                company_col = col
                break
        
        if company_col:
            unique_companies = sales_df[company_col].dropna().unique().tolist()
            companies_found = [str(c) for c in unique_companies if str(c).strip()]
        
        # Basic cleaning
        sales_data = sales_df.where(pd.notnull(sales_df), None).to_dict(orient='records')
        preview_data["sales"] = sales_data[:50]  # Limit preview to 50 rows
        
    return {
        "success": True, 
        "data": preview_data,
        "companies": companies_found,
        "message": f"File parsed successfully. Found {len(companies_found)} unique companies. Please confirm import."
    }

@router.post("/import")
async def import_data(
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(allow_import)
):
    """Import confirmed data and auto-create companies"""
    imported_count = 0
    companies_created = 0
    errors = []
    
    # First, extract and create all companies
    if "companies" in data and data["companies"]:
        for company_name in data["companies"]:
            try:
                if not company_name or not str(company_name).strip():
                    continue
                    
                company_name = str(company_name).strip()
                
                # Check if exists
                existing = db.query(models.Company).filter(models.Company.name == company_name).first()
                if not existing:
                    new_company = models.Company(
                        name=company_name,
                        process_type=models.ProcessType.OTHER,
                        is_active=True
                    )
                    db.add(new_company)
                    db.commit()
                    db.refresh(new_company)
                    companies_created += 1
                    audit.log_action(db, current_user.id, "create", "companies", new_company.id, None, {"name": company_name, "source": "excel_import"})
            except Exception as e:
                errors.append(f"Company '{company_name}': {str(e)}")
    
    # Process Sales data
    if "sales" in data:
        for index, row in enumerate(data["sales"]):
            try:
                # Find company column
                company_name = None
                possible_cols = ['Party', 'party', 'Company', 'company', 'Customer', 'customer', 'Name', 'name']
                for col in possible_cols:
                    if col in row and row[col]:
                        company_name = str(row[col]).strip()
                        break
                
                if not company_name:
                    # Skip rows without company name silently (might be empty rows)
                    continue
                    
                company = db.query(models.Company).filter(models.Company.name == company_name).first()
                if not company:
                    errors.append(f"Row {index + 1}: Company '{company_name}' not found")
                    continue
                
                # Check if this row actually contains Sales data
                # We check for at least one sales-related column or value
                has_sales_data = False
                sales_indicators = ['Invoice No', 'invoice_no', 'Quantity', 'quantity', 'Rate', 'rate', 'Amount', 'amount']
                
                for key in row.keys():
                    if key in sales_indicators and row[key]:
                        has_sales_data = True
                        break
                
                # If no clear sales data, assume it's just a company import and skip sales creation
                if not has_sales_data:
                    continue

                # Check duplicate invoice
                invoice_no = str(row.get("Invoice No") or row.get("invoice_no") or f"INV-{index}")
                if db.query(models.Sales).filter(models.Sales.invoice_number == invoice_no).first():
                    errors.append(f"Row {index + 1}: Duplicate Invoice {invoice_no}")
                    continue
                    
                # Create Sale
                sale = models.Sales(
                    invoice_number=invoice_no,
                    invoice_date=pd.to_datetime(row.get("Date") or row.get("date")).date() if (row.get("Date") or row.get("date")) else datetime.now().date(),
                    company_id=company.id,
                    quantity=float(row.get("Quantity") or row.get("quantity") or 0),
                    rate=float(row.get("Rate") or row.get("rate") or 0),
                    gst_rate=float(row.get("GST%") or row.get("gst_rate") or 0),
                    gst_type=models.GSTType.INTRA_STATE,  # Default
                    payment_status=models.PaymentStatus.UNPAID,
                    created_by=current_user.id
                )
                
                # Calculate totals
                base = sale.quantity * sale.rate
                gst = base * (sale.gst_rate / 100)
                sale.base_amount = base
                sale.total_amount = base + gst
                sale.amount_due = sale.total_amount
                
                db.add(sale)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                
    db.commit()
    
    audit.log_action(db, current_user.id, "import", "excel", 0, None, {
        "sales_count": imported_count,
        "companies_created": companies_created,
        "error_count": len(errors)
    })
    
    return {
        "success": True,
        "imported_count": imported_count,
        "companies_created": companies_created,
        "errors": errors[:20]  # Limit to first 20 errors
    }
