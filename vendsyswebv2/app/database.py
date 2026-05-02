from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 创建数据库引擎
# check_same_thread=False 是SQLite特定的配置
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG  # 调试模式下显示SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类，所有模型都将继承这个类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖函数
    用于FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表
    """
    from app.models import Base, Category, Product, VendingMachine, Aisle, AisleProduct
    from app.models import InventoryRecord, ReplenishmentOrder, PriceStrategy
    Base.metadata.create_all(bind=engine)
