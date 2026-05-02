"""
命令日志模型
记录远程控制命令的执行情况
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class CommandLog(Base):
    """
    命令日志表模型
    记录所有远程控制命令的发送和执行情况
    """
    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True, comment="设备ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作用户ID")

    # 命令信息
    command_type = Column(String(50), nullable=False, comment="命令类型: reboot(重启), unlock(开锁), set_temp(设置温度), set_ad(设置广告), firmware_upgrade(固件升级)")
    command_name = Column(String(100), nullable=True, comment="命令名称")
    command_params = Column(Text, nullable=True, comment="命令参数(JSON格式)")

    # 执行状态
    status = Column(String(20), nullable=False, default="pending", comment="执行状态: pending(待执行), sent(已发送), success(成功), failed(失败), timeout(超时)")
    result_message = Column(Text, nullable=True, comment="执行结果信息")

    # 时间信息
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    executed_at = Column(DateTime, nullable=True, comment="执行时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 固件升级相关
    firmware_id = Column(Integer, ForeignKey("firmware.id"), nullable=True, comment="固件ID(仅固件升级时)")
    firmware_version = Column(String(50), nullable=True, comment="目标固件版本")
    upgrade_progress = Column(Integer, default=0, comment="升级进度(0-100)")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    device = relationship("Device", back_populates="command_logs")

    def __repr__(self):
        return f"<CommandLog(id={self.id}, device_id={self.device_id}, command_type={self.command_type}, status={self.status})>"
