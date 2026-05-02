"""
硬件参数相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HardwareParamsBase(BaseModel):
    """硬件参数基础模型"""
    lane_motor_status: Optional[str] = Field(None, description="货道电机状态JSON")
    motor_fault_count: Optional[int] = Field(default=0, description="电机故障数量")
    door_lock_status: Optional[str] = Field(default="locked", description="门锁状态")
    door_open_count: Optional[int] = Field(default=0, description="门开关次数")
    temperature: Optional[float] = Field(None, description="温度")
    humidity: Optional[float] = Field(None, description="湿度")
    target_temperature: Optional[float] = Field(None, description="目标温度")
    cooling_system_status: Optional[str] = Field(default="idle", description="制冷系统状态")
    heating_system_status: Optional[str] = Field(default="idle", description="加热系统状态")
    power_source: Optional[str] = Field(default="mains", description="电源类型")
    voltage: Optional[float] = Field(None, description="电压")
    current: Optional[float] = Field(None, description="电流")
    power: Optional[float] = Field(None, description="功率")
    battery_level: Optional[int] = Field(None, description="电池电量")
    battery_voltage: Optional[float] = Field(None, description="电池电压")
    screen_status: Optional[str] = Field(default="on", description="屏幕状态")
    screen_brightness: Optional[int] = Field(default=80, description="屏幕亮度")
    current_ad_content: Optional[str] = Field(None, description="当前广告内容")
    vibration_sensor_triggered: Optional[bool] = Field(default=False, description="震动传感器")
    has_fault: Optional[bool] = Field(default=False, description="是否有故障")
    fault_codes: Optional[str] = Field(None, description="故障代码")
    fault_description: Optional[str] = Field(None, description="故障描述")


class HardwareParamsCreate(HardwareParamsBase):
    """创建硬件参数请求模型"""
    device_id: int = Field(..., description="设备ID")


class HardwareParamsResponse(HardwareParamsBase):
    """硬件参数响应模型"""
    id: int
    device_id: int
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
