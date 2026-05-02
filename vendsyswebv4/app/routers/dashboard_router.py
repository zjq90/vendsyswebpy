"""
自动售后机数据统计与分析系统 - 可视化大屏路由
为管理层提供全局视角的数据大屏，实时展示关键运营指标
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.schemas import ApiResponse


router = APIRouter(prefix="/dashboard", tags=["可视化大屏"])


@router.get("/overview", response_model=ApiResponse)
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db)
):
    """
    获取可视化大屏概览数据
    包括今日、本月、本年的关键指标
    """
    try:
        service = DashboardService(db)
        data = await service.get_dashboard_overview()
        
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


@router.get("/realtime-trend", response_model=ApiResponse)
async def get_realtime_sales_trend(
    hours: int = Query(24, ge=1, le=168, description="查询最近N小时的数据"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取实时销售趋势
    """
    try:
        service = DashboardService(db)
        data = await service.get_realtime_sales_trend(hours)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data={"trend": data, "hours": hours}
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/top-devices", response_model=ApiResponse)
async def get_top_devices(
    top_n: int = Query(5, ge=1, le=20, description="返回前N个设备"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日Top N设备
    """
    try:
        service = DashboardService(db)
        data = await service.get_top_devices(top_n)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data={"top_devices": data}
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/top-products", response_model=ApiResponse)
async def get_top_products(
    top_n: int = Query(10, ge=1, le=50, description="返回前N个商品"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日Top N热销商品
    """
    try:
        service = DashboardService(db)
        data = await service.get_top_products(top_n)
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data={"top_products": data}
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/payment-distribution", response_model=ApiResponse)
async def get_payment_distribution(
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日支付方式分布
    """
    try:
        service = DashboardService(db)
        data = await service.get_payment_distribution()
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data={"payment_distribution": data}
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/alerts", response_model=ApiResponse)
async def get_alert_data(
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警数据
    包括设备离线、待处理维护等
    """
    try:
        service = DashboardService(db)
        data = await service.get_alert_data()
        
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


@router.get("/hourly-sales", response_model=ApiResponse)
async def get_hourly_sales_today(
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日每小时销售数据
    """
    try:
        service = DashboardService(db)
        data = await service.get_hourly_sales_today()
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data={"hourly_sales": data}
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.get("/all-data", response_model=ApiResponse)
async def get_all_dashboard_data(
    db: AsyncSession = Depends(get_db)
):
    """
    获取大屏所有数据（一次性获取）
    用于大屏初始化加载
    """
    try:
        service = DashboardService(db)
        
        # 并行获取所有数据
        overview = await service.get_dashboard_overview()
        realtime_trend = await service.get_realtime_sales_trend(24)
        top_devices = await service.get_top_devices(5)
        top_products = await service.get_top_products(10)
        payment_distribution = await service.get_payment_distribution()
        alerts = await service.get_alert_data()
        hourly_sales = await service.get_hourly_sales_today()
        
        # 合并所有数据
        all_data = {
            "overview": overview,
            "realtime_trend": realtime_trend,
            "top_devices": top_devices,
            "top_products": top_products,
            "payment_distribution": payment_distribution,
            "alerts": alerts,
            "hourly_sales": hourly_sales,
            "update_time": datetime.now().isoformat()
        }
        
        return ApiResponse(
            code=200,
            message="获取成功",
            data=all_data
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取失败: {str(e)}",
            data=None
        )
