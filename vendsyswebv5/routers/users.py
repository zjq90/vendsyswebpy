import time
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List

from models.database import User, Role, Franchisee, get_db
from schemas.schemas import UserCreate, UserUpdate, PasswordUpdate, BaseResponse, PageResponse
from utils.auth import (
    get_current_user, get_current_active_superuser, 
    hash_password, check_user_permission
)
from utils.logger import log_operation, get_execute_time

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=PageResponse)
async def get_users(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名"),
    real_name: Optional[str] = Query(None, description="真实姓名"),
    phone: Optional[str] = Query(None, description="手机号"),
    role_id: Optional[int] = Query(None, description="角色ID"),
    franchisee_id: Optional[int] = Query(None, description="加盟商ID"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分页获取用户列表
    
    权限控制:
    - 超级管理员: 查看所有用户
    - 其他用户: 只能查看自己及下级加盟商的用户
    """
    start_time = time.time()
    
    # 构建查询
    query = db.query(User)
    
    # 数据权限控制
    if not current_user.is_superuser:
        # 如果用户有关联加盟商，只能查看自己及下级加盟商的用户
        if current_user.franchisee_id:
            # 获取当前加盟商及其所有下级的ID列表
            from routers.franchisees import get_all_child_franchisee_ids
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            query = query.filter(User.franchisee_id.in_(franchisee_ids))
        else:
            # 没有关联加盟商，只能查看自己
            query = query.filter(User.id == current_user.id)
    
    # 搜索条件
    if username:
        query = query.filter(User.username.like(f"%{username}%"))
    
    if real_name:
        query = query.filter(User.real_name.like(f"%{real_name}%"))
    
    if phone:
        query = query.filter(User.phone.like(f"%{phone}%"))
    
    if role_id:
        query = query.filter(User.role_id == role_id)
    
    if franchisee_id:
        query = query.filter(User.franchisee_id == franchisee_id)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # 统计总数
    total = query.count()
    
    # 分页查询
    users = query.order_by(User.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 构建返回数据
    user_list = []
    for user in users:
        # 获取角色信息
        role_name = None
        role_code = None
        if user.role_id:
            role = db.query(Role).filter(Role.id == user.role_id).first()
            if role:
                role_name = role.name
                role_code = role.code
        
        # 获取加盟商信息
        franchisee_name = None
        franchisee_code = None
        if user.franchisee_id:
            franchisee = db.query(Franchisee).filter(Franchisee.id == user.franchisee_id).first()
            if franchisee:
                franchisee_name = franchisee.name
                franchisee_code = franchisee.code
        
        user_list.append({
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "phone": user.phone,
            "email": user.email,
            "avatar": user.avatar,
            "role_id": user.role_id,
            "role_name": role_name,
            "role_code": role_code,
            "franchisee_id": user.franchisee_id,
            "franchisee_name": franchisee_name,
            "franchisee_code": franchisee_code,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        })
    
    await log_operation(
        request=request,
        user=current_user,
        module="用户管理",
        action="查询",
        description=f"查询用户列表, 共{total}条",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return PageResponse(
        code=200,
        message="success",
        data={"list": user_list},
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=BaseResponse)
async def get_user_detail(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户详情
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 数据权限检查
    if not current_user.is_superuser:
        # 只能查看自己或下级加盟商的用户
        if user_id != current_user.id:
            if current_user.franchisee_id and user.franchisee_id:
                from routers.franchisees import get_all_child_franchisee_ids
                allowed_ids = await get_all_child_franchisee_ids(
                    current_user.franchisee_id, db
                )
                allowed_ids.append(current_user.franchisee_id)
                if user.franchisee_id not in allowed_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问此用户信息"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此用户信息"
                )
    
    # 获取角色信息
    role_name = None
    role_code = None
    if user.role_id:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if role:
            role_name = role.name
            role_code = role.code
    
    # 获取加盟商信息
    franchisee_name = None
    if user.franchisee_id:
        franchisee = db.query(Franchisee).filter(Franchisee.id == user.franchisee_id).first()
        if franchisee:
            franchisee_name = franchisee.name
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "phone": user.phone,
            "email": user.email,
            "avatar": user.avatar,
            "role_id": user.role_id,
            "role_name": role_name,
            "role_code": role_code,
            "franchisee_id": user.franchisee_id,
            "franchisee_name": franchisee_name,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    )


@router.post("", response_model=BaseResponse)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建用户
    
    权限控制:
    - 超级管理员: 可创建任意用户，包括超级管理员
    - 其他用户: 只能创建自己加盟商及下级的普通用户
    """
    start_time = time.time()
    
    # 权限检查
    if not current_user.is_superuser:
        if not check_user_permission(current_user, db, "user:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无创建用户权限"
            )
        # 非超级管理员不能创建超级管理员
        if user_data.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权创建超级管理员"
            )
    
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 数据权限检查：非超级管理员只能创建自己加盟商及下级的用户
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            # 必须设置加盟商，且是自己或下级
            if not user_data.franchisee_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="请选择加盟商"
                )
            
            from routers.franchisees import get_all_child_franchisee_ids
            allowed_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            allowed_ids.append(current_user.franchisee_id)
            
            if user_data.franchisee_id not in allowed_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能创建自己及下级加盟商的用户"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户未关联加盟商，无法创建用户"
            )
    
    # 检查角色是否存在
    if user_data.role_id:
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色不存在"
            )
    
    # 检查加盟商是否存在
    if user_data.franchisee_id:
        franchisee = db.query(Franchisee).filter(
            Franchisee.id == user_data.franchisee_id
        ).first()
        if not franchisee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="加盟商不存在"
            )
    
    # 创建用户
    user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        real_name=user_data.real_name,
        phone=user_data.phone,
        email=user_data.email,
        role_id=user_data.role_id,
        franchisee_id=user_data.franchisee_id,
        is_superuser=user_data.is_superuser,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    await log_operation(
        request=request,
        user=current_user,
        module="用户管理",
        action="新增",
        description=f"创建用户: {user.username}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200,
        message="创建成功",
        data={"id": user.id}
    )


