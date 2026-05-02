import time
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List

from models.database import Franchisee, User, Device, get_db
from schemas.schemas import FranchiseeCreate, FranchiseeUpdate, BaseResponse, PageResponse
from utils.auth import get_current_user, get_current_active_superuser, check_user_permission
from utils.logger import log_operation, get_execute_time

router = APIRouter(prefix="/api/franchisees", tags=["加盟商管理"])


@router.get("", response_model=PageResponse)
async def get_franchisees(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="名称"),
    code: Optional[str] = Query(None, description="编码"),
    type: Optional[str] = Query(None, description="类型: agent-代理商, franchisee-加盟商"),
    level: Optional[int] = Query(None, description="层级"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分页获取加盟商列表
    
    权限控制:
    - 超级管理员: 查看所有加盟商
    - 运营经理/其他: 根据权限查看
    - 加盟商用户: 只能查看自己及下级
    """
    start_time = time.time()
    
    # 构建查询
    query = db.query(Franchisee)
    
    # 数据权限控制
    if not current_user.is_superuser:
        # 如果用户有关联加盟商，只能查看自己及下级
        if current_user.franchisee_id:
            # 获取当前加盟商及其所有下级的ID列表
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            query = query.filter(Franchisee.id.in_(franchisee_ids))
    
    # 搜索条件
    if name:
        query = query.filter(Franchisee.name.like(f"%{name}%"))
    
    if code:
        query = query.filter(Franchisee.code.like(f"%{code}%"))
    
    if type:
        query = query.filter(Franchisee.type == type)
    
    if level:
        query = query.filter(Franchisee.level == level)
    
    if is_active is not None:
        query = query.filter(Franchisee.is_active == is_active)
    
    # 统计总数
    total = query.count()
    
    # 分页查询
    franchisees = query.order_by(Franchisee.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 构建返回数据
    franchisee_list = []
    for f in franchisees:
        # 获取上级名称
        parent_name = None
        if f.parent_id:
            parent = db.query(Franchisee).filter(Franchisee.id == f.parent_id).first()
            if parent:
                parent_name = parent.name
        
        # 获取设备数量
        device_count = db.query(Device).filter(Device.franchisee_id == f.id).count()
        
        # 获取用户数量
        user_count = db.query(User).filter(User.franchisee_id == f.id).count()
        
        franchisee_list.append({
            "id": f.id,
            "name": f.name,
            "code": f.code,
            "type": f.type,
            "level": f.level,
            "parent_id": f.parent_id,
            "parent_name": parent_name,
            "contact_person": f.contact_person,
            "contact_phone": f.contact_phone,
            "contact_email": f.contact_email,
            "address": f.address,
            "description": f.description,
            "is_active": f.is_active,
            "device_count": device_count,
            "user_count": user_count,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None
        })
    
    await log_operation(
        request=request,
        user=current_user,
        module="加盟商管理",
        action="查询",
        description=f"查询加盟商列表, 共{total}条",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return PageResponse(
        code=200,
        message="success",
        data={"list": franchisee_list},
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/all", response_model=BaseResponse)
async def get_all_franchisees(
    request: Request,
    is_active: Optional[bool] = Query(True, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有加盟商（用于下拉选择）
    """
    query = db.query(Franchisee)
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            query = query.filter(Franchisee.id.in_(franchisee_ids))
    
    if is_active is not None:
        query = query.filter(Franchisee.is_active == is_active)
    
    franchisees = query.order_by(Franchisee.level, Franchisee.created_at).all()
    
    franchisee_list = [
        {
            "id": f.id,
            "name": f.name,
            "code": f.code,
            "type": f.type,
            "level": f.level,
            "parent_id": f.parent_id
        }
        for f in franchisees
    ]
    
    return BaseResponse(code=200, message="success", data={"list": franchisee_list})


@router.get("/tree", response_model=BaseResponse)
async def get_franchisee_tree(
    request: Request,
    is_active: Optional[bool] = Query(True, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取加盟商树形结构
    """
    query = db.query(Franchisee)
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            query = query.filter(Franchisee.id.in_(franchisee_ids))
    
    if is_active is not None:
        query = query.filter(Franchisee.is_active == is_active)
    
    franchisees = query.order_by(Franchisee.level, Franchisee.created_at).all()
    
    # 构建树形结构
    franchisee_dict = {}
    root_franchisees = []
    
    for f in franchisees:
        franchisee_dict[f.id] = {
            "id": f.id,
            "name": f.name,
            "code": f.code,
            "type": f.type,
            "level": f.level,
            "parent_id": f.parent_id,
            "children": []
        }
    
    for fid, f_data in franchisee_dict.items():
        if f_data["parent_id"] is None:
            root_franchisees.append(f_data)
        else:
            parent = franchisee_dict.get(f_data["parent_id"])
            if parent:
                parent["children"].append(f_data)
    
    return BaseResponse(code=200, message="success", data={"list": root_franchisees})


@router.get("/{franchisee_id}", response_model=BaseResponse)
async def get_franchisee_detail(
    request: Request,
    franchisee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取加盟商详情
    """
    franchisee = db.query(Franchisee).filter(Franchisee.id == franchisee_id).first()
    
    if not franchisee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="加盟商不存在"
        )
    
    # 数据权限检查
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            allowed_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            allowed_ids.append(current_user.franchisee_id)
            if franchisee_id not in allowed_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此加盟商信息"
                )
    
    # 获取上级名称
    parent_name = None
    if franchisee.parent_id:
        parent = db.query(Franchisee).filter(Franchisee.id == franchisee.parent_id).first()
        if parent:
            parent_name = parent.name
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "id": franchisee.id,
            "name": franchisee.name,
            "code": franchisee.code,
            "type": franchisee.type,
            "level": franchisee.level,
            "parent_id": franchisee.parent_id,
            "parent_name": parent_name,
            "contact_person": franchisee.contact_person,
            "contact_phone": franchisee.contact_phone,
            "contact_email": franchisee.contact_email,
            "address": franchisee.address,
            "description": franchisee.description,
            "is_active": franchisee.is_active,
            "created_at": franchisee.created_at.isoformat() if franchisee.created_at else None,
            "updated_at": franchisee.updated_at.isoformat() if franchisee.updated_at else None
        }
    )


