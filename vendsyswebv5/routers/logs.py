import time
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from models.database import OperationLog, User, get_db
from schemas.schemas import BaseResponse, PageResponse
from utils.auth import get_current_user, get_current_active_superuser
from utils.logger import log_operation, get_execute_time

router = APIRouter(prefix="/api/logs", tags=["操作日志"])


@router.get("", response_model=PageResponse)
async def get_operation_logs(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名"),
    module: Optional[str] = Query(None, description="模块"),
    action: Optional[str] = Query(None, description="操作类型"),
    start_time: Optional[str] = Query(None, description="开始时间(YYYY-MM-DD)"),
    end_time: Optional[str] = Query(None, description="结束时间(YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分页获取操作日志
    
    权限控制:
    - 超级管理员: 查看所有日志
    - 其他用户: 只能查看自己的日志
    """
    start_time_query = time.time()
    
    # 构建查询
    query = db.query(OperationLog)
    
    # 数据权限控制
    if not current_user.is_superuser:
        query = query.filter(OperationLog.user_id == current_user.id)
    
    # 搜索条件
    if username:
        query = query.filter(OperationLog.username.like(f"%{username}%"))
    
    if module:
        query = query.filter(OperationLog.module.like(f"%{module}%"))
    
    if action:
        query = query.filter(OperationLog.action.like(f"%{action}%"))
    
    # 时间范围
    if start_time:
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d")
            query = query.filter(OperationLog.created_at >= start_dt)
        except:
            pass
    
    if end_time:
        try:
            end_dt = datetime.strptime(end_time, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(OperationLog.created_at < end_dt)
        except:
            pass
    
    # 统计总数
    total = query.count()
    
    # 分页查询
    logs = query.order_by(OperationLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 构建返回数据
    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "module": log.module,
            "action": log.action,
            "description": log.description,
            "request_method": log.request_method,
            "request_path": log.request_path,
            "response_code": log.response_code,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "execute_time": log.execute_time,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    await log_operation(
        request=request,
        user=current_user,
        module="操作日志",
        action="查询",
        description=f"查询操作日志, 共{total}条",
        execute_time=get_execute_time(start_time_query),
        db=db
    )
    
    return PageResponse(
        code=200,
        message="success",
        data={"list": log_list},
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{log_id}", response_model=BaseResponse)
async def get_log_detail(
    request: Request,
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取日志详情
    """
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日志不存在"
        )
    
    # 数据权限检查
    if not current_user.is_superuser:
        if log.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此日志"
            )
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "module": log.module,
            "action": log.action,
            "description": log.description,
            "request_method": log.request_method,
            "request_path": log.request_path,
            "request_params": log.request_params,
            "response_code": log.response_code,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "execute_time": log.execute_time,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
    )


@router.delete("/clear", response_model=BaseResponse)
async def clear_old_logs(
    request: Request,
    days: int = Query(30, ge=1, description="保留天数"),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    清理指定天数前的日志
    
    权限: 只有超级管理员可以清理日志
    """
    start_time = time.time()
    
    # 计算截止时间
    cutoff_time = datetime.now() - timedelta(days=days)
    
    # 统计要删除的数量
    count = db.query(OperationLog).filter(
        OperationLog.created_at < cutoff_time
    ).count()
    
    # 删除日志
    db.query(OperationLog).filter(
        OperationLog.created_at < cutoff_time
    ).delete()
    
    db.commit()
    
    await log_operation(
        request=request,
        user=current_user,
        module="操作日志",
        action="清理",
        description=f"清理{days}天前的日志, 共删除{count}条",
        execute_time=get_execute_time(start_time),
        db=db
    )
    
    return BaseResponse(
        code=200,
        message=f"清理成功，共删除{count}条日志",
        data={"deleted_count": count}
    )


@router.get("/statistics/summary", response_model=BaseResponse)
async def get_log_statistics(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取日志统计信息
    """
    # 今日时间范围
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 今日操作数
    today_count = db.query(OperationLog).filter(
        OperationLog.created_at >= today_start,
        OperationLog.created_at <= today_end
    ).count()
    
    # 操作类型统计
    from sqlalchemy import func
    action_stats = db.query(
        OperationLog.action,
        func.count(OperationLog.id).label("count")
    ).filter(
        OperationLog.created_at >= today_start
    ).group_by(OperationLog.action).all()
    
    action_list = [{"action": s.action, "count": s.count} for s in action_stats]
    
    # 模块统计
    module_stats = db.query(
        OperationLog.module,
        func.count(OperationLog.id).label("count")
    ).filter(
        OperationLog.created_at >= today_start
    ).group_by(OperationLog.module).all()
    
    module_list = [{"module": s.module, "count": s.count} for s in module_stats]
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "today_count": today_count,
            "action_stats": action_list,
            "module_stats": module_list
        }
    )
