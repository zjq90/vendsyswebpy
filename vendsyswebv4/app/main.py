"""
自动售后机数据统计与分析系统 - FastAPI主应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    await init_db()
    print(f"[OK] 数据库初始化完成: {settings.DATABASE_URL}")
    yield
    print("[OK] 应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="自动售后机数据统计与分析系统 - 提供销售报表、商品分析、设备效能分析、用户行为分析、可视化大屏等功能",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# 挂载静态文件
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# 导入路由
from app.routers import (
    sales_router,
    products_router,
    devices_router,
    users_router,
    dashboard_router
)

# 注册路由
app.include_router(sales_router.router, prefix=settings.API_PREFIX)
app.include_router(products_router.router, prefix=settings.API_PREFIX)
app.include_router(devices_router.router, prefix=settings.API_PREFIX)
app.include_router(users_router.router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router.router, prefix=settings.API_PREFIX)


# 页面路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    首页 - 销售报表页面
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/sales", response_class=HTMLResponse)
async def sales_page(request: Request):
    """
    销售报表页面
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """
    商品分析页面
    """
    return templates.TemplateResponse("products.html", {"request": request})


@app.get("/devices", response_class=HTMLResponse)
async def devices_page(request: Request):
    """
    设备效能分析页面
    """
    return templates.TemplateResponse("devices.html", {"request": request})


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """
    用户行为分析页面
    """
    return templates.TemplateResponse("users.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    可视化大屏页面
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


# 健康检查接口
@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG
        }
    )


@app.get("/api/info")
async def api_info():
    """
    获取API信息
    """
    return JSONResponse(
        content={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "api_prefix": settings.API_PREFIX,
            "endpoints": {
                "销售报表": f"{settings.API_PREFIX}/sales",
                "商品分析": f"{settings.API_PREFIX}/products",
                "设备效能": f"{settings.API_PREFIX}/devices",
                "用户行为": f"{settings.API_PREFIX}/users",
                "可视化大屏": f"{settings.API_PREFIX}/dashboard"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
