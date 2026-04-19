from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserResponse, Token
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Annotated[Session, Depends(get_db)]):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(
    user_data: UserLogin,
    db: Annotated[Session, Depends(get_db)]
):
    """用户登录"""
    print(f"[登录] 尝试登录用户: {user_data.username}")

    # 查找用户
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        print(f"[登录] 用户不存在: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        print(f"[登录] 密码错误: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 生成 Token
    access_token = create_access_token(
        data={"sub": str(user.id)},  # 转成字符串
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    print(f"[登录] 成功: {user.username}, user_id: {user.id}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout():
    """用户登出"""
    return {"message": "登出成功"}


@router.post("/guest", response_model=Token)
def guest_login(
    db: Annotated[Session, Depends(get_db)]
):
    """游客登录（无需注册）"""
    print("[游客登录] 正在处理游客登录请求")

    guest_username = "guest"
    guest_password = "guest_temporary_password"

    # 查找游客用户
    user = db.query(User).filter(User.username == guest_username).first()

    if not user:
        # 创建游客用户
        print("[游客登录] 游客用户不存在，正在创建")
        hashed_password = get_password_hash(guest_password)
        user = User(
            username=guest_username,
            password_hash=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[游客登录] 游客用户创建成功: {user.id}")
    else:
        print(f"[游客登录] 使用现有游客用户: {user.id}")

    # 生成 Token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    print(f"[游客登录] Token 生成成功")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """获取当前用户信息"""
    return current_user
