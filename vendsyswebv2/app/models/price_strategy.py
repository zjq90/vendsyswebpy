from datetime import datetime, time
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Time
from sqlalchemy.orm import relationship
from app.database import Base


class PriceStrategy(Base):
    """
    价格策略模型
    支持分时段定价、区域差异化定价、促销活动价格设置
    """
    __tablename__ = "price_strategies"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="策略ID")
    
    # 策略名称
    name = Column(String(100), nullable=False, comment="策略名称")
    
    # 策略类型：time_based(分时段), region_based(区域), promotion(促销活动)
    strategy_type = Column(String(20), nullable=False, comment="策略类型")
    
    # 商品ID（外键，可选，为空则应用于所有商品）
    product_id = Column(Integer, ForeignKey("products.id"), comment="商品ID")
    
    # 开始时间（时段定价使用）
    start_time = Column(Time, comment="开始时间")
    
    # 结束时间（时段定价使用）
    end_time = Column(Time, comment="结束时间")
    
    # 适用星期（逗号分隔，如1,2,3,4,5表示周一到周五）
    applicable_days = Column(String(20), comment="适用星期")
    
    # 适用区域（区域定价使用）
    applicable_region = Column(String(50), comment="适用区域")
    
    # 折扣类型：percentage(百分比折扣), fixed(固定金额), fixed_price(固定价格)
    discount_type = Column(String(20), default="percentage", comment="折扣类型")
    
    # 折扣值
    discount_value = Column(Numeric(10, 2), nullable=False, comment="折扣值")
    
    # 优先级（数值越大优先级越高）
    priority = Column(Integer, default=1, comment="优先级")
    
    # 状态：active(启用), inactive(禁用)
    status = Column(String(20), default="active", comment="状态")
    
    # 开始日期（促销活动使用）
    start_date = Column(DateTime, comment="开始日期")
    
    # 结束日期（促销活动使用）
    end_date = Column(DateTime, comment="结束日期")
    
    # 策略描述
    description = Column(Text, comment="策略描述")
    
    # 创建时间和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    product = relationship("Product", back_populates="price_strategies")
    
    def __repr__(self):
        """字符串表示"""
        return f"<PriceStrategy(id={self.id}, name='{self.name}', type='{self.strategy_type}')>"
    
    def is_applicable(self, current_time: time = None, current_day: int = None, region: str = None):
        """
        检查策略是否适用于当前情况
        
        Args:
            current_time: 当前时间
            current_day: 当前星期几（1=周一，7=周日）
            region: 区域标识
        
        Returns:
            是否适用
        """
        if self.status != "active":
            return False
        
        # 检查促销活动日期
        if self.strategy_type == "promotion":
            now = datetime.utcnow()
            if self.start_date and now < self.start_date:
                return False
            if self.end_date and now > self.end_date:
                return False
        
        # 检查时段
        if self.start_time and self.end_time and current_time:
            if not (self.start_time <= current_time <= self.end_time):
                return False
        
        # 检查星期
        if self.applicable_days and current_day is not None:
            days = [int(d.strip()) for d in self.applicable_days.split(",")]
            if current_day not in days:
                return False
        
        # 检查区域
        if self.applicable_region and region:
            if self.applicable_region != region:
                return False
        
        return True
    
    def calculate_price(self, original_price: float):
        """
        根据策略计算价格
        
        Args:
            original_price: 原始价格
        
        Returns:
            计算后的价格
        """
        if self.discount_type == "percentage":
            # 百分比折扣，如80表示8折
            return original_price * (float(self.discount_value) / 100)
        elif self.discount_type == "fixed":
            # 固定金额折扣
            return max(0, original_price - float(self.discount_value))
        elif self.discount_type == "fixed_price":
            # 固定价格
            return float(self.discount_value)
        else:
            return original_price
