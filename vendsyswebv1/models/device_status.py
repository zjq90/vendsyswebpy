"""
设备状态模型
记录设备的在线/离线状态、网络连接质量、信号强度等
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class DeviceStatus(Base):
    """
    设备状态记录表
    实时记录设备的在线状态、网络质量、信号强度等
    """
    __tablename__ = "device_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True, comment="设备ID")

    # 在线状态
    is_online = Column(Boolean, default=True, comment="是否在线")
    last_online_time = Column(DateTime, nullable=True, comment="最后在线时间")

    # 网络连接质量
    network_type = Column(String(20), nullable=True, comment="网络类型: 4G, 5G, WiFi, 有线")
    network_quality = Column(Integer, nullable=True, comment="网络质量评分: 0-100")
    signal_strength = Column(Integer, nullable=True, comment="信号强度: 0-100, 越高越好")
    signal_level = Column(String(20), nullable=True, comment="信号等级: excellent(优), good(良), fair(中), poor(差)")

    # 网络延迟和丢包率
    latency_ms = Column(Integer, nullable=True, comment="网络延迟(毫秒)")
    packet_loss_rate = Column(Float, nullable=True, comment="丢包率(0-100)")

    # IP信息
    ip_address = Column(String(50), nullable=True, comment="设备IP地址")
    apn = Column(String(100), nullable=True, comment="APN接入点")

    # 记录时间
    recorded_at = Column(DateTime, default=datetime.now, index=True, comment="记录时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联关系
    device = relationship("Device", back_populates="status_history")

    def __repr__(self):
        return f"<DeviceStatus(id={self.id}, device_id={self.device_id}, is_online={self.is_online})>"
