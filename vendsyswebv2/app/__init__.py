"""
自动售货机商品与库存管理系统
应用主模块
"""

from app.config import settings
from app.database import engine, SessionLocal, get_db, init_db
from app.models import *
from app.routers import api_router
from app.schemas import *
from app.utils.init_data import init_database, generate_test_data, reset_database

__version__ = "1.0.0"
__author__ = "Vending Machine System"

__all__ = [
    "settings",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "api_router",
    "init_database",
    "generate_test_data",
    "reset_database",
]
