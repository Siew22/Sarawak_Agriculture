from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

# ====================================================================
#  Part 1: Password Hashing & Verification
# ====================================================================

# 创建一个密码上下文，指定使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.
    
    This function now includes truncation to handle bcrypt's 72-byte limit.
    """
    # 将明文密码编码为 bytes，然后截断到72字节，以匹配 bcrypt 的限制
    truncated_password_bytes = plain_password.encode('utf-8')[:72]
    
    return pwd_context.verify(truncated_password_bytes, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password.

    This function now includes truncation to handle bcrypt's 72-byte limit.
    """
    # 将明文密码编码为 bytes，然后截断到72字节，以匹配 bcrypt 的限制
    truncated_password_bytes = password.encode('utf-8')[:72]
    
    return pwd_context.hash(truncated_password_bytes)


# ====================================================================
#  Part 2: JWT Token Generation & Handling
# ====================================================================

# --- Configuration ---
# 警告: 在生产环境中，这些密钥绝对不能硬编码在代码里。
# 它们应该来自 .env 文件，并通过 app/config.py 加载。
# 为了快速开发，我们暂时将其留在这里。
SECRET_KEY = "a_very_secret_and_long_string_for_jwt_that_is_hard_to_guess"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Token 60分钟后过期

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 如果没有提供过期时间，则使用默认配置
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """

    Verifies a JWT token and returns the payload (e.g., username/email).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        # In a more complex app, you might create a TokenData schema here
        return email 
    except JWTError:
        raise credentials_exception