from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

# ====================================================================
#  Part 1: Password Hashing & Verification
# ====================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_password(password: str) -> bytes:
    """
    A single, private helper to encode and truncate password safely for bcrypt.
    """
    return password.encode('utf-8')[:72]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.
    """
    truncated_password_bytes = _truncate_password(plain_password)
    return pwd_context.verify(truncated_password_bytes, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password.
    """
    truncated_password_bytes = _truncate_password(password)
    return pwd_context.hash(truncated_password_bytes)

# ====================================================================
#  Part 2: JWT Token Generation & Handling
# ====================================================================

SECRET_KEY = "a_very_secret_and_long_string_for_jwt_that_is_hard_to_guess"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email 
    except JWTError:
        raise credentials_exception