"""
用户相关的Pydantic模型
用于请求验证和响应格式化
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    real_name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    role: str = Field(default="salesman", description="角色: admin 或 salesman")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="电话")
    is_active: bool = Field(default=True, description="是否激活")


class UserCreate(UserBase):
    """创建用户请求模型"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    real_name: Optional[str] = Field(None, min_length=2, max_length=50, description="真实姓名")
    role: Optional[str] = Field(None, description="角色")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="电话")
    is_active: Optional[bool] = Field(None, description="是否激活")
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="新密码")


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
