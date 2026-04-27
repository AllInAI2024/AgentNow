from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.user import UserLogin, Token, UserResponse, ChangePassword, APIResponse
from app.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_db,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/login",
    response_model=Token,
    summary="用户登录",
    description="使用手机号+密码登录，返回JWT Token和用户信息"
)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.phone == login_data.phone).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    access_token = create_access_token(user_id=user.id)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/change-password",
    response_model=APIResponse,
    summary="修改密码",
    description="修改当前登录用户的密码。首次使用默认密码登录后必须调用此接口修改密码。"
)
def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与原密码相同"
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.is_default_password = False
    
    db.commit()
    db.refresh(current_user)
    
    return APIResponse(
        code=200,
        message="密码修改成功",
        data=None
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息"
)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=APIResponse,
    summary="用户登出",
    description="用户登出（前端需要删除Token）"
)
def logout():
    return APIResponse(
        code=200,
        message="登出成功",
        data=None
    )
