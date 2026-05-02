import time
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from models.database import Permission, RolePermission, User, get_db
from schemas.schemas import PermissionCreate, BaseResponse
from utils.auth import get_current_user, get_current_active_superuser
from utils.logger import log_operation, get_execute_time

router = APIRouter(prefix="/api/permissions", tags=["权限管理"])


@router.get("", response_model=BaseResponse)
async def get_permissions(
    request: Request,
    type: Optional[str] = Query(None, description="权限类型: menu-菜单, button-按钮"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取权限列表（树形结构）
    """
    query = db.query(Permission)
    
    if type:
        query = query.filter(Permission.type == type)
    
    if is_active is not None:
        query = query.filter(Permission.is_active == is_active)
    
    permissions = query.order_by(Permission.sort_order).all()
    
    # 构建树形结构
    permission_dict = {}
    root_permissions = []
    
    for p in permissions:
        permission_dict[p.id] = {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "type": p.type,
            "parent_id": p.parent_id,
            "path": p.path,
            "icon": p.icon,
            "sort_order": p.sort_order,
            "is_active": p.is_active,
            "children": []
        }
    
    for pid, p_data in permission_dict.items():
        if p_data["parent_id"] is None:
            root_permissions.append(p_data)
        else:
            parent = permission_dict.get(p_data["parent_id"])
            if parent:
                parent["children"].append(p_data)
    
    return BaseResponse(
        code=200,
        message="success",
        data={"list": root_permissions}
    )


@router.get("/all", response_model=BaseResponse)
async def get_all_permissions(
    request: Request,
    is_active: Optional[bool] = Query(True, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有权限（扁平化列表，用于角色分配权限）
    """
    query = db.query(Permission)
    
    if is_active is not None:
        query = query.filter(Permission.is_active == is_active)
    
    permissions = query.order_by(Permission.sort_order).all()
    
    permission_list = [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "type": p.type,
            "parent_id": p.parent_id,
            "path": p.path,
            "icon": p.icon,
            "sort_order": p.sort_order
        }
        for p in permissions
    ]
    
    return BaseResponse(
        code=200,
        message="success",
        data={"list": permission_list}
    )


@router.get("/{permission_id}", response_model=BaseResponse)
async def get_permission_detail(
    request: Request,
    permission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取权限详情
    """
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "id": permission.id,
            "name": permission.name,
            "code": permission.code,
            "type": permission.type,
            "parent_id": permission.parent_id,
            "path": permission.path,
            "icon": permission.icon,
            "sort_order": permission.sort_order,
            "is_active": permission.is_active,
            "created_at": permission.created_at.isoformat() if permission.created_at else None,
            "updated_at": permission.updated_at.isoformat() if permission.updated_at else None
        }
    )


@router.post("", response_model=BaseResponse)
async def create_permission(
    request: Request,
    permission_data: PermissionCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    创建权限
    """
    start_time = time.time()
    
    # 检查权限编码是否已存在
    existing = db.query(Permission).filter(Permission.code == permission_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限编码已存在"
        )
    
    # 检查父级权限是否存在
    if permission_data.parent_id:
        parent = db.query(Permission).filter(Permission.id == permission_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父级权限不存在"
            )
    
    # 创建权限
    permission = Permission(
        name=permission_data.name,
        code=permission_data.code,
        type=permission_data.type,
        parent_id=permission_data.parent_id,
        path=permission_data.path,
        icon=permission_data.icon,
        sort_order=permission_data.sort_order,
        is_active=True
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    await log_operation(
        request=request,
        user=current_user,
        module="权限管理",
        action="新增",
        description=f"创建权限: {permission.name}({permission.code})",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200,
        message="创建成功",
        data={"id": permission.id}
    )


@router.delete("/{permission_id}", response_model=BaseResponse)
async def delete_permission(
    request: Request,
    permission_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    删除权限
    
    注意:
    1. 有子权限的不能删除
    2. 已被角色使用的不能删除
    """
    start_time = time.time()
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    # 检查是否有子权限
    children_count = db.query(Permission).filter(Permission.parent_id == permission_id).count()
    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该权限有{children_count}个子权限，不能删除"
        )
    
    # 检查是否已被角色使用
    role_permission_count = db.query(RolePermission).filter(
        RolePermission.permission_id == permission_id
    ).count()
    if role_permission_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该权限已被{role_permission_count}个角色使用，不能删除"
        )
    
    # 删除权限
    db.delete(permission)
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="权限管理",
        action="删除",
        description=f"删除权限: {permission.name}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="删除成功")
