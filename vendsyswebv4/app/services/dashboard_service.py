"""
自动售后机数据统计与分析系统 - 可视化大屏服务
为管理层提供全局视角的数据大屏，实时展示关键运营指标
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.models.models import Order, Device, User, Maintenance, Product, OrderItem


class DashboardService:
    """可视化大屏服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """
        获取可视化大屏概览数据
        包括今日、本月、本年的关键指标
        """
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 本月范围
        month_start = datetime(today.year, today.month, 1)
        if today.month == 12:
            month_end = datetime(today.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            month_end = datetime(today.year, today.month + 1, 1) - timedelta(seconds=1)
        
        # 本年范围
        year_start = datetime(today.year, 1, 1)
        year_end = datetime(today.year + 1, 1, 1) - timedelta(seconds=1)
        
        # 今日销售数据
        today_query = select(
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= today_start,
                Order.order_time <= today_end
            )
        )
        today_result = await self.db.execute(today_query)
        today_row = today_result.fetchone()
        today_orders = int(today_row.orders or 0)
        today_amount = float(today_row.amount or 0)
        
        # 本月销售数据
        month_query = select(
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= month_start,
                Order.order_time <= month_end
            )
        )
        month_result = await self.db.execute(month_query)
        month_row = month_result.fetchone()
        month_orders = int(month_row.orders or 0)
        month_amount = float(month_row.amount or 0)
        
        # 本年销售数据
        year_query = select(
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= year_start,
                Order.order_time <= year_end
            )
        )
        year_result = await self.db.execute(year_query)
        year_row = year_result.fetchone()
        year_orders = int(year_row.orders or 0)
        year_amount = float(year_row.amount or 0)
        
        # 设备统计
        device_query = select(
            func.count(Device.id).label("total"),
            func.sum(case((Device.status == "normal", 1), else_=0)).label("normal"),
            func.sum(case((Device.status == "maintenance", 1), else_=0)).label("maintenance"),
            func.sum(case((Device.status == "offline", 1), else_=0)).label("offline")
        )
        device_result = await self.db.execute(device_query)
        device_row = device_result.fetchone()
        
        total_devices = int(device_row.total or 0)
        normal_devices = int(device_row.normal or 0)
        maintenance_devices = int(device_row.maintenance or 0)
        offline_devices = int(device_row.offline or 0)
        online_devices = normal_devices + maintenance_devices
        
        # 用户统计
        user_query = select(func.count(User.id)).label("total")
        user_result = await self.db.execute(user_query)
        total_users = int(user_result.scalar() or 0)
        
        # 今日新用户
        today_new_users_query = select(func.count(User.id)).where(
            User.register_date == today
        )
        today_new_users_result = await self.db.execute(today_new_users_query)
        today_new_users = int(today_new_users_result.scalar() or 0)
        
        return {
            "today": {
                "amount": round(today_amount, 2),
                "orders": today_orders
            },
            "month": {
                "amount": round(month_amount, 2),
                "orders": month_orders
            },
            "year": {
                "amount": round(year_amount, 2),
                "orders": year_orders
            },
            "devices": {
                "total": total_devices,
                "online": online_devices,
                "offline": offline_devices,
                "normal": normal_devices,
                "maintenance": maintenance_devices,
                "online_rate": round(online_devices / total_devices * 100, 2) if total_devices > 0 else 0
            },
            "users": {
                "total": total_users,
                "today_new": today_new_users
            }
        }
    
    async def get_realtime_sales_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取实时销售趋势（最近N小时）
        """
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        query = select(
            func.strftime("%Y-%m-%d %H:00", Order.order_time).label("time_slot"),
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= start_time
            )
        ).group_by(func.strftime("%Y-%m-%d %H:00", Order.order_time)).order_by("time_slot")
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        trend_data = []
        for row in rows:
            trend_data.append({
                "time_slot": str(row.time_slot) if row.time_slot else "",
                "orders": int(row.orders or 0),
                "amount": round(float(row.amount or 0), 2)
            })
        
        return trend_data
    
    async def get_top_devices(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        获取Top N设备（按今日销售额）
        """
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        query = select(
            Device.id,
            Device.device_code,
            Device.device_name,
            Device.location,
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).join(Device, Order.device_id == Device.id).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= today_start,
                Order.order_time <= today_end
            )
        ).group_by(Device.id).order_by(desc("amount")).limit(top_n)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        top_devices = []
        for row in rows:
            top_devices.append({
                "id": row.id,
                "device_code": row.device_code,
                "device_name": row.device_name,
                "location": row.location,
                "orders": int(row.orders or 0),
                "amount": round(float(row.amount or 0), 2)
            })
        
        return top_devices
    
    async def get_top_products(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        获取Top N热销商品（今日）
        """
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        query = select(
            Product.id,
            Product.product_name,
            Product.category,
            func.sum(OrderItem.quantity).label("quantity"),
            func.sum(OrderItem.subtotal).label("amount")
        ).join(OrderItem, Product.id == OrderItem.product_id).join(Order, OrderItem.order_id == Order.id).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= today_start,
                Order.order_time <= today_end
            )
        ).group_by(Product.id).order_by(desc("quantity")).limit(top_n)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        top_products = []
        for row in rows:
            top_products.append({
                "id": row.id,
                "product_name": row.product_name,
                "category": row.category,
                "quantity": int(row.quantity or 0),
                "amount": round(float(row.amount or 0), 2)
            })
        
        return top_products
    
    async def get_payment_distribution(self) -> List[Dict[str, Any]]:
        """
        获取今日支付方式分布
        """
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        query = select(
            Order.pay_method,
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= today_start,
                Order.order_time <= today_end
            )
        ).group_by(Order.pay_method)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        method_names = {
            "wechat": "微信支付",
            "alipay": "支付宝",
            "cash": "现金支付"
        }
        
        payment_data = []
        total_amount = 0
        
        for row in rows:
            amount = float(row.amount or 0)
            total_amount += amount
            payment_data.append({
                "method": row.pay_method,
                "method_name": method_names.get(row.pay_method, row.pay_method),
                "orders": int(row.orders or 0),
                "amount": round(amount, 2)
            })
        
        # 计算占比
        for item in payment_data:
            item["percentage"] = round(item["amount"] / total_amount * 100, 2) if total_amount > 0 else 0
        
        return payment_data
    
    async def get_alert_data(self) -> Dict[str, Any]:
        """
        获取告警数据（设备离线、库存不足、待处理维护）
        """
        # 离线设备
        offline_query = select(
            Device.id,
            Device.device_code,
            Device.device_name,
            Device.location
        ).where(Device.status == "offline")
        
        offline_result = await self.db.execute(offline_query)
        offline_rows = offline_result.fetchall()
        
        offline_devices = []
        for row in offline_rows:
            offline_devices.append({
                "id": row.id,
                "device_code": row.device_code,
                "device_name": row.device_name,
                "location": row.location
            })
        
        # 待处理维护
        pending_maintenance_query = select(
            Maintenance.id,
            Maintenance.title,
            Maintenance.maintenance_type,
            Device.device_name,
            Device.location
        ).join(Device, Maintenance.device_id == Device.id).where(
            Maintenance.status.in_(["pending", "processing"])
        ).order_by(Maintenance.report_time.desc())
        
        pending_maintenance_result = await self.db.execute(pending_maintenance_query)
        pending_maintenance_rows = pending_maintenance_result.fetchall()
        
        pending_maintenances = []
        for row in pending_maintenance_rows:
            pending_maintenances.append({
                "id": row.id,
                "title": row.title,
                "type": row.maintenance_type,
                "device_name": row.device_name,
                "location": row.location
            })
        
        return {
            "offline_devices": {
                "count": len(offline_devices),
                "list": offline_devices[:5]  # 只返回前5个
            },
            "pending_maintenances": {
                "count": len(pending_maintenances),
                "list": pending_maintenances[:5]  # 只返回前5个
            }
        }
    
    async def get_hourly_sales_today(self) -> List[Dict[str, Any]]:
        """
        获取今日每小时销售数据
        """
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        query = select(
            func.strftime("%H", Order.order_time).label("hour"),
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= today_start,
                Order.order_time <= today_end
            )
        ).group_by(func.strftime("%H", Order.order_time)).order_by("hour")
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # 创建24小时的完整数据
        hourly_data = []
        hour_map = {int(row.hour): {
            "orders": int(row.orders or 0),
            "amount": float(row.amount or 0)
        } for row in rows}
        
        for hour in range(24):
            data = hour_map.get(hour, {"orders": 0, "amount": 0})
            hourly_data.append({
                "hour": hour,
                "hour_label": f"{hour:02d}:00",
                "orders": data["orders"],
                "amount": round(data["amount"], 2)
            })
        
        return hourly_data
