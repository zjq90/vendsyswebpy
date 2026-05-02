import time
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from models.database import (
    Device, Transaction, Franchisee, User, 
    OperationLog, get_db
)
from schemas.schemas import BaseResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["可视化大屏"])


@router.get("/summary", response_model=BaseResponse)
async def get_dashboard_summary(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取大屏概览数据
    """
    # 今日时间范围
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 构建基础查询（考虑数据权限）
    device_query = db.query(Device)
    transaction_query = db.query(Transaction)
    franchisee_query = db.query(Franchisee)
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            from routers.franchisees import get_all_child_franchisee_ids
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            
            device_query = device_query.filter(Device.franchisee_id.in_(franchisee_ids))
            transaction_query = transaction_query.join(Device).filter(
                Device.franchisee_id.in_(franchisee_ids)
            )
            franchisee_query = franchisee_query.filter(
                Franchisee.id.in_(franchisee_ids)
            )
    
    # 设备统计
    total_devices = device_query.count()
    online_devices = device_query.filter(Device.status == "online").count()
    offline_devices = device_query.filter(Device.status == "offline").count()
    fault_devices = device_query.filter(Device.status == "fault").count()
    
    # 加盟商统计
    total_franchisees = franchisee_query.count()
    
    # 用户统计
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # 交易统计 - 今日
    today_transactions = transaction_query.filter(
        Transaction.created_at >= today_start,
        Transaction.created_at <= today_end
    )
    
    today_order_count = today_transactions.count()
    today_sales = today_transactions.filter(
        Transaction.status == "success"
    ).with_entities(
        func.sum(Transaction.pay_amount).label("total")
    ).scalar() or Decimal(0)
    
    # 交易统计 - 本月
    month_start = datetime(today.year, today.month, 1)
    month_transactions = transaction_query.filter(
        Transaction.created_at >= month_start
    )
    
    month_order_count = month_transactions.count()
    month_sales = month_transactions.filter(
        Transaction.status == "success"
    ).with_entities(
        func.sum(Transaction.pay_amount).label("total")
    ).scalar() or Decimal(0)
    
    # 交易统计 - 总计
    total_order_count = transaction_query.count()
    total_sales = transaction_query.filter(
        Transaction.status == "success"
    ).with_entities(
        func.sum(Transaction.pay_amount).label("total")
    ).scalar() or Decimal(0)
    
    # 在线率计算
    online_rate = (online_devices / total_devices * 100) if total_devices > 0 else 0
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "devices": {
                "total": total_devices,
                "online": online_devices,
                "offline": offline_devices,
                "fault": fault_devices,
                "online_rate": round(online_rate, 1)
            },
            "franchisees": {
                "total": total_franchisees
            },
            "users": {
                "total": total_users
            },
            "today": {
                "order_count": today_order_count,
                "sales": float(today_sales)
            },
            "month": {
                "order_count": month_order_count,
                "sales": float(month_sales)
            },
            "total": {
                "order_count": total_order_count,
                "sales": float(total_sales)
            }
        }
    )


@router.get("/sales-trend", response_model=BaseResponse)
async def get_sales_trend(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取销售趋势数据
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # 构建查询
    transaction_query = db.query(Transaction)
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            from routers.franchisees import get_all_child_franchisee_ids
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            transaction_query = transaction_query.join(Device).filter(
                Device.franchisee_id.in_(franchisee_ids)
            )
    
    # 按日期统计
    from sqlalchemy import cast, Date
    
    daily_stats = transaction_query.filter(
        Transaction.created_at >= datetime.combine(start_date, datetime.min.time()),
        Transaction.status == "success"
    ).with_entities(
        cast(Transaction.created_at, Date).label("date"),
        func.count(Transaction.id).label("order_count"),
        func.sum(Transaction.pay_amount).label("sales")
    ).group_by(
        cast(Transaction.created_at, Date)
    ).order_by(
        "date"
    ).all()
    
    # 构建连续日期的数据
    result = {}
    for i in range(days):
        date = start_date + timedelta(days=i)
        result[date] = {"date": date.isoformat(), "order_count": 0, "sales": 0}
    
    # 填充实际数据
    for stat in daily_stats:
        if stat.date in result:
            result[stat.date]["order_count"] = stat.order_count
            result[stat.date]["sales"] = float(stat.sales) if stat.sales else 0
    
    # 转换为列表
    trend_list = list(result.values())
    trend_list.sort(key=lambda x: x["date"])
    
    return BaseResponse(
        code=200,
        message="success",
        data={"trend": trend_list}
    )


@router.get("/device-status", response_model=BaseResponse)
async def get_device_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取设备状态分布
    """
    device_query = db.query(Device)
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            from routers.franchisees import get_all_child_franchisee_ids
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            device_query = device_query.filter(Device.franchisee_id.in_(franchisee_ids))
    
    # 按状态统计
    status_stats = device_query.with_entities(
        Device.status,
        func.count(Device.id).label("count")
    ).group_by(Device.status).all()
    
    # 构建结果
    status_dict = {
        "online": 0,
        "offline": 0,
        "fault": 0
    }
    
    status_labels = {
        "online": "在线",
        "offline": "离线",
        "fault": "故障"
    }
    
    for stat in status_stats:
        if stat.status in status_dict:
            status_dict[stat.status] = stat.count
    
    # 转换为列表格式
    result = []
    for key, value in status_dict.items():
        result.append({
            "status": key,
            "status_name": status_labels.get(key, key),
            "count": value
        })
    
    return BaseResponse(
        code=200,
        message="success",
        data={"list": result}
    )


@router.get("/top-franchisees", response_model=BaseResponse)
async def get_top_franchisees(
    request: Request,
    limit: int = Query(10, ge=1, le=20, description="返回数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取加盟商销售额排名
    """
    # 今日时间范围
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 构建查询
    query = db.query(
        Franchisee.id,
        Franchisee.name,
        Franchisee.code,
        func.count(Transaction.id).label("order_count"),
        func.sum(Transaction.pay_amount).label("sales")
    ).join(
        Device, Device.franchisee_id == Franchisee.id
    ).join(
        Transaction, Transaction.device_id == Device.id
    ).filter(
        Transaction.created_at >= today_start,
        Transaction.status == "success"
    )
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            from routers.franchisees import get_all_child_franchisee_ids
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            query = query.filter(Franchisee.id.in_(franchisee_ids))
    
    # 分组排序
    top_franchisees = query.group_by(
        Franchisee.id
    ).order_by(
        desc("sales")
    ).limit(limit).all()
    
    # 构建结果
    result = []
    for i, f in enumerate(top_franchisees):
        result.append({
            "rank": i + 1,
            "id": f.id,
            "name": f.name,
            "code": f.code,
            "order_count": f.order_count,
            "sales": float(f.sales) if f.sales else 0
        })
    
    return BaseResponse(
        code=200,
        message="success",
        data={"list": result}
    )


@router.get("/payment-stats", response_model=BaseResponse)
async def get_payment_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取支付方式统计
    """
    # 今日时间范围
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 构建查询
    query = db.query(
        Transaction.pay_type,
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.pay_amount).label("amount")
    ).filter(
        Transaction.created_at >= today_start,
        Transaction.status == "success"
    )
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            from routers.franchisees import get_all_child_franchisee_ids
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            query = query.join(Device).filter(
                Device.franchisee_id.in_(franchisee_ids)
            )
    
    # 分组统计
    payment_stats = query.group_by(Transaction.pay_type).all()
    
    # 支付方式名称映射
    pay_type_labels = {
        "wechat": "微信支付",
        "alipay": "支付宝",
        "cash": "现金",
        "unionpay": "银联"
    }
    
    # 构建结果
    result = []
    for stat in payment_stats:
        result.append({
            "pay_type": stat.pay_type,
            "pay_type_name": pay_type_labels.get(stat.pay_type, stat.pay_type),
            "count": stat.count,
            "amount": float(stat.amount) if stat.amount else 0
        })
    
    return BaseResponse(
        code=200,
        message="success",
        data={"list": result}
    )


@router.get("/real-time-orders", response_model=BaseResponse)
async def get_real_time_orders(
    request: Request,
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取实时订单数据
    """
    # 构建查询
    query = db.query(Transaction)
    
    # 数据权限控制
    if not current_user.is_superuser:
        if current_user.franchisee_id:
            from routers.franchisees import get_all_child_franchisee_ids
            franchisee_ids = await get_all_child_franchisee_ids(
                current_user.franchisee_id, db
            )
            franchisee_ids.append(current_user.franchisee_id)
            query = query.join(Device).filter(
                Device.franchisee_id.in_(franchisee_ids)
            )
    
    # 查询最近订单
    orders = query.order_by(
        Transaction.created_at.desc()
    ).limit(limit).all()
    
    # 构建结果
    result = []
    status_labels = {
        "pending": "待支付",
        "success": "成功",
        "failed": "失败",
        "refunded": "已退款"
    }
    
    pay_type_labels = {
        "wechat": "微信",
        "alipay": "支付宝",
        "cash": "现金",
        "unionpay": "银联"
    }
    
    for order in orders:
        result.append({
            "id": order.id,
            "order_no": order.order_no,
            "total_amount": float(order.total_amount) if order.total_amount else 0,
            "pay_amount": float(order.pay_amount) if order.pay_amount else 0,
            "pay_type": order.pay_type,
            "pay_type_name": pay_type_labels.get(order.pay_type, order.pay_type),
            "status": order.status,
            "status_name": status_labels.get(order.status, order.status),
            "created_at": order.created_at.isoformat() if order.created_at else None
        })
    
    return BaseResponse(
        code=200,
        message="success",
        data={"list": result}
    )
