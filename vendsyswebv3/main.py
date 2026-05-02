"""
自动售货机订单交易管理系统
主应用入口文件
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exception_handlers import RequestValidationError
import os

from config import settings, get_project_root, get_static_dir, get_templates_dir
from database import db_manager
from routers import orders, abnormal_orders, reconciliations, invoices


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    print(f"正在启动 {settings.APP_NAME} (版本 {settings.APP_VERSION})...")
    
    # 初始化数据库
    print("正在初始化数据库...")
    await db_manager.init_db(drop_tables=False)
    print("数据库初始化完成")
    
    yield
    
    # 应用关闭时清理资源
    print("正在关闭数据库连接...")
    await db_manager.close_db()
    print(f"{settings.APP_NAME} 已关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="自动售货机订单交易管理系统 - 包含订单管理、异常订单处理、对账管理、发票管理等功能",
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
static_dir = get_static_dir()
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 配置模板
templates_dir = get_templates_dir()
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    """
    error_message = str(exc) if settings.DEBUG else "服务器内部错误"
    
    if settings.DEBUG:
        import traceback
        traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": error_message,
            "data": None
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理器
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求参数验证失败",
            "data": {"errors": errors}
        }
    )


# 注册 API 路由
app.include_router(orders.router)
app.include_router(abnormal_orders.router)
app.include_router(reconciliations.router)
app.include_router(invoices.router)


# ==================== 前端页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    首页 - 仪表盘
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    """
    订单管理页面
    """
    return templates.TemplateResponse("orders.html", {"request": request})


@app.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_detail_page(request: Request, order_id: str):
    """
    订单详情页面
    """
    return templates.TemplateResponse("order_detail.html", {"request": request, "order_id": order_id})


@app.get("/abnormal-orders", response_class=HTMLResponse)
async def abnormal_orders_page(request: Request):
    """
    异常订单管理页面
    """
    return templates.TemplateResponse("abnormal_orders.html", {"request": request})


@app.get("/reconciliations", response_class=HTMLResponse)
async def reconciliations_page(request: Request):
    """
    对账管理页面
    """
    return templates.TemplateResponse("reconciliations.html", {"request": request})


@app.get("/invoices", response_class=HTMLResponse)
async def invoices_page(request: Request):
    """
    发票管理页面
    """
    return templates.TemplateResponse("invoices.html", {"request": request})


@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """
    测试功能页面
    """
    return templates.TemplateResponse("test.html", {"request": request})


# ==================== 健康检查接口 ====================

@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "debug": settings.DEBUG
        }
    }


# ==================== API 信息接口 ====================

@app.get("/api/info")
async def api_info():
    """
    API 信息接口
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "api_prefix": settings.API_PREFIX,
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     {settings.APP_NAME:^46}     ║
║     版本: {settings.APP_VERSION:<36}     ║
║                                                            ║
║     服务地址: http://{settings.HOST}:{settings.PORT:<23} ║
║     API文档:  http://{settings.HOST}:{settings.PORT}/docs  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
