# ====================================================================
#  app/routers/users.py (Final - Local Debug Version)
# ====================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, database
from app.auth import schemas as auth_schemas
from app.database import get_db
from app.services import email_service

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user_signup(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Handles new user registration.
    1. Checks if email or IC is already registered.
    2. Creates the user in the database.
    3. Creates a verification code.
    4. Sends the verification code via the configured email service.
    """
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if crud.get_profile_by_ic_no(db, ic_no=user.ic_no):
        raise HTTPException(status_code=400, detail="IC number already registered")

    # Create user in the database
    new_user = crud.create_user(db=db, user=user)
    
    # Create a verification code associated with the new user
    verification_code = crud.create_verification_code(
        db, user_id=new_user.id, purpose="signup_verification"
    )
    
    # Attempt to send the verification email
    email_sent_successfully = email_service.send_verification_email(
        recipient_email=new_user.email, code=verification_code
    )
    
    if not email_sent_successfully:
        # If email sending fails, return a specific error to the client
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not send verification email. Please ensure the debug email server is running."
        )
    
    # If everything is successful
    return {
        "message": "Signup successful! A verification code has been 'sent' (check your debug terminal).",
        "user_id": new_user.id
    }

@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email_with_code(user_id: int, code: str, db: Session = Depends(get_db)):
    """
    Verifies the email verification code provided by the user.
    """
    success = crud.verify_user_code(db, user_id=user_id, code=code, purpose="signup_verification")
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
        
    return {"message": "Email verified successfully! You can now log in."}