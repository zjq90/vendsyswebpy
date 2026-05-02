"""
自动售后机数据统计与分析系统 - 销售报表服务
提供日/周/月/年维度的销售额、订单量、客单价统计
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.models import Order, OrderItem, Device, User


class SalesService:
    """销售报表服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_sales_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取销售汇总统计
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 销售汇总数据
        """
        query = select(
            func.count(Order.id).label("total_orders"),
            func.sum(Order.pay_amount).label("total_amount"),
            func.sum(Order.total_quantity).label("total_quantity")
        ).where(Order.pay_status == "success")
        
        # 添加日期过滤
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.where(Order.order_time >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where(Order.order_time <= end_datetime)
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        total_orders = row.total_orders or 0
        total_amount = float(row.total_amount or 0)
        total_quantity = row.total_quantity or 0
        
        # 计算客单价
        avg_order_value = total_amount / total_orders if total_orders > 0 else 0
        
        return {
            "total_sales": round(total_amount, 2),
            "total_orders": total_orders,
            "total_quantity": total_quantity,
            "avg_order_value": round(avg_order_value, 2)
        }
    
    async def get_daily_sales(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        device_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取日销售数据
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param device_id: 设备ID（可选，用于按设备过滤）
        :return: 日销售数据列表
        """
        # 默认查询最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)
        
        # 构建查询条件
        conditions = [Order.pay_status == "success"]
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        conditions.append(and_(Order.order_time >= start_datetime, Order.order_time <= end_datetime))
        
        if device_id:
            conditions.append(Order.device_id == device_id)
        
        query = select(
            func.date(Order.order_time).label("date"),
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount"),
            func.sum(Order.total_quantity).label("quantity")
        ).where(and_(*conditions)).group_by(func.date(Order.order_time)).order_by(func.date(Order.order_time))
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        daily_data = []
        for row in rows:
            daily_data.append({
                "date": str(row.date) if row.date else "",
                "order_count": row.orders or 0,
                "total_sales": round(float(row.amount or 0), 2),
                "quantity": row.quantity or 0
            })
        
        return daily_data
    
    async def get_weekly_sales(
        self,
        year: Optional[int] = None,
        device_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取周销售数据
        :param year: 年份
        :param device_id: 设备ID
        :return: 周销售数据列表
        """
        if not year:
            year = date.today().year
        
        conditions = [
            Order.pay_status == "success",
            func.strftime("%Y", Order.order_time) == str(year)
        ]
        
        if device_id:
            conditions.append(Order.device_id == device_id)
        
        query = select(
            func.strftime("%W", Order.order_time).label("week"),
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(and_(*conditions)).group_by(func.strftime("%W", Order.order_time)).order_by(func.strftime("%W", Order.order_time))
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        weekly_data = []
        for row in rows:
            week_num = int(row.week) if row.week else 0
            weekly_data.append({
                "year": year,
                "week": week_num + 1,
                "order_count": row.orders or 0,
                "total_sales": round(float(row.amount or 0), 2)
            })
        
        return weekly_data
    
    async def get_monthly_sales(
        self,
        year: Optional[int] = None,
        device_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取月销售数据
        :param year: 年份
        :param device_id: 设备ID
        :return: 月销售数据列表
        """
        if not year:
            year = date.today().year
        
        conditions = [
            Order.pay_status == "success",
            func.strftime("%Y", Order.order_time) == str(year)
        ]
        
        if device_id:
            conditions.append(Order.device_id == device_id)
        
        query = select(
            func.strftime("%m", Order.order_time).label("month"),
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(and_(*conditions)).group_by(func.strftime("%m", Order.order_time)).order_by(func.strftime("%m", Order.order_time))
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        monthly_data = []
        month_names = ["", "一月", "二月", "三月", "四月", "五月", "六月", 
                       "七月", "八月", "九月", "十月", "十一月", "十二月"]
        
        for row in rows:
            month_num = int(row.month) if row.month else 0
            monthly_data.append({
                "year": year,
                "month": month_num,
                "month_name": month_names[month_num] if 1 <= month_num <= 12 else row.month,
                "order_count": row.orders or 0,
                "total_sales": round(float(row.amount or 0), 2)
            })
        
        return monthly_data
    
    async def get_yearly_sales(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        device_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取年销售数据
        :param start_year: 开始年份
        :param end_year: 结束年份
        :param device_id: 设备ID
        :return: 年销售数据列表
        """
        current_year = date.today().year
        if not end_year:
            end_year = current_year
        if not start_year:
            start_year = end_year - 4  # 默认显示最近5年
        
        conditions = [
            Order.pay_status == "success",
            func.strftime("%Y", Order.order_time).between(str(start_year), str(end_year))
        ]
        
        if device_id:
            conditions.append(Order.device_id == device_id)
        
        query = select(
            func.strftime("%Y", Order.order_time).label("year"),
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(and_(*conditions)).group_by(func.strftime("%Y", Order.order_time)).order_by(func.strftime("%Y", Order.order_time))
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        yearly_data = []
        for row in rows:
            yearly_data.append({
                "year": int(row.year) if row.year else 0,
                "order_count": row.orders or 0,
                "total_sales": round(float(row.amount or 0), 2)
            })
        
        return yearly_data
    
    async def get_sales_by_payment_method(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        按支付方式统计销售
        """
        conditions = [Order.pay_status == "success"]
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            conditions.append(Order.order_time >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(Order.order_time <= end_datetime)
        
        query = select(
            Order.pay_method,
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).where(and_(*conditions)).group_by(Order.pay_method)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        method_names = {
            "wechat": "微信支付",
            "alipay": "支付宝",
            "cash": "现金支付",
            "card": "银行卡",
            "other": "其他"
        }
        
        payment_data = []
        for row in rows:
            payment_data.append({
                "payment_method": row.pay_method,
                "payment_method_name": method_names.get(row.pay_method, row.pay_method),
                "order_count": row.orders or 0,
                "total_sales": round(float(row.amount or 0), 2)
            })
        
        return payment_data
    
    async def get_sales_by_device(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        按设备统计销售（Top N）
        """
        conditions = [Order.pay_status == "success"]
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            conditions.append(Order.order_time >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(Order.order_time <= end_datetime)
        
        query = select(
            Order.device_id,
            Device.device_name,
            Device.location,
            func.count(Order.id).label("orders"),
            func.sum(Order.pay_amount).label("amount")
        ).join(Device, Order.device_id == Device.id).where(and_(*conditions)).group_by(Order.device_id).order_by(func.sum(Order.pay_amount).desc()).limit(top_n)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        device_data = []
        for row in rows:
            device_data.append({
                "device_id": row.device_id,
                "device_name": row.device_name,
                "location": row.location,
                "order_count": row.orders or 0,
                "total_sales": round(float(row.amount or 0), 2)
            })
        
        return device_data
    
    async def get_order_list(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        device_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取订单列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param device_id: 设备ID
        :param page: 页码
        :param page_size: 每页大小
        :return: 订单列表和分页信息
        """
        conditions = [Order.pay_status == "success"]
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            conditions.append(Order.order_time >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(Order.order_time <= end_datetime)
        if device_id:
            conditions.append(Order.device_id == device_id)
        
        count_query = select(func.count(Order.id)).where(and_(*conditions))
        result = await self.db.execute(count_query)
        total_count = result.scalar() or 0
        
        query = select(
            Order.id,
            Order.order_no,
            Order.order_time,
            Order.pay_amount,
            Order.pay_method,
            Order.pay_status,
            Order.total_quantity,
            Device.device_name,
            Device.location,
            User.nickname.label("user_name")
        ).join(Device, Order.device_id == Device.id).join(User, Order.user_id == User.id).where(and_(*conditions)).order_by(Order.order_time.desc()).offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        status_map = {
            "success": "completed",
            "paid": "completed",
            "pending": "pending",
            "failed": "cancelled",
            "refund": "refunded"
        }
        
        order_list = []
        for row in rows:
            order_list.append({
                "order_id": row.id,
                "order_no": row.order_no,
                "order_time": row.order_time.strftime("%Y-%m-%d %H:%M:%S") if row.order_time else "",
                "created_at": row.order_time.strftime("%Y-%m-%d %H:%M:%S") if row.order_time else "",
                "total_amount": round(float(row.pay_amount or 0), 2),
                "pay_amount": round(float(row.pay_amount or 0), 2),
                "payment_method": row.pay_method,
                "pay_method": row.pay_method,
                "quantity": row.total_quantity or 0,
                "device_name": row.device_name,
                "location": row.location,
                "user_name": row.user_name,
                "user_nickname": row.user_name,
                "status": status_map.get(row.pay_status, row.pay_status)
            })
        
        return {
            "items": order_list,
            "list": order_list,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 0
        }
