from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app import crud, database
from app.auth import schemas as auth_schemas
from app.database import get_db
from app.services import email_service # 导入邮件服务

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user_signup(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    # 检查 Email 和 IC No. 是否已存在
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_profile_by_ic_no(db, ic_no=user.ic_no):
        raise HTTPException(status_code=400, detail="IC number already registered")

    # 1. 创建用户 (但此时 is_active=False)
    new_user = crud.create_user(db=db, user=user)
    
    # 2. 在数据库中为该用户创建一个验证码
    try:
        verification_code = crud.create_verification_code(
            db, user_id=new_user.id, purpose="signup_verification"
        )
    except Exception as e:
        # 如果数据库操作失败，需要给出错误提示
        print(f"Error creating verification code: {e}")
        raise HTTPException(status_code=500, detail="Could not process signup, please try again.")

    # 3. 调用邮件服务发送这个验证码
    success = email_service.send_verification_email(
        recipient_email=new_user.email, code=verification_code
    )
    
    if not success:
        # 如果邮件发送失败，这是一个严重的系统问题
        # 我们应该告诉前端，但仍然要完成注册流程
        print(f"CRITICAL: Failed to send verification email to {new_user.email}")
        # 在生产环境中，这里应该有更复杂的错误处理，比如重试机制
        # 但对于用户来说，我们可以提示他们联系客服或重试
        raise HTTPException(status_code=503, detail="Could not send verification email. Please try again later.")
    
    # 4. 返回成功信息，并附上 user_id 以便下一步验证
    return {
        "message": "Signup successful! A verification code has been sent to your email.",
        "user_id": new_user.id
    }

# (新) 创建验证API
@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email_with_code(
    user_id: int,
    code: str,
    db: Session = Depends(get_db)
):
    success = crud.verify_user_code(
        db, user_id=user_id, code=code, purpose="signup_verification"
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    return {"message": "Email verified successfully! You can now log in."}