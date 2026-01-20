from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app import models, auth
from app.models import UserRole

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if we have users
    if not db.query(models.User).first():
        print("Seeding default users...")
        
        users = [
            {
                "email": "admin@sktexcot.com",
                "password": "admin123", 
                "full_name": "System Admin",
                "role": UserRole.OWNER
            },
            {
                "email": "accountant@sktexcot.com",
                "password": "Account@123",
                "full_name": "Accountant User",
                "role": UserRole.ACCOUNTANT
            },
            {
                "email": "merchandiser@sktexcot.com",
                "password": "Merch@123",
                "full_name": "Merchandiser User",
                "role": UserRole.MERCHANDISER
            }
        ]
        
        for u in users:
            hashed = auth.get_password_hash(u["password"])
            db_user = models.User(
                email=u["email"],
                password_hash=hashed,
                full_name=u["full_name"],
                role=u["role"],
                is_active=True
            )
            db.add(db_user)
        
        db.commit()
        print("Users seeded successfully.")
    else:
        print("Database already initialized.")
    
    db.close()

if __name__ == "__main__":
    init_db()
