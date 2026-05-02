"""
货道模型
定义设备内货道的信息，包括商品种类、总量、余量、货道状况
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Lane(Base):
    """
    货道表模型
    存储设备每个货道的商品信息、库存状态、货道状况等
    """
    __tablename__ = "lanes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True, comment="设备ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True, comment="商品ID")

    # 货道标识
    lane_number = Column(Integer, nullable=False, comment="货道编号")
    lane_code = Column(String(50), nullable=True, comment="货道代码")
    lane_name = Column(String(100), nullable=True, comment="货道名称")

    # 货道位置
    row = Column(Integer, nullable=True, comment="行号")
    col = Column(Integer, nullable=True, comment="列号")

    # 库存信息
    total_capacity = Column(Integer, nullable=False, default=10, comment="总容量")
    current_stock = Column(Integer, nullable=False, default=0, comment="当前库存")
    min_stock_threshold = Column(Integer, default=2, comment="最低库存预警阈值")

    # 价格信息 (可覆盖商品默认价格)
    sale_price = Column(Float, nullable=True, comment="售价(覆盖商品默认价格)")

    # 货道状态
    status = Column(String(20), nullable=False, default="normal", comment="状态: normal(正常), empty(空), fault(故障), disabled(禁用)")
    motor_status = Column(String(20), nullable=True, default="normal", comment="电机状态: normal(正常), fault(故障), stuck(卡住)")
    sensor_status = Column(String(20), nullable=True, default="normal", comment="传感器状态: normal(正常), fault(故障)")

    # 电机参数
    motor_type = Column(String(50), nullable=True, comment="电机类型")
    motor_power = Column(Integer, nullable=True, comment="电机功率")
    rotation_degrees = Column(Integer, nullable=True, comment="旋转角度")

    # 销售统计
    total_sales = Column(Integer, default=0, comment="累计销售数量")
    today_sales = Column(Integer, default=0, comment="今日销售数量")
    last_sale_time = Column(DateTime, nullable=True, comment="最后销售时间")

    # 补货信息
    last_refill_time = Column(DateTime, nullable=True, comment="最后补货时间")
    last_refill_quantity = Column(Integer, default=0, comment="最后补货数量")

    # 时间信息
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    device = relationship("Device", back_populates="lanes")
    product = relationship("Product")

    def __repr__(self):
        return f"<Lane(id={self.id}, device_id={self.device_id}, lane_number={self.lane_number}, current_stock={self.current_stock})>"

    @property
    def is_low_stock(self):
        """判断是否库存不足"""
        return self.current_stock <= self.min_stock_threshold

    @property
    def stock_percentage(self):
        """计算库存百分比"""
        if self.total_capacity == 0:
            return 0
        return int((self.current_stock / self.total_capacity) * 100)
