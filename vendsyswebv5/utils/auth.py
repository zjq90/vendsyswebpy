import hashlib
import secrets
import time
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models.database import User, get_db

# JWT模拟（简化版，实际项目建议使用PyJWT）
SECRET_KEY = "vending_system_secret_key_2024"
TOKEN_EXPIRE_SECONDS = 7200  # 2小时

# 存储token的字典，实际项目可使用Redis
token_store = {}


def hash_password(password: str) -> str:
    """
    密码加密 - 使用SHA256加盐
    实际项目建议使用bcrypt或passlib
    """
    salt = SECRET_KEY
    hash_obj = hashlib.sha256(f"{password}{salt}".encode("utf-8"))
    return hash_obj.hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password


def generate_token(user_id: int, username: str) -> str:
    """生成token"""
    timestamp = int(time.time())
    random_str = secrets.token_hex(16)
    token = f"{user_id}_{username}_{timestamp}_{random_str}"
    token_hash = hashlib.sha256(f"{token}{SECRET_KEY}".encode("utf-8")).hexdigest()
    final_token = f"{token_hash}_{user_id}_{timestamp}"
    
    # 存储token信息
    token_store[final_token] = {
        "user_id": user_id,
        "username": username,
        "created_at": timestamp,
        "expire_at": timestamp + TOKEN_EXPIRE_SECONDS
    }
    return final_token


def verify_token(token: str) -> Optional[dict]:
    """
    验证token
    返回: 包含user_id, username等信息的字典，无效返回None
    """
    if not token:
        return None
    
    token_info = token_store.get(token)
    if not token_info:
        return None
    
    # 检查是否过期
    current_time = int(time.time())
    if current_time > token_info.get("expire_at", 0):
        del token_store[token]
        return None
    
    return token_info


def remove_token(token: str):
    """移除token（登出）"""
    if token in token_store:
        del token_store[token]


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户 - 依赖项
    """
    token = credentials.credentials
    token_info = verify_token(token)
    
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = token_info.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前超级管理员 - 依赖项
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


def check_user_permission(user: User, db: Session, permission_code: str) -> bool:
    """
    检查用户是否有指定权限
    """
    # 超级管理员拥有所有权限
    if user.is_superuser:
        return True
    
    # 没有角色则没有权限
    if not user.role_id:
        return False
    
    # 延迟导入避免循环依赖
    from models.database import Role, RolePermission, Permission
    
    # 查询角色权限
    role_permissions = db.query(RolePermission).filter(
        RolePermission.role_id == user.role_id
    ).all()
    
    permission_ids = [rp.permission_id for rp in role_permissions]
    
    # 检查是否有该权限
    permission = db.query(Permission).filter(
        Permission.code == permission_code,
        Permission.id.in_(permission_ids)
    ).first()
    
    return permission is not None
