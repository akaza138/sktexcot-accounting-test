from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

# This model is defined here or imported from models to avoid circular imports if separated carefully.
# For simplicity, we will assume AuditLog is defined in models.py and we import the Log function here 
# OR we define the utility here and pass the model.

def log_action(
    db: Session,
    user_id: int,
    action: str,
    table_name: str,
    record_id: Optional[int] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    try:
        # We perform a local import to avoid circular dependency if models.py imports this
        from .models import AuditLog 
        
        # Helper to serialise dicts to JSON string (if database field is Text) or let SQLAlchemy handle JSON type
        # Postgres supports JSON type directly.
        
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
        db.rollback()
