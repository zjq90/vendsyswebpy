"""
自动售后机数据统计与分析系统 - 配置模块
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    应用配置类，从环境变量读取配置
    """
    # 应用基础配置
    APP_NAME: str = "自动售后机数据统计与分析系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置 - 使用SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/vendsys.db"
    
    # 服务配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS配置 - 允许跨域请求
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # API前缀
    API_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()


# 项目基础路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 静态文件目录
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# 模板目录
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(TEMPLATE_DIR, exist_ok=True)
