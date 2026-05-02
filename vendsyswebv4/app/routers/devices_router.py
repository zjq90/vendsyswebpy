"""
自动售后机数据统计与分析系统 - 设备效能分析路由
提供单机产出、故障率统计、运维成本分析
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.devices_service import DevicesService
from app.schemas.schemas import ApiResponse


router = APIRouter(prefix="/devices", tags=["设备效能分析"])


@router.get("/performance", response_model=ApiResponse)
async def get_devices_performance(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="设备状态过滤"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取设备效能分析
    包括单机产出、故障率统计
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = DevicesService(db)
        data = await service.get_devices_performance(start, end, status)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data={"devices_performance": data}
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/overview", response_model=ApiResponse)
async def get_devices_overview(
    db: AsyncSession = Depends(get_db)
):
    """
    获取设备概览统计
    包括设备总数、在线数、离线数等
    """
    try:
        service = DevicesService(db)
        data = await service.get_devices_overview()
        
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


@router.get("/maintenance", response_model=ApiResponse)
async def get_maintenance_analysis(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取运维分析
    包括运维成本分析、故障统计
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = DevicesService(db)
        data = await service.get_maintenance_analysis(start, end)
        
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


@router.get("/maintenance-analysis", response_model=ApiResponse)
async def get_maintenance_analysis_alias(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取运维分析（别名端点）
    """
    try:
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = DevicesService(db)
        data = await service.get_maintenance_analysis(start, end)
        
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


@router.get("/low-stock", response_model=ApiResponse)
async def get_low_stock_devices(
    min_threshold: int = Query(3, ge=1, le=10, description="最低库存阈值"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取库存不足的设备
    """
    try:
        service = DevicesService(db)
        data = await service.get_low_stock_devices(min_threshold)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data={"low_stock_devices": data}
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/list", response_model=ApiResponse)
async def get_devices_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    status: Optional[str] = Query(None, description="设备状态过滤"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取设备列表（支持分页和过滤）
    """
    try:
        service = DevicesService(db)
        data = await service.get_devices_list(
            page, page_size, status, keyword
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
