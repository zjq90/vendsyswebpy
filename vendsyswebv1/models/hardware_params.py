"""
硬件参数模型
监控货道电机状态、门锁状态、温湿度、电力状况等
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class HardwareParams(Base):
    """
    硬件参数记录表
    实时监控设备的硬件状态，包括电机、门锁、温湿度、电力等
    """
    __tablename__ = "hardware_params"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True, comment="设备ID")

    # 货道电机状态 (存储为JSON格式的字符串，记录每个货道的电机状态)
    lane_motor_status = Column(Text, nullable=True, comment="货道电机状态(JSON格式: {lane_id: status})")
    motor_fault_count = Column(Integer, default=0, comment="电机故障数量")

    # 门锁状态
    door_lock_status = Column(String(20), nullable=True, default="locked", comment="门锁状态: locked(已锁), unlocked(已解锁), fault(故障)")
    door_open_count = Column(Integer, default=0, comment="门开关次数")

    # 温湿度
    temperature = Column(Float, nullable=True, comment="温度(摄氏度)")
    humidity = Column(Float, nullable=True, comment="湿度(百分比)")
    target_temperature = Column(Float, nullable=True, comment="目标温度")
    temperature_unit = Column(String(5), default="C", comment="温度单位: C(摄氏度), F(华氏度)")

    # 制冷/加热系统
    cooling_system_status = Column(String(20), nullable=True, default="idle", comment="制冷系统状态: idle(待机), cooling(制冷中), heating(加热中), fault(故障)")
    heating_system_status = Column(String(20), nullable=True, default="idle", comment="加热系统状态")

    # 电力状况
    power_source = Column(String(20), nullable=True, default="mains", comment="电源类型: mains(市电), battery(电池), solar(太阳能)")
    voltage = Column(Float, nullable=True, comment="电压(V)")
    current = Column(Float, nullable=True, comment="电流(A)")
    power = Column(Float, nullable=True, comment="功率(W)")
    battery_level = Column(Integer, nullable=True, comment="电池电量(0-100)")
    battery_voltage = Column(Float, nullable=True, comment="电池电压(V)")

    # 屏幕相关
    screen_status = Column(String(20), nullable=True, default="on", comment="屏幕状态: on(开启), off(关闭), standby(待机), fault(故障)")
    screen_brightness = Column(Integer, nullable=True, default=80, comment="屏幕亮度(0-100)")
    current_ad_content = Column(String(500), nullable=True, comment="当前广告内容")

    # 其他传感器
    vibration_sensor_triggered = Column(Boolean, default=False, comment="震动传感器是否触发")
    light_sensor_value = Column(Integer, nullable=True, comment="光线传感器值")

    # 故障信息
    has_fault = Column(Boolean, default=False, comment="是否有故障")
    fault_codes = Column(Text, nullable=True, comment="故障代码列表(JSON格式)")
    fault_description = Column(Text, nullable=True, comment="故障描述")

    # 记录时间
    recorded_at = Column(DateTime, default=datetime.now, index=True, comment="记录时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联关系
    device = relationship("Device", back_populates="hardware_history")

    def __repr__(self):
        return f"<HardwareParams(id={self.id}, device_id={self.device_id}, temperature={self.temperature})>"
