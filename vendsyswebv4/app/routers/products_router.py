"""
自动售后机数据统计与分析系统 - 商品分析路由
提供热销商品排行、滞销商品分析、毛利率分析
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.products_service import ProductsService
from app.schemas.schemas import ApiResponse


router = APIRouter(prefix="/products", tags=["商品分析"])


@router.get("/hot", response_model=ApiResponse)
async def get_hot_products(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    top_n: int = Query(20, ge=1, le=100, description="返回前N个商品"),
    category: Optional[str] = Query(None, description="商品分类（可选过滤）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取热销商品排行
    """
    try:
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = ProductsService(db)
        data = await service.get_hot_products(start, end, top_n, category)
        
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


@router.get("/slow-selling", response_model=ApiResponse)
async def get_slow_selling_products(
    days_threshold: int = Query(30, ge=7, le=90, description="滞销天数阈值"),
    min_sales_threshold: int = Query(5, ge=1, le=20, description="最低销量阈值"),
    category: Optional[str] = Query(None, description="商品分类（可选过滤）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取滞销商品分析
    """
    try:
        service = ProductsService(db)
        data = await service.get_slow_selling_products(
            days_threshold, min_sales_threshold, category
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


@router.get("/profit-margin", response_model=ApiResponse)
async def get_profit_margin_analysis(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取毛利率分析
    按商品分类统计毛利率
    """
    try:
        # 解析日期参数
        start = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        end = None
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        service = ProductsService(db)
        data = await service.get_profit_margin_analysis(start, end)
        
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


@router.get("/categories", response_model=ApiResponse)
async def get_product_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有商品分类
    """
    try:
        service = ProductsService(db)
        data = await service.get_product_categories()
        
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
async def get_products_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    category: Optional[str] = Query(None, description="商品分类（可选过滤）"),
    status: Optional[str] = Query(None, description="状态（可选过滤）"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取商品列表（支持分页和过滤）
    """
    try:
        service = ProductsService(db)
        data = await service.get_products_list(
            page, page_size, category, status, keyword
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
