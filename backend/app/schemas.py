from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from .models import UserRole, ProcessType, GSTType, PaymentStatus, PaymentMode, BalanceType, TransactionType

# Auth Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.MERCHANDISER
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

class UserOut(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Company Schemas
class CompanyBase(BaseModel):
    name: str
    process_type: ProcessType = ProcessType.OTHER
    address: Optional[str] = None
    state: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = None
    opening_balance: Optional[float] = 0.0
    balance_type: BalanceType = BalanceType.CREDIT
    payment_terms: Optional[str] = None
    bank_account_no: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: Optional[bool] = True

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    # ... allow updating all fields

class CompanyOut(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Sales Schemas
class SalesBase(BaseModel):
    invoice_date: date
    company_id: int
    process_type: Optional[ProcessType] = None
    item_description: Optional[str] = None
    quantity: float
    rate: float
    gst_type: GSTType
    gst_rate: float
    tcs_amount: Optional[float] = 0.0
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    amount_paid: Optional[float] = 0.0
    payment_mode: Optional[PaymentMode] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = None

class SalesCreate(SalesBase):
    pass

class SalesUpdate(BaseModel):
    invoice_date: Optional[date] = None
    company_id: Optional[int] = None
    process_type: Optional[ProcessType] = None
    item_description: Optional[str] = None
    quantity: Optional[float] = None
    rate: Optional[float] = None
    gst_type: Optional[GSTType] = None
    gst_rate: Optional[float] = None
    tcs_amount: Optional[float] = None
    amount_paid: Optional[float] = None
    payment_mode: Optional[PaymentMode] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = None

class SalesOut(SalesBase):
    id: int
    invoice_number: str
    base_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_amount: float
    amount_due: float
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    company: Optional[CompanyOut] = None

    class Config:
        from_attributes = True

# Billing Schemas
class BillingBase(BaseModel):
    bill_number: str
    bill_date: date
    vendor_id: int
    process_type: Optional[str] = None
    customer_name: Optional[str] = None
    item_description: Optional[str] = None
    quantity: float
    rate: float
    gst_type: GSTType
    gst_rate: float
    tds_applicable: bool = False
    tds_rate: Optional[float] = 0.0
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    amount_paid: Optional[float] = 0.0
    payment_mode: Optional[PaymentMode] = None
    payment_date: Optional[date] = None
    tds_file_date: Optional[str] = None
    notes: Optional[str] = None

class BillingCreate(BillingBase):
    pass

class BillingUpdate(BaseModel):
    bill_number: Optional[str] = None
    bill_date: Optional[date] = None
    vendor_id: Optional[int] = None
    process_type: Optional[str] = None
    customer_name: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[float] = None
    rate: Optional[float] = None
    gst_type: Optional[GSTType] = None
    gst_rate: Optional[float] = None
    tds_applicable: Optional[bool] = None
    tds_rate: Optional[float] = None
    amount_paid: Optional[float] = None
    payment_mode: Optional[PaymentMode] = None
    payment_date: Optional[date] = None
    tds_file_date: Optional[str] = None
    notes: Optional[str] = None

class BillingOut(BillingBase):
    id: int
    base_amount: float
    gst_amount: float
    tds_amount: float
    total_amount: float
    amount_due: float
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    vendor: Optional[CompanyOut] = None

    class Config:
        from_attributes = True

# Payment Schemas
class PaymentBase(BaseModel):
    payment_date: date
    payment_type: TransactionType
    company_id: int
    amount: float
    payment_mode: PaymentMode
    transaction_reference: Optional[str] = None
    bank_account: Optional[str] = None
    notes: Optional[str] = None
    
    # Optional links
    sales_id: Optional[int] = None
    billing_id: Optional[int] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentOut(PaymentBase):
    id: int
    created_by: int
    created_at: datetime
    
    company: Optional[CompanyOut] = None
    
    class Config:
        from_attributes = True

# Ledger Schemas
class LedgerOut(BaseModel):
    id: int
    transaction_date: date
    transaction_type: TransactionType
    reference_id: Optional[int] = None
    reference_model: Optional[str] = None
    debit_amount: float = 0.0
    credit_amount: float = 0.0
    narration: Optional[str] = None
    
    # helper for UI
    running_balance: Optional[float] = 0.0 
    
    class Config:
        from_attributes = True

# Common Response
class APIResponse(BaseModel):
    success: bool
    data: Optional[dict | list] = None
    message: Optional[str] = None
