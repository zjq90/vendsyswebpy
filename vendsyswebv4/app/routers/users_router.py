"""
自动售后机数据统计与分析系统 - 用户行为分析路由
提供活跃用户数、复购率、新用户增长趋势、购买时段分布
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.users_service import UsersService
from app.schemas.schemas import ApiResponse


router = APIRouter(prefix="/users", tags=["用户行为分析"])


@router.get("/behavior", response_model=ApiResponse)
async def get_user_behavior_analysis(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户行为分析
    包括活跃用户数、复购率等
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = UsersService(db)
        data = await service.get_user_behavior_analysis(start, end)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/new-users-growth", response_model=ApiResponse)
async def get_new_users_growth(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    period_type: str = Query("day", description="周期类型: day-按日, week-按周, month-按月"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取新用户增长趋势
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = UsersService(db)
        data = await service.get_new_users_growth(start, end, period_type)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/time-distribution", response_model=ApiResponse)
async def get_purchase_time_distribution(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取购买时段分布热力图数据
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = UsersService(db)
        data = await service.get_purchase_time_distribution(start, end)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/weekday-distribution", response_model=ApiResponse)
async def get_weekday_distribution(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取按星期几的购买分布
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = UsersService(db)
        data = await service.get_weekday_distribution(start, end)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/top-users", response_model=ApiResponse)
async def get_top_users(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    top_n: int = Query(20, ge=1, le=100, description="返回前N个用户"),
    sort_by: str = Query("amount", description="排序方式: amount-按金额, orders-按订单数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取消费排行用户
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = UsersService(db)
        data = await service.get_top_users(start, end, top_n, sort_by)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/top", response_model=ApiResponse)
async def get_top_users_alias(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    top_n: int = Query(20, ge=1, le=100, description="返回前N个用户"),
    sort_by: str = Query("amount", description="排序方式: amount-按金额, orders-按订单数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取消费排行用户（别名端点）
    """
    try:
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = UsersService(db)
        data = await service.get_top_users(start, end, top_n, sort_by)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/new-growth", response_model=ApiResponse)
async def get_new_users_growth_alias(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    period_type: str = Query("day", description="周期类型: day-按日, week-按周, month-按月"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取新用户增长趋势（别名端点）
    """
    try:
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = UsersService(db)
        data = await service.get_new_users_growth(start, end, period_type)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/list", response_model=ApiResponse)
async def get_users_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    user_type: Optional[str] = Query(None, description="用户类型过滤"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表（支持分页和过滤）
    """
    try:
        service = UsersService(db)
        data = await service.get_users_list(
            page, page_size, user_type, keyword
        )
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )
