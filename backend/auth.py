from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Annotated
import secrets

try:
    from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
    from database import get_db
    from models import User
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
    from backend.database import get_db
    from backend.models import User

# OAuth2 依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Token 生成
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """获取当前登录用户"""
    print(f"[get_current_user] 收到 token: {token[:20] if token else 'None'}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"[get_current_user] payload: {payload}")
        user_id_str = payload.get("sub")
        if user_id_str is None:
            print("[get_current_user] user_id is None")
            raise credentials_exception
        user_id = int(user_id_str)  # 转成整数
    except JWTError as e:
        print(f"[get_current_user] JWTError: {e}")
        raise credentials_exception
    except ValueError:
        print("[get_current_user] user_id 转换失败")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"[get_current_user] 用户不存在: {user_id}")
        raise credentials_exception

    print(f"[get_current_user] 找到用户: {user.username}")
    return user


def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    db: Annotated[Session, Depends(get_db)] = None
) -> Optional[User]:
    """可选的当前用户（用于公开接口）"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return db.query(User).filter(User.id == user_id).first()
    except JWTError:
        return None
