import time
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from models.database import SystemConfig, User, get_db
from schemas.schemas import ConfigCreate, ConfigUpdate, BaseResponse
from utils.auth import get_current_user, get_current_active_superuser
from utils.logger import log_operation, get_execute_time

router = APIRouter(prefix="/api/configs", tags=["系统配置"])


@router.get("", response_model=BaseResponse)
async def get_configs(
    request: Request,
    category: Optional[str] = Query(None, description="配置分类"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取配置列表
    
    权限控制:
    - 公开配置(is_public=True)：所有登录用户可查看
    - 非公开配置：只有超级管理员可查看
    """
    query = db.query(SystemConfig)
    
    # 非超级管理员只能查看公开配置
    if not current_user.is_superuser:
        query = query.filter(SystemConfig.is_public == True)
    else:
        if is_public is not None:
            query = query.filter(SystemConfig.is_public == is_public)
    
    if category:
        query = query.filter(SystemConfig.category == category)
    
    configs = query.order_by(SystemConfig.category, SystemConfig.key).all()
    
    config_list = []
    for config in configs:
        config_list.append({
            "id": config.id,
            "category": config.category,
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "is_public": config.is_public,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        })
    
    return BaseResponse(
        code=200,
        message="success",
        data={"list": config_list}
    )


@router.get("/category/{category}", response_model=BaseResponse)
async def get_configs_by_category(
    request: Request,
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    按分类获取配置
    """
    query = db.query(SystemConfig).filter(SystemConfig.category == category)
    
    # 非超级管理员只能查看公开配置
    if not current_user.is_superuser:
        query = query.filter(SystemConfig.is_public == True)
    
    configs = query.all()
    
    config_dict = {}
    for config in configs:
        config_dict[config.key] = config.value
    
    return BaseResponse(
        code=200,
        message="success",
        data=config_dict
    )


@router.get("/public", response_model=BaseResponse)
async def get_public_configs(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取公开配置（无需登录）
    """
    configs = db.query(SystemConfig).filter(
        SystemConfig.is_public == True
    ).all()
    
    config_dict = {}
    for config in configs:
        config_dict[config.key] = config.value
    
    return BaseResponse(
        code=200,
        message="success",
        data=config_dict
    )


@router.get("/{config_id}", response_model=BaseResponse)
async def get_config_detail(
    request: Request,
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取配置详情
    """
    config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 非超级管理员不能查看非公开配置
    if not current_user.is_superuser and not config.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此配置"
        )
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "id": config.id,
            "category": config.category,
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "is_public": config.is_public,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
    )


@router.post("", response_model=BaseResponse)
async def create_config(
    request: Request,
    config_data: ConfigCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    创建配置
    
    权限: 只有超级管理员可以创建配置
    """
    start_time = time.time()
    
    # 检查key是否已存在
    existing = db.query(SystemConfig).filter(SystemConfig.key == config_data.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="配置键已存在"
        )
    
    # 创建配置
    config = SystemConfig(
        category=config_data.category,
        key=config_data.key,
        value=config_data.value,
        description=config_data.description,
        is_public=config_data.is_public
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    await log_operation(
        request=request,
        user=current_user,
        module="系统配置",
        action="新增",
        description=f"创建配置: {config.key}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200,
        message="创建成功",
        data={"id": config.id}
    )


@router.put("/{config_id}", response_model=BaseResponse)
async def update_config(
    request: Request,
    config_id: int,
    config_data: ConfigUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    更新配置
    
    权限: 只有超级管理员可以更新配置
    """
    start_time = time.time()
    
    config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 更新字段
    config.value = config_data.value
    if config_data.description is not None:
        config.description = config_data.description
    
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="系统配置",
        action="修改",
        description=f"修改配置: {config.key}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="更新成功")


@router.put("/batch", response_model=BaseResponse)
async def update_configs_batch(
    request: Request,
    configs: List[dict],
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    批量更新配置
    
    参数格式:
    [
        {"key": "config_key1", "value": "new_value1"},
        {"key": "config_key2", "value": "new_value2"}
    ]
    """
    start_time = time.time()
    
    updated_keys = []
    for item in configs:
        key = item.get("key")
        value = item.get("value")
        
        if key and value is not None:
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                config.value = value
                updated_keys.append(key)
    
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="系统配置",
        action="批量修改",
        description=f"批量更新配置: {', '.join(updated_keys)}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200,
        message=f"成功更新{len(updated_keys)}个配置",
        data={"updated_keys": updated_keys}
    )


@router.delete("/{config_id}", response_model=BaseResponse)
async def delete_config(
    request: Request,
    config_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    删除配置
    
    权限: 只有超级管理员可以删除配置
    """
    start_time = time.time()
    
    config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    key = config.key
    db.delete(config)
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="系统配置",
        action="删除",
        description=f"删除配置: {key}",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(code=200, message="删除成功")


# ==================== 配置分类常量 ====================
CONFIG_CATEGORIES = {
    "system": "系统参数",
    "payment": "支付配置",
    "sms": "短信服务",
    "email": "邮件服务",
    "vending": "售货机参数",
    "display": "显示配置"
}
