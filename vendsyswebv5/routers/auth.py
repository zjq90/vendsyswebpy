import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.database import User, Role, Permission, RolePermission, get_db
from schemas.schemas import LoginRequest, UserCreate, UserUpdate, PasswordUpdate, BaseResponse
from utils.auth import (
    hash_password, verify_password, generate_token, 
    remove_token, get_current_user
)
from utils.logger import log_operation, get_execute_time

router = APIRouter(prefix="/api/auth", tags=["认证管理"])


@router.post("/login", response_model=BaseResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    参数:
        username: 用户名
        password: 密码
    """
    start_time = time.time()
    
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user:
        await log_operation(
            request=request,
            module="认证",
            action="登录",
            description=f"用户{login_data.username}登录失败: 用户不存在",
            response_code=401,
            execute_time=get_execute_time(start_time),
            db=db
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        await log_operation(
            request=request,
            user=user,
            module="认证",
            action="登录",
            description=f"用户{login_data.username}登录失败: 用户已禁用",
            response_code=403,
            execute_time=get_execute_time(start_time),
            db=db
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 验证密码
    if not verify_password(login_data.password, user.password):
        await log_operation(
            request=request,
            user=user,
            module="认证",
            action="登录",
            description=f"用户{login_data.username}登录失败: 密码错误",
            response_code=401,
            execute_time=get_execute_time(start_time),
            db=db
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 生成token
    token = generate_token(user.id, user.username)
    
    # 更新最后登录时间
    from datetime import datetime
    user.last_login_at = datetime.now()
    db.commit()
    
    # 记录日志
    await log_operation(
        request=request,
        user=user,
        module="认证",
        action="登录",
        description=f"用户{user.username}登录成功",
        response_code=200,
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    # 获取用户权限菜单
    menus = await get_user_menus(user, db)
    
    return BaseResponse(
        code=200,
        message="登录成功",
        data={
            "token": token,
            "user_info": {
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "phone": user.phone,
                "email": user.email,
                "avatar": user.avatar,
                "role_id": user.role_id,
                "franchisee_id": user.franchisee_id,
                "is_superuser": user.is_superuser,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
            },
            "menus": menus
        }
    )


@router.post("/logout", response_model=BaseResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户登出
    """
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import Security
    
    security = HTTPBearer()
    credentials = await security(request)
    if credentials:
        remove_token(credentials.credentials)
    
    await log_operation(
        request=request,
        user=current_user,
        module="认证",
        action="登出",
        description=f"用户{current_user.username}登出",
        db=db
    )
    
    return BaseResponse(code=200, message="登出成功")


@router.get("/info", response_model=BaseResponse)
async def get_user_info(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    """
    # 获取用户权限菜单
    menus = await get_user_menus(current_user, db)
    
    # 获取角色信息
    role_name = None
    role_code = None
    if current_user.role_id:
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        if role:
            role_name = role.name
            role_code = role.code
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "real_name": current_user.real_name,
            "phone": current_user.phone,
            "email": current_user.email,
            "avatar": current_user.avatar,
            "role_id": current_user.role_id,
            "role_name": role_name,
            "role_code": role_code,
            "franchisee_id": current_user.franchisee_id,
            "is_superuser": current_user.is_superuser,
            "is_active": current_user.is_active,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            "menus": menus
        }
    )


@router.put("/password", response_model=BaseResponse)
async def change_password(
    request: Request,
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    """
    start_time = time.time()
    
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password):
        await log_operation(
            request=request,
            user=current_user,
            module="认证",
            action="修改密码",
            description="修改密码失败: 旧密码错误",
            response_code=400,
            execute_time=get_execute_time(start_time),
            db=db
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 更新密码
    current_user.password = hash_password(password_data.new_password)
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="认证",
        action="修改密码",
        description="修改密码成功",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="密码修改成功")


async def get_user_menus(user: User, db: Session):
    """
    获取用户权限菜单
    
    逻辑:
    1. 超级管理员拥有所有菜单
    2. 普通用户根据角色权限获取菜单
    """
    if user.is_superuser:
        # 超级管理员获取所有菜单
        menus = db.query(Permission).filter(
            Permission.type == "menu",
            Permission.is_active == True
        ).order_by(Permission.sort_order).all()
    else:
        # 普通用户根据角色权限获取
        if not user.role_id:
            return []
        
        # 获取角色权限
        role_permissions = db.query(RolePermission).filter(
            RolePermission.role_id == user.role_id
        ).all()
        
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        # 获取菜单
        menus = db.query(Permission).filter(
            Permission.id.in_(permission_ids),
            Permission.type == "menu",
            Permission.is_active == True
        ).order_by(Permission.sort_order).all()
    
    # 构建树形结构
    menu_dict = {}
    root_menus = []
    
    for menu in menus:
        menu_dict[menu.id] = {
            "id": menu.id,
            "name": menu.name,
            "code": menu.code,
            "type": menu.type,
            "parent_id": menu.parent_id,
            "path": menu.path,
            "icon": menu.icon,
            "sort_order": menu.sort_order,
            "children": []
        }
    
    for menu_id, menu_data in menu_dict.items():
        if menu_data["parent_id"] is None:
            root_menus.append(menu_data)
        else:
            parent = menu_dict.get(menu_data["parent_id"])
            if parent:
                parent["children"].append(menu_data)
    
    # 按排序字段排序
    root_menus.sort(key=lambda x: x["sort_order"])
    for menu in root_menus:
        menu["children"].sort(key=lambda x: x["sort_order"])
    
    return root_menus
