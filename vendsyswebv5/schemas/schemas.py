from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import re

# ==================== 通用响应模型 ====================

class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class PageResponse(BaseResponse):
    total: int = 0
    page: int = 1
    page_size: int = 10


# ==================== 登录相关模型 ====================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    
    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()


class LoginResponse(BaseResponse):
    data: dict = None


# ==================== 角色模型 ====================

class RoleCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RolePermissionUpdate(BaseModel):
    permission_ids: List[int]


# ==================== 权限模型 ====================

class PermissionCreate(BaseModel):
    name: str
    code: str
    type: str
    parent_id: Optional[int] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = 0


# ==================== 加盟商模型 ====================

class FranchiseeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="名称")
    code: str = Field(..., min_length=2, max_length=50, description="编码")
    type: str = Field(default="franchisee", description="类型")
    level: int = Field(default=1, ge=1, le=3, description="层级")
    parent_id: Optional[int] = Field(default=None, description="上级ID")
    contact_person: Optional[str] = Field(default=None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(default=None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(default=None, max_length=100, description="邮箱")
    address: Optional[str] = Field(default=None, max_length=200, description="地址")
    description: Optional[str] = Field(default=None, max_length=500, description="描述")
    
    @validator('contact_phone')
    def validate_phone(cls, v):
        if v and v.strip():
            phone_regex = r'^1[3-9]\d{9}$'
            if not re.match(phone_regex, v.strip()):
                raise ValueError('请输入有效的手机号码')
            return v.strip()
        return v
    
    @validator('contact_email')
    def validate_email(cls, v):
        if v and v.strip():
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, v.strip()):
                raise ValueError('请输入有效的邮箱地址')
            return v.strip()
        return v


class FranchiseeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100, description="名称")
    contact_person: Optional[str] = Field(default=None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(default=None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(default=None, max_length=100, description="邮箱")
    address: Optional[str] = Field(default=None, max_length=200, description="地址")
    description: Optional[str] = Field(default=None, max_length=500, description="描述")
    is_active: Optional[bool] = Field(default=None, description="状态")
    
    @validator('contact_phone')
    def validate_phone(cls, v):
        if v and v.strip():
            phone_regex = r'^1[3-9]\d{9}$'
            if not re.match(phone_regex, v.strip()):
                raise ValueError('请输入有效的手机号码')
            return v.strip()
        return v
    
    @validator('contact_email')
    def validate_email(cls, v):
        if v and v.strip():
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, v.strip()):
                raise ValueError('请输入有效的邮箱地址')
            return v.strip()
        return v


# ==================== 用户模型 ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    real_name: Optional[str] = Field(default=None, max_length=50, description="真实姓名")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号")
    email: Optional[str] = Field(default=None, max_length=100, description="邮箱")
    role_id: Optional[int] = Field(default=None, description="角色ID")
    franchisee_id: Optional[int] = Field(default=None, description="加盟商ID")
    is_superuser: bool = Field(default=False, description="是否超级管理员")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and v.strip():
            phone_regex = r'^1[3-9]\d{9}$'
            if not re.match(phone_regex, v.strip()):
                raise ValueError('请输入有效的手机号码')
            return v.strip()
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and v.strip():
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, v.strip()):
                raise ValueError('请输入有效的邮箱地址')
            return v.strip()
        return v


class UserUpdate(BaseModel):
    real_name: Optional[str] = Field(default=None, max_length=50, description="真实姓名")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号")
    email: Optional[str] = Field(default=None, max_length=100, description="邮箱")
    role_id: Optional[int] = Field(default=None, description="角色ID")
    franchisee_id: Optional[int] = Field(default=None, description="加盟商ID")
    is_active: Optional[bool] = Field(default=None, description="状态")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and v.strip():
            phone_regex = r'^1[3-9]\d{9}$'
            if not re.match(phone_regex, v.strip()):
                raise ValueError('请输入有效的手机号码')
            return v.strip()
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and v.strip():
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, v.strip()):
                raise ValueError('请输入有效的邮箱地址')
            return v.strip()
        return v


class PasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=32, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=32, description="新密码")


# ==================== 系统配置模型 ====================

class ConfigCreate(BaseModel):
    category: str
    key: str
    value: str
    description: Optional[str] = None
    is_public: bool = False


class ConfigUpdate(BaseModel):
    value: str
    description: Optional[str] = None


# ==================== 设备模型 ====================

class DeviceCreate(BaseModel):
    device_no: str
    name: Optional[str] = None
    model: Optional[str] = None
    franchisee_id: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    franchisee_id: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
