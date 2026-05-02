from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Aisle(Base):
    """
    货道模型
    管理售货机的具体货道信息
    """
    __tablename__ = "aisles"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="货道ID")
    
    # 售货机ID（外键）
    vending_machine_id = Column(Integer, ForeignKey("vending_machines.id"), nullable=False, comment="售货机ID")
    
    # 货道编号（如A1, B2等）
    aisle_code = Column(String(10), nullable=False, comment="货道编号")
    
    # 行号
    row_number = Column(Integer, nullable=False, comment="行号")
    
    # 列号
    column_number = Column(Integer, nullable=False, comment="列号")
    
    # 最大容量
    max_capacity = Column(Integer, default=10, comment="最大容量")
    
    # 货道状态：empty(空), normal(正常), full(满), blocked(堵塞)
    status = Column(String(20), default="empty", comment="货道状态")
    
    # 创建时间和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系：一个货道属于一个售货机
    vending_machine = relationship("VendingMachine", back_populates="aisles")
    
    # 关系：一个货道可以有一个商品绑定
    product_binding = relationship("AisleProduct", back_populates="aisle", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        """字符串表示"""
        return f"<Aisle(id={self.id}, code='{self.aisle_code}', machine_id={self.vending_machine_id})>"


class AisleProduct(Base):
    """
    货道商品绑定模型
    将具体商品与售货机的具体货道进行绑定
    """
    __tablename__ = "aisle_products"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="绑定ID")
    
    # 货道ID（外键）
    aisle_id = Column(Integer, ForeignKey("aisles.id"), unique=True, nullable=False, comment="货道ID")
    
    # 商品ID（外键）
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    
    # 当前库存量
    current_stock = Column(Integer, default=0, comment="当前库存量")
    
    # 库存阈值（低于此值触发补货提醒）
    stock_threshold = Column(Integer, default=5, comment="库存阈值")
    
    # 销售价格（可以单独设置，为空则使用商品零售价）
    sale_price = Column(Numeric(10, 2), comment="销售价格")
    
    # 绑定状态：active(有效)，inactive(无效)
    status = Column(String(20), default="active", comment="绑定状态")
    
    # 创建时间和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系：一个绑定属于一个货道
    aisle = relationship("Aisle", back_populates="product_binding")
    
    # 关系：一个绑定属于一个商品
    product = relationship("Product", back_populates="aisle_bindings")
    
    def __repr__(self):
        """字符串表示"""
        return f"<AisleProduct(id={self.id}, aisle_id={self.aisle_id}, product_id={self.product_id})>"
    
    def is_low_stock(self):
        """检查是否低于库存阈值"""
        return self.current_stock <= self.stock_threshold
    
    def get_sale_price(self):
        """获取销售价格，优先使用货道设置的价格，否则使用商品零售价"""
        if self.sale_price is not None:
            return float(self.sale_price)
        return float(self.product.retail_price)
