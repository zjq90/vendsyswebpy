from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    """
    商品模型
    管理售货机中的商品信息
    """
    __tablename__ = "products"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="商品ID")
    
    # 商品名称
    name = Column(String(200), nullable=False, index=True, comment="商品名称")
    
    # 商品图片URL
    image_url = Column(String(500), comment="商品图片URL")
    
    # 商品规格
    specification = Column(String(100), comment="商品规格")
    
    # 条形码
    barcode = Column(String(50), unique=True, index=True, comment="条形码")
    
    # 分类ID（外键）
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, comment="分类ID")
    
    # 成本价
    cost_price = Column(Numeric(10, 2), nullable=False, comment="成本价")
    
    # 零售价
    retail_price = Column(Numeric(10, 2), nullable=False, comment="零售价")
    
    # 商品描述
    description = Column(Text, comment="商品描述")
    
    # 状态：active(上架)，inactive(下架)
    status = Column(String(20), default="active", comment="状态")
    
    # 创建时间和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系：一个商品属于一个分类
    category = relationship("Category", back_populates="products")
    
    # 关系：一个商品可以在多个货道中
    aisle_bindings = relationship("AisleProduct", back_populates="product", cascade="all, delete-orphan")
    
    # 关系：一个商品可以有多个价格策略
    price_strategies = relationship("PriceStrategy", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        """字符串表示"""
        return f"<Product(id={self.id}, name='{self.name}', barcode='{self.barcode}')>"
    
    def get_current_price(self, time_str: str = None, region: str = None):
        """
        获取当前价格，考虑价格策略
        
        Args:
            time_str: 时间字符串，格式为HH:MM
            region: 区域标识
        
        Returns:
            当前价格
        """
        # TODO: 实现价格策略逻辑
        return float(self.retail_price)
