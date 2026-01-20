from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum, Float, Text, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

# Enums
class UserRole(str, enum.Enum):
    OWNER = "owner"
    ACCOUNTANT = "accountant"
    MERCHANDISER = "merchandiser"

class ProcessType(str, enum.Enum):
    KNITTING = "knitting"
    DYEING = "dyeing"
    PATTERN = "pattern"
    STITCHING = "stitching"
    FINISHING = "finishing"
    OTHER = "other"

class BalanceType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class GSTType(str, enum.Enum):
    INTRA_STATE = "intra_state" # CGST + SGST
    INTER_STATE = "inter_state" # IGST

class PaymentStatus(str, enum.Enum):
    PAID = "paid"
    UNPAID = "unpaid"
    PARTIAL = "partial"

class PaymentMode(str, enum.Enum):
    CASH = "cash"
    BANK = "bank"
    UPI = "upi"
    CHEQUE = "cheque"
    NEFT = "neft"
    RTGS = "rtgs"

class TransactionType(str, enum.Enum):
    SALE = "sale"
    PURCHASE = "purchase"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    OPENING = "opening"

# Models

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.MERCHANDISER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    process_type = Column(Enum(ProcessType), default=ProcessType.OTHER)
    address = Column(Text)
    state = Column(String)
    gst_number = Column(String, unique=True, nullable=True)
    pan_number = Column(String, unique=True, nullable=True)
    phone = Column(String)
    email = Column(String)
    contact_person = Column(String)
    opening_balance = Column(Float, default=0.0)
    balance_type = Column(Enum(BalanceType), default=BalanceType.CREDIT)
    payment_terms = Column(String)
    bank_account_no = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    process_type = Column(Enum(ProcessType))
    item_description = Column(Text, nullable=True)
    quantity = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)
    base_amount = Column(Float, default=0.0) # qty * rate
    gst_type = Column(Enum(GSTType))
    gst_rate = Column(Float, default=0.0) # percentage
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    tcs_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    amount_paid = Column(Float, default=0.0)
    amount_due = Column(Float, default=0.0)
    payment_mode = Column(Enum(PaymentMode), nullable=True) # If paid immediately
    payment_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company")
    creator = relationship("User")

class Billing(Base):
    __tablename__ = "billing"

    id = Column(Integer, primary_key=True, index=True)
    bill_number = Column(String, index=True, nullable=False) # Vendor's bill no
    bill_date = Column(Date, nullable=False)
    vendor_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    process_type = Column(String) # Changed from Enum to allow custom values
    customer_name = Column(String, nullable=True) # Added per user design
    item_description = Column(Text)
    quantity = Column(Float)
    rate = Column(Float)
    base_amount = Column(Float)
    gst_type = Column(Enum(GSTType))
    gst_rate = Column(Float)
    gst_amount = Column(Float) # Total GST
    tds_applicable = Column(Boolean, default=False)
    tds_rate = Column(Float, default=0.0)
    tds_amount = Column(Float, default=0.0)
    tds_file_date = Column(String, nullable=True)  # TDS filing date or period (flexible text field)
    total_amount = Column(Float) # Base + GST - TDS
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    amount_paid = Column(Float, default=0.0)
    amount_due = Column(Float, default=0.0)
    payment_mode = Column(Enum(PaymentMode), nullable=True)
    payment_date = Column(Date, nullable=True)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    vendor = relationship("Company")
    creator = relationship("User")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_date = Column(Date, nullable=False)
    payment_type = Column(Enum(TransactionType)) # RECEIPT or PAYMENT
    company_id = Column(Integer, ForeignKey("companies.id"))
    reference_type = Column(String) # "sales" or "billing" - not strictly FK enforced here to allow mixing? Or maybe strictly link
    # For simplicity, keeping it loose or we can have nullable FKs to both
    sales_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    billing_id = Column(Integer, ForeignKey("billing.id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    payment_mode = Column(Enum(PaymentMode))
    transaction_reference = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    sale = relationship("Sales")
    bill = relationship("Billing")
    creator = relationship("User")

class Ledger(Base):
    __tablename__ = "ledger"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(Enum(TransactionType))
    reference_id = Column(Integer) # ID of sale/purchase/payment
    reference_model = Column(String) # "Sales", "Billing", "Payment"
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    balance = Column(Float, default=0.0) # Running balance logic is complex, might calculate on fly or store
    narration = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    record_id = Column(Integer, nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
