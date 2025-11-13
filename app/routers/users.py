from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# 使用绝对路径导入，确保稳定性
from app import crud, database
from app.auth import schemas as auth_schemas
from app.auth import security
from app.database import get_db
from app.services import email_service

# ====================================================================
#  Router Configuration
# ====================================================================

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

# OAuth2 scheme for token dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# ====================================================================
#  Dependency for Getting Current User
# ====================================================================

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get the current user from a JWT token.
    Protects routes that require a logged-in user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = security.verify_token(token, credentials_exception)
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# ====================================================================
#  API Endpoints
# ====================================================================

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a new user and send verification email")
def create_user_signup(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Handles new user registration.
    - Checks if email or IC number already exist.
    - Creates the user and profile.
    - Creates a verification code.
    - Sends the verification code via email.
    """
    # Check 1: Email existence
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check 2: IC number existence
    if user.ic_no and crud.get_profile_by_ic_no(db, ic_no=user.ic_no):
        raise HTTPException(status_code=400, detail="IC number already registered")

    # Create user in the database
    new_user = crud.create_user(db=db, user=user)
    
    # Create and send verification code
    try:
        verification_code = crud.create_verification_code(
            db, user_id=new_user.id, purpose="signup_verification"
        )
        success = email_service.send_verification_email(
            recipient_email=new_user.email, code=verification_code
        )
        if not success:
            # Raise a service unavailable error if email sending fails
            raise HTTPException(status_code=503, detail="Could not send verification email. Please try again later.")
    except Exception as e:
        print(f"Error during verification code sending: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during the signup process.")
    
    return {
        "message": "Signup successful! A verification code has been sent to your email.",
        "user_id": new_user.id
    }


@router.post("/verify-email", status_code=status.HTTP_200_OK, summary="Verify user's email with a code")
def verify_email_with_code(
    user_id: int,
    code: str,
    db: Session = Depends(get_db)
):
    """
    Verifies the 6-digit code sent to the user's email.
    If successful, activates the user's account.
    """
    success = crud.verify_user_code(
        db, user_id=user_id, code=code, purpose="signup_verification"
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    return {"message": "Email verified successfully! You can now log in."}


@router.get("/me", response_model=auth_schemas.UserOut, summary="Get current logged-in user's info")
async def read_users_me(current_user: database.User = Depends(get_current_user)):
    """
    A protected endpoint that returns the information of the currently authenticated user.
    Requires a valid JWT token in the Authorization header.
    """
    return current_user