@router.put("/{user_id}", response_model=BaseResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户信息
    """
    start_time = time.time()
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 数据权限检查
    if not current_user.is_superuser:
        # 只能修改自己或下级加盟商的用户
        if user_id != current_user.id:
            if current_user.franchisee_id and user.franchisee_id:
                from routers.franchisees import get_all_child_franchisee_ids
                allowed_ids = await get_all_child_franchisee_ids(
                    current_user.franchisee_id, db
                )
                allowed_ids.append(current_user.franchisee_id)
                if user.franchisee_id not in allowed_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权修改此用户信息"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权修改此用户信息"
                )
    
    # 检查加盟商是否存在
    update_data = user_data.dict(exclude_unset=True)
    
    if "franchisee_id" in update_data and update_data["franchisee_id"]:
        franchisee = db.query(Franchisee).filter(
            Franchisee.id == update_data["franchisee_id"]
        ).first()
        if not franchisee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="加盟商不存在"
            )
    
    # 检查角色是否存在
    if "role_id" in update_data and update_data["role_id"]:
        role = db.query(Role).filter(Role.id == update_data["role_id"]).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色不存在"
            )
    
    # 更新字段
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="用户管理",
        action="修改",
        description=f"修改用户: {user.username}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="更新成功")


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    删除用户
    
    注意: 只有超级管理员可以删除用户
    """
    start_time = time.time()
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 删除用户
    username = user.username
    db.delete(user)
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="用户管理",
        action="删除",
        description=f"删除用户: {username}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="删除成功")


@router.put("/{user_id}/reset-password", response_model=BaseResponse)
async def reset_password(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    重置用户密码为默认密码
    
    默认密码: 123456
    """
    start_time = time.time()
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 重置为默认密码
    user.password = hash_password("123456")
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="用户管理",
        action="重置密码",
        description=f"重置用户密码: {user.username}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="密码已重置为默认密码: 123456")
