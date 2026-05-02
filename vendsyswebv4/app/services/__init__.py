"""
自动售后机数据统计与分析系统 - 服务层模块
"""
from app.services import (
    sales_service,
    products_service,
    devices_service,
    users_service,
    dashboard_service
)

__all__ = [
    "sales_service",
    "products_service",
    "devices_service",
    "users_service",
    "dashboard_service"
]
