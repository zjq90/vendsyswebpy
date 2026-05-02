import time
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from models.database import Role, Permission, RolePermission, User, get_db
from schemas.schemas import RoleCreate, RoleUpdate, RolePermissionUpdate, BaseResponse, PageResponse
from utils.auth import get_current_user, get_current_active_superuser
from utils.logger import log_operation, get_execute_time

router = APIRouter(prefix="/api/roles", tags=["角色管理"])


@router.get("", response_model=PageResponse)
async def get_roles(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="角色名称"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分页获取角色列表
    """
    start_time = time.time()
    
    # 构建查询
    query = db.query(Role)
    
    if name:
        query = query.filter(Role.name.like(f"%{name}%"))
    
    if is_active is not None:
        query = query.filter(Role.is_active == is_active)
    
    # 统计总数
    total = query.count()
    
    # 分页查询
    roles = query.order_by(Role.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 构建返回数据
    role_list = []
    for role in roles:
        # 获取权限数量
        permission_count = db.query(RolePermission).filter(
            RolePermission.role_id == role.id
        ).count()
        
        # 获取用户数量
        user_count = db.query(User).filter(
            User.role_id == role.id
        ).count()
        
        role_list.append({
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "description": role.description,
            "is_system": role.is_system,
            "is_active": role.is_active,
            "permission_count": permission_count,
            "user_count": user_count,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None
        })
    
    await log_operation(
        request=request,
        user=current_user,
        module="角色管理",
        action="查询",
        description=f"查询角色列表, 共{total}条",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return PageResponse(
        code=200,
        message="success",
        data={"list": role_list},
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/all", response_model=BaseResponse)
async def get_all_roles(
    request: Request,
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有角色（用于下拉选择）
    """
    query = db.query(Role)
    
    if is_active is not None:
        query = query.filter(Role.is_active == is_active)
    
    roles = query.order_by(Role.sort_order if hasattr(Role, 'sort_order') else Role.created_at).all()
    
    role_list = [
        {
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "is_system": role.is_system
        }
        for role in roles
    ]
    
    return BaseResponse(code=200, message="success", data={"list": role_list})


@router.get("/{role_id}", response_model=BaseResponse)
async def get_role_detail(
    request: Request,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取角色详情
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 获取角色的权限ID列表
    role_permissions = db.query(RolePermission).filter(
        RolePermission.role_id == role_id
    ).all()
    
    permission_ids = [rp.permission_id for rp in role_permissions]
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "description": role.description,
            "is_system": role.is_system,
            "is_active": role.is_active,
            "permission_ids": permission_ids,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None
        }
    )


@router.post("", response_model=BaseResponse)
async def create_role(
    request: Request,
    role_data: RoleCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    创建角色
    
    注意: 只有超级管理员可以创建角色
    """
    start_time = time.time()
    
    # 检查角色编码是否已存在
    existing = db.query(Role).filter(Role.code == role_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色编码已存在"
        )
    
    # 检查角色名称是否已存在
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名称已存在"
        )
    
    # 创建角色
    role = Role(
        name=role_data.name,
        code=role_data.code,
        description=role_data.description,
        is_system=False,
        is_active=True
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    await log_operation(
        request=request,
        user=current_user,
        module="角色管理",
        action="新增",
        description=f"创建角色: {role.name}({role.code})",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200,
        message="创建成功",
        data={"id": role.id}
    )


@router.put("/{role_id}", response_model=BaseResponse)
async def update_role(
    request: Request,
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    更新角色
    
    注意: 系统内置角色不能修改名称和编码
    """
    start_time = time.time()
    
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否为系统内置角色
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置角色不能修改"
        )
    
    # 更新字段
    update_data = role_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
    
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="角色管理",
        action="修改",
        description=f"修改角色: {role.name}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="更新成功")


@router.delete("/{role_id}", response_model=BaseResponse)
async def delete_role(
    request: Request,
    role_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    删除角色
    
    注意: 
    1. 系统内置角色不能删除
    2. 已被用户使用的角色不能删除
    """
    start_time = time.time()
    
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否为系统内置角色
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置角色不能删除"
        )
    
    # 检查是否有用户使用该角色
    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该角色已被{user_count}个用户使用，不能删除"
        )
    
    # 删除角色权限关联
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    
    # 删除角色
    db.delete(role)
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="角色管理",
        action="删除",
        description=f"删除角色: {role.name}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="删除成功")


@router.put("/{role_id}/permissions", response_model=BaseResponse)
async def update_role_permissions(
    request: Request,
    role_id: int,
    permission_data: RolePermissionUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    更新角色权限
    
    参数:
        permission_ids: 权限ID列表
    功能:
        1. 自动包含子权限的父级菜单权限
        2. 校验权限是否存在
        3. 删除旧权限并添加新权限
    """
    start_time = time.time()
    
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 获取所有权限
    all_permissions = db.query(Permission).all()
    permission_map = {p.id: p for p in all_permissions}
    
    # 构建父级ID映射，用于快速查找
    parent_map = {}
    for p in all_permissions:
        if p.parent_id:
            if p.parent_id not in parent_map:
                parent_map[p.parent_id] = []
            parent_map[p.parent_id].append(p.id)
    
    # 收集所有需要的权限ID（包含自动添加的父级权限）
    all_needed_ids = set(permission_data.permission_ids)
    
    # 递归获取所有父级权限
    def get_all_parents(perm_id):
        parents = []
        current_id = perm_id
        while current_id:
            perm = permission_map.get(current_id)
            if perm and perm.parent_id:
                parents.append(perm.parent_id)
                current_id = perm.parent_id
            else:
                break
        return parents
    
    # 为每个选中的权限添加其所有父级
    for perm_id in permission_data.permission_ids:
        parents = get_all_parents(perm_id)
        for parent_id in parents:
            all_needed_ids.add(parent_id)
    
    # 转换为列表
    final_permission_ids = list(all_needed_ids)
    
    # 检查权限是否存在
    if final_permission_ids:
        existing_permissions = db.query(Permission).filter(
            Permission.id.in_(final_permission_ids)
        ).all()
        existing_ids = {p.id for p in existing_permissions}
        
        # 检查是否有不存在的权限
        for pid in final_permission_ids:
            if pid not in existing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权限ID {pid} 不存在"
                )
    
    # 删除旧的权限关联
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    
    # 添加新的权限关联
    for permission_id in final_permission_ids:
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id
        )
        db.add(role_permission)
    
    db.commit()
    
    # 统计信息
    auto_added_count = len(final_permission_ids) - len(permission_data.permission_ids)
    
    await log_operation(
        request=request,
        user=current_user,
        module="角色管理",
        action="分配权限",
        description=f"为角色{role.name}分配{len(final_permission_ids)}个权限(自动包含{auto_added_count}个父级菜单)",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200, 
        message=f"权限更新成功，共分配{len(final_permission_ids)}个权限"
    )


@router.get("/{role_id}/permissions", response_model=BaseResponse)
async def get_role_permissions(
    request: Request,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取角色的权限列表
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 获取角色权限
    role_permissions = db.query(RolePermission).filter(
        RolePermission.role_id == role_id
    ).all()
    
    permission_ids = [rp.permission_id for rp in role_permissions]
    
    # 获取权限详情
    permissions = []
    if permission_ids:
        permissions = db.query(Permission).filter(
            Permission.id.in_(permission_ids)
        ).order_by(Permission.sort_order).all()
    
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