@router.post("", response_model=BaseResponse)
async def create_franchisee(
    request: Request,
    franchisee_data: FranchiseeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建加盟商
    
    权限控制:
    - 超级管理员: 可创建任意层级
    - 其他用户: 只能创建自己的下级加盟商
    """
    start_time = time.time()
    
    # 权限检查
    if not current_user.is_superuser:
        if not check_user_permission(current_user, db, "franchisee:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无创建加盟商权限"
            )
    
    # 检查编码是否已存在
    existing = db.query(Franchisee).filter(Franchisee.code == franchisee_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="加盟商编码已存在"
        )
    
    # 检查上级加盟商
    parent_franchisee = None
    parent_level = 0
    if franchisee_data.parent_id:
        parent_franchisee = db.query(Franchisee).filter(
            Franchisee.id == franchisee_data.parent_id
        ).first()
        if not parent_franchisee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="上级加盟商不存在"
            )
        parent_level = parent_franchisee.level
    
    # 非超级管理员只能创建自己的下级
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            # 当前用户的加盟商
            user_franchisee = db.query(Franchisee).filter(
                Franchisee.id == current_user.franchisee_id
            ).first()
            if user_franchisee:
                # 必须以当前用户的加盟商为上级
                if franchisee_data.parent_id != current_user.franchisee_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="只能创建自己的下级加盟商"
                    )
                # 层级 = 上级层级 + 1
                franchisee_data.level = user_franchisee.level + 1
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户未关联加盟商，无法创建"
            )
    else:
        # 超级管理员可设置层级
        if franchisee_data.parent_id and parent_franchisee:
            franchisee_data.level = parent_level + 1
    
    # 创建加盟商
    franchisee = Franchisee(
        name=franchisee_data.name,
        code=franchisee_data.code,
        type=franchisee_data.type,
        level=franchisee_data.level,
        parent_id=franchisee_data.parent_id,
        contact_person=franchisee_data.contact_person,
        contact_phone=franchisee_data.contact_phone,
        contact_email=franchisee_data.contact_email,
        address=franchisee_data.address,
        description=franchisee_data.description,
        is_active=True
    )
    
    db.add(franchisee)
    db.commit()
    db.refresh(franchisee)
    
    await log_operation(
        request=request,
        user=current_user,
        module="加盟商管理",
        action="新增",
        description=f"创建加盟商: {franchisee.name}({franchisee.code})",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200,
        message="创建成功",
        data={"id": franchisee.id}
    )


@router.put("/{franchisee_id}", response_model=BaseResponse)
async def update_franchisee(
    request: Request,
    franchisee_id: int,
    franchisee_data: FranchiseeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新加盟商
    """
    start_time = time.time()
    
    franchisee = db.query(Franchisee).filter(Franchisee.id == franchisee_id).first()
    
    if not franchisee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="加盟商不存在"
        )
    
    # 数据权限检查
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            allowed_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            allowed_ids.append(current_user.franchisee_id)
            if franchisee_id not in allowed_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权修改此加盟商信息"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改"
            )
    
    # 更新字段
    update_data = franchisee_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(franchisee, key, value)
    
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="加盟商管理",
        action="修改",
        description=f"修改加盟商: {franchisee.name}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="更新成功")


@router.delete("/{franchisee_id}", response_model=BaseResponse)
async def delete_franchisee(
    request: Request,
    franchisee_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    删除加盟商
    
    注意:
    1. 有下级加盟商的不能删除
    2. 有关联用户的不能删除
    3. 有关联设备的不能删除
    """
    start_time = time.time()
    
    franchisee = db.query(Franchisee).filter(Franchisee.id == franchisee_id).first()
    
    if not franchisee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="加盟商不存在"
        )
    
    # 检查是否有下级加盟商
    children_count = db.query(Franchisee).filter(
        Franchisee.parent_id == franchisee_id
    ).count()
    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该加盟商有{children_count}个下级，不能删除"
        )
    
    # 检查是否有关联用户
    user_count = db.query(User).filter(User.franchisee_id == franchisee_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该加盟商关联{user_count}个用户，不能删除"
        )
    
    # 检查是否有关联设备
    device_count = db.query(Device).filter(Device.franchisee_id == franchisee_id).count()
    if device_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该加盟商关联{device_count}台设备，不能删除"
        )
    
    # 删除加盟商
    db.delete(franchisee)
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="加盟商管理",
        action="删除",
        description=f"删除加盟商: {franchisee.name}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="删除成功")


async def get_all_child_franchisee_ids(parent_id: int, db: Session) -> List[int]:
    """
    递归获取所有下级加盟商的ID列表
    """
    result = []
    
    # 直接子级
    children = db.query(Franchisee).filter(
        Franchisee.parent_id == parent_id
    ).all()
    
    for child in children:
        result.append(child.id)
        # 递归获取孙级
        grand_children = await get_all_child_franchisee_ids(child.id, db)
        result.extend(grand_children)
    
    return result
