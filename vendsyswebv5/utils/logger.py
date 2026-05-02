import time
import json
from fastapi import Request
from sqlalchemy.orm import Session
from models.database import OperationLog, User


async def log_operation(
    request: Request,
    user: User = None,
    module: str = "",
    action: str = "",
    description: str = "",
    request_params: dict = None,
    response_code: int = 200,
    execute_time: int = 0,
    db: Session = None
):
    """
    记录操作日志
    
    参数:
        request: FastAPI的Request对象
        user: 当前用户对象
        module: 模块名称
        action: 操作类型
        description: 操作描述
        request_params: 请求参数
        response_code: 响应状态码
        execute_time: 执行时间(ms)
        db: 数据库会话
    """
    if not db:
        return
    
    try:
        log = OperationLog()
        
        # 用户信息
        if user:
            log.user_id = user.id
            log.username = user.username
        
        # 模块和操作信息
        log.module = module
        log.action = action
        log.description = description
        
        # 请求信息
        log.request_method = request.method
        log.request_path = request.url.path
        
        # 请求参数
        if request_params:
            log.request_params = json.dumps(request_params, ensure_ascii=False, default=str)
        
        # 响应状态码
        log.response_code = response_code
        
        # 执行时间
        log.execute_time = execute_time
        
        # 客户端信息
        try:
            log.ip_address = request.client.host if request.client else ""
        except:
            log.ip_address = ""
        
        try:
            log.user_agent = request.headers.get("user-agent", "")
        except:
            log.user_agent = ""
        
        db.add(log)
        db.commit()
    except Exception as e:
        # 记录日志失败不影响主流程
        print(f"记录操作日志失败: {str(e)}")
        try:
            db.rollback()
        except:
            pass


def get_execute_time(start_time: float) -> int:
    """
    计算执行时间(毫秒)
    
    参数:
        start_time: 开始时间(time.time())
    
    返回:
        执行时间(毫秒)
    """
    return int((time.time() - start_time) * 1000)
