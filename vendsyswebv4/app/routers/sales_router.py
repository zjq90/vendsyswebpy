"""
自动售后机数据统计与分析系统 - 销售报表路由
提供日/周/月/年维度的销售数据API
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.sales_service import SalesService
from app.schemas.schemas import ApiResponse


router = APIRouter(prefix="/sales", tags=["销售报表"])


@router.get("/summary", response_model=ApiResponse)
async def get_sales_summary(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取销售汇总统计
    包括总销售额、订单数、客单价
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = SalesService(db)
        data = await service.get_sales_summary(start, end)
        
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


@router.get("/daily", response_model=ApiResponse)
async def get_daily_sales(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    device_id: Optional[int] = Query(None, description="设备ID（可选过滤）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取日销售数据
    默认返回最近30天的数据
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = SalesService(db)
        data = await service.get_daily_sales(start, end, device_id)
        
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


@router.get("/weekly", response_model=ApiResponse)
async def get_weekly_sales(
    year: Optional[int] = Query(None, description="年份，默认当前年"),
    device_id: Optional[int] = Query(None, description="设备ID（可选过滤）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取周销售数据
    """
    try:
        service = SalesService(db)
        data = await service.get_weekly_sales(year, device_id)
        
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


@router.get("/monthly", response_model=ApiResponse)
async def get_monthly_sales(
    year: Optional[int] = Query(None, description="年份，默认当前年"),
    device_id: Optional[int] = Query(None, description="设备ID（可选过滤）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取月销售数据
    """
    try:
        service = SalesService(db)
        data = await service.get_monthly_sales(year, device_id)
        
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


@router.get("/yearly", response_model=ApiResponse)
async def get_yearly_sales(
    start_year: Optional[int] = Query(None, description="开始年份"),
    end_year: Optional[int] = Query(None, description="结束年份"),
    device_id: Optional[int] = Query(None, description="设备ID（可选过滤）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取年销售数据
    默认返回最近5年的数据
    """
    try:
        service = SalesService(db)
        data = await service.get_yearly_sales(start_year, end_year, device_id)
        
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


@router.get("/by-payment", response_model=ApiResponse)
async def get_sales_by_payment(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    按支付方式统计销售
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = SalesService(db)
        data = await service.get_sales_by_payment_method(start, end)
        
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


@router.get("/by-device", response_model=ApiResponse)
async def get_sales_by_device(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    top_n: int = Query(10, ge=1, le=100, description="返回前N个设备"),
    db: AsyncSession = Depends(get_db)
):
    """
    按设备统计销售（Top N）
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = SalesService(db)
        data = await service.get_sales_by_device(start, end, top_n)
        
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


@router.get("/payment-methods", response_model=ApiResponse)
async def get_payment_methods(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    按支付方式统计销售（别名端点）
    """
    try:
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = SalesService(db)
        data = await service.get_sales_by_payment_method(start, end)
        
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
async def get_order_list(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    device_id: Optional[int] = Query(None, description="设备ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取订单列表
    """
    try:
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = SalesService(db)
        data = await service.get_order_list(start, end, device_id, page, page_size)
        
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
