"""
数据验证模式模块
包含所有Pydantic验证模型
"""

from app.schemas.schemas import (
    # 分类
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    # 商品
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    # 售货机
    VendingMachineBase,
    VendingMachineCreate,
    VendingMachineUpdate,
    VendingMachineResponse,
    # 货道
    AisleBase,
    AisleCreate,
    AisleUpdate,
    AisleResponse,
    # 货道商品绑定
    AisleProductBase,
    AisleProductCreate,
    AisleProductUpdate,
    BatchAisleProductCreate,
    AisleProductResponse,
    # 库存记录
    InventoryRecordBase,
    InventoryRecordResponse,
    # 补货单
    ReplenishmentOrderBase,
    ReplenishmentOrderCreate,
    ReplenishmentOrderUpdate,
    ReplenishmentOrderResponse,
    # 价格策略
    PriceStrategyBase,
    PriceStrategyCreate,
    PriceStrategyUpdate,
    PriceStrategyResponse,
    # 销售
    SalesCreate,
    # 通用
    ApiResponse,
)

__all__ = [
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "VendingMachineBase",
    "VendingMachineCreate",
    "VendingMachineUpdate",
    "VendingMachineResponse",
    "AisleBase",
    "AisleCreate",
    "AisleUpdate",
    "AisleResponse",
    "AisleProductBase",
    "AisleProductCreate",
    "AisleProductUpdate",
    "BatchAisleProductCreate",
    "AisleProductResponse",
    "InventoryRecordBase",
    "InventoryRecordResponse",
    "ReplenishmentOrderBase",
    "ReplenishmentOrderCreate",
    "ReplenishmentOrderUpdate",
    "ReplenishmentOrderResponse",
    "PriceStrategyBase",
    "PriceStrategyCreate",
    "PriceStrategyUpdate",
    "PriceStrategyResponse",
    "SalesCreate",
    "ApiResponse",
]
