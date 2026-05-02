"""
API路由模块
包含所有API路由定义
"""

from fastapi import APIRouter
from app.routers import categories, products, vending_machines, aisles, inventory, price_strategies

# 创建主路由
api_router = APIRouter()

# 包含所有子路由
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(vending_machines.router)
api_router.include_router(aisles.router)
api_router.include_router(inventory.router)
api_router.include_router(price_strategies.router)

__all__ = ["api_router"]
