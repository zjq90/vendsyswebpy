"""
数据模型模块
包含所有数据库模型定义
"""

from app.models.category import Category
from app.models.product import Product
from app.models.vending_machine import VendingMachine
from app.models.aisle import Aisle, AisleProduct
from app.models.replenishment import InventoryRecord, ReplenishmentOrder
from app.models.price_strategy import PriceStrategy
from app.database import Base

# 导出所有模型
__all__ = [
    "Base",
    "Category",
    "Product",
    "VendingMachine",
    "Aisle",
    "AisleProduct",
    "InventoryRecord",
    "ReplenishmentOrder",
    "PriceStrategy",
]
