"""
自动售后机数据统计与分析系统 - 路由模块
"""
from app.routers import (
    sales_router,
    products_router,
    devices_router,
    users_router,
    dashboard_router
)

__all__ = [
    "sales_router",
    "products_router",
    "devices_router",
    "users_router",
    "dashboard_router"
]
