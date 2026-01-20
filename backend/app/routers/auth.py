from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import auth, models, schemas, database, audit
from ..dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        # Log failed attempt
        audit.log_action(db, user.id if user else 0, "login_failed", "users", 0, None, {"email": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    refresh_token = auth.create_refresh_token(
        data={"sub": user.email, "role": user.role}
    )
    
    # Update last login
    user.last_login = auth.datetime.utcnow()
    db.commit()
    
    audit.log_action(db, user.id, "login", "users", user.id)
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = auth.decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    email = payload.get("sub")
    role = payload.get("role")
    
    # In a real app we might check if the user still exists or is active
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = auth.create_access_token(
        data={"sub": email, "role": role}, expires_delta=access_token_expires
    )
    
    # Return same refresh token or rotate it. For simplicity, returning the same or creating new.
    # Let's create new to keep expiration sliding
    new_refresh_token = auth.create_refresh_token(
        data={"sub": email, "role": role}
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit.log_action(db, current_user.id, "logout", "users", current_user.id)
    return {"message": "Successfully logged out"}
