"""
固件模型
用于管理设备固件版本和远程升级
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from database import Base


class Firmware(Base):
    """
    固件表模型
    存储固件版本信息，用于远程升级管理
    """
    __tablename__ = "firmware"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version = Column(String(50), unique=True, nullable=False, comment="固件版本号")
    version_name = Column(String(100), nullable=True, comment="版本名称")

    # 设备类型兼容
    device_type = Column(String(50), nullable=True, comment="适用设备类型")
    compatible_models = Column(String(500), nullable=True, comment="兼容型号列表(逗号分隔)")

    # 文件信息
    file_name = Column(String(200), nullable=False, comment="固件文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    md5_checksum = Column(String(32), nullable=True, comment="MD5校验值")

    # 版本信息
    release_date = Column(DateTime, nullable=True, comment="发布日期")
    description = Column(Text, nullable=True, comment="版本描述/更新内容")
    change_log = Column(Text, nullable=True, comment="更新日志")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_force_update = Column(Boolean, default=False, comment="是否强制更新")
    status = Column(String(20), default="testing", comment="状态: testing(测试中), release(发布), deprecated(废弃)")

    # 升级统计
    download_count = Column(Integer, default=0, comment="下载次数")
    update_success_count = Column(Integer, default=0, comment="升级成功次数")
    update_fail_count = Column(Integer, default=0, comment="升级失败次数")

    # 时间信息
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<Firmware(id={self.id}, version={self.version}, status={self.status})>"
