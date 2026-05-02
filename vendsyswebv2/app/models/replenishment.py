from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from app.database import Base


class InventoryRecord(Base):
    """
    库存记录模型
    记录库存变更历史，用于库存监控和追溯
    """
    __tablename__ = "inventory_records"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    
    # 货道商品绑定ID（外键）
    aisle_product_id = Column(Integer, ForeignKey("aisle_products.id"), nullable=False, comment="货道商品绑定ID")
    
    # 变更类型：sale(销售), restock(补货), manual(手动调整), sensor(传感器检测)
    change_type = Column(String(20), nullable=False, comment="变更类型")
    
    # 变更数量（正数为增加，负数为减少）
    change_quantity = Column(Integer, nullable=False, comment="变更数量")
    
    # 变更前库存
    before_stock = Column(Integer, nullable=False, comment="变更前库存")
    
    # 变更后库存
    after_stock = Column(Integer, nullable=False, comment="变更后库存")
    
    # 关联订单号（可选）
    order_number = Column(String(50), comment="关联订单号")
    
    # 操作人ID（可选）
    operator_id = Column(Integer, comment="操作人ID")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系：一个库存记录属于一个货道商品绑定
    aisle_product = relationship("AisleProduct")
    
    def __repr__(self):
        """字符串表示"""
        return f"<InventoryRecord(id={self.id}, type='{self.change_type}', qty={self.change_quantity})>"


class ReplenishmentOrder(Base):
    """
    补货单模型
    当库存低于阈值时自动生成补货单
    """
    __tablename__ = "replenishment_orders"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="补货单ID")
    
    # 补货单号
    order_number = Column(String(50), unique=True, nullable=False, index=True, comment="补货单号")
    
    # 售货机ID（外键）
    vending_machine_id = Column(Integer, ForeignKey("vending_machines.id"), nullable=False, comment="售货机ID")
    
    # 货道商品绑定ID（外键）
    aisle_product_id = Column(Integer, ForeignKey("aisle_products.id"), nullable=False, comment="货道商品绑定ID")
    
    # 当前库存
    current_stock = Column(Integer, nullable=False, comment="当前库存")
    
    # 库存阈值
    stock_threshold = Column(Integer, nullable=False, comment="库存阈值")
    
    # 建议补货数量
    suggested_quantity = Column(Integer, default=10, comment="建议补货数量")
    
    # 实际补货数量
    actual_quantity = Column(Integer, comment="实际补货数量")
    
    # 状态：pending(待处理), in_progress(处理中), completed(已完成), cancelled(已取消)
    status = Column(String(20), default="pending", comment="状态")
    
    # 优先级：low, medium, high, urgent
    priority = Column(String(20), default="medium", comment="优先级")
    
    # 负责人ID（可选）
    assignee_id = Column(Integer, comment="负责人ID")
    
    # 提醒已发送标志
    reminder_sent = Column(Integer, default=0, comment="提醒已发送")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 完成时间
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关系
    vending_machine = relationship("VendingMachine")
    aisle_product = relationship("AisleProduct")
    
    def __repr__(self):
        """字符串表示"""
        return f"<ReplenishmentOrder(id={self.id}, order_no='{self.order_number}', status='{self.status}')>"
    
    def calculate_priority(self):
        """
        根据库存情况计算优先级
        """
        if self.current_stock == 0:
            return "urgent"
        elif self.current_stock <= self.stock_threshold * 0.5:
            return "high"
        else:
            return "medium"
