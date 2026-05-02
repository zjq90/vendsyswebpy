"""
自动售后机数据统计与分析系统 - 用户行为分析服务
提供活跃用户数、复购率、新用户增长趋势、购买时段分布
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, distinct
from sqlalchemy.orm import selectinload

from app.models.models import User, Order, OrderItem, Product


class UsersService:
    """用户行为分析服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_behavior_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取用户行为分析
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 用户行为分析数据
        """
        # 默认查询最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 统计总用户数
        total_users_query = select(func.count(User.id))
        total_users_result = await self.db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0
        
        # 统计新用户数（在此期间注册）
        new_users_query = select(func.count(User.id)).where(
            and_(
                User.register_date >= start_date,
                User.register_date <= end_date
            )
        )
        new_users_result = await self.db.execute(new_users_query)
        new_users = new_users_result.scalar() or 0
        
        # 统计活跃用户数（在此期间有购买行为）
        active_users_query = select(func.count(distinct(Order.user_id))).where(
            and_(
                Order.user_id.isnot(None),
                Order.pay_status == "success",
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        )
        active_users_result = await self.db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0
        
        # 统计复购用户（在此期间购买次数 >= 2）
        repeat_users_query = select(
            Order.user_id,
            func.count(Order.id).label("order_count")
        ).where(
            and_(
                Order.user_id.isnot(None),
                Order.pay_status == "success",
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        ).group_by(Order.user_id).having(func.count(Order.id) >= 2)
        
        repeat_users_result = await self.db.execute(repeat_users_query)
        repeat_users_rows = repeat_users_result.fetchall()
        repeat_purchase_users = len(repeat_users_rows)
        
        # 计算复购率
        repeat_purchase_rate = (
            (repeat_purchase_users / active_users * 100)
            if active_users > 0 else 0
        )
        
        # 统计平均购买次数和客单价
        user_orders_query = select(
            Order.user_id,
            func.count(Order.id).label("order_count"),
            func.sum(Order.pay_amount).label("total_amount")
        ).where(
            and_(
                Order.user_id.isnot(None),
                Order.pay_status == "success",
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        ).group_by(Order.user_id)
        
        user_orders_result = await self.db.execute(user_orders_query)
        user_orders_rows = user_orders_result.fetchall()
        
        total_orders_in_period = 0
        total_amount_in_period = 0
        
        for row in user_orders_rows:
            total_orders_in_period += int(row.order_count or 0)
            total_amount_in_period += float(row.total_amount or 0)
        
        # 平均购买次数
        avg_purchase_count = (
            total_orders_in_period / active_users
            if active_users > 0 else 0
        )
        
        # 客单价
        avg_order_value = (
            total_amount_in_period / total_orders_in_period
            if total_orders_in_period > 0 else 0
        )
        
        return {
            "period": f"{start_date} 至 {end_date}",
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_users": total_users,
            "active_users": active_users,
            "new_users": new_users,
            "repeat_purchase_users": repeat_purchase_users,
            "repeat_purchase_rate": round(repeat_purchase_rate, 2),
            "repeat_rate": round(repeat_purchase_rate, 2),
            "avg_purchase_count": round(avg_purchase_count, 2),
            "avg_order_value": round(avg_order_value, 2),
            "total_orders_in_period": total_orders_in_period,
            "total_amount_in_period": round(total_amount_in_period, 2)
        }
    
    async def get_new_users_growth(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period_type: str = "day"  # day, week, month
    ) -> List[Dict[str, Any]]:
        """
        获取新用户增长趋势
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param period_type: 周期类型：day-按日, week-按周, month-按月
        :return: 新用户增长数据列表
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            if period_type == "month":
                start_date = end_date - timedelta(days=364)  # 近12个月
            elif period_type == "week":
                start_date = end_date - timedelta(days=83)  # 近12周
            else:
                start_date = end_date - timedelta(days=29)  # 近30天
        
        # 按不同周期查询
        if period_type == "month":
            # 按月统计
            query = select(
                func.strftime("%Y-%m", User.register_date).label("period"),
                func.count(User.id).label("new_users")
            ).where(
                and_(
                    User.register_date >= start_date,
                    User.register_date <= end_date
                )
            ).group_by(func.strftime("%Y-%m", User.register_date)).order_by("period")
        elif period_type == "week":
            # 按周统计
            query = select(
                func.strftime("%Y-%W", User.register_date).label("period"),
                func.count(User.id).label("new_users")
            ).where(
                and_(
                    User.register_date >= start_date,
                    User.register_date <= end_date
                )
            ).group_by(func.strftime("%Y-%W", User.register_date)).order_by("period")
        else:
            # 按日统计
            query = select(
                func.date(User.register_date).label("period"),
                func.count(User.id).label("new_users")
            ).where(
                and_(
                    User.register_date >= start_date,
                    User.register_date <= end_date
                )
            ).group_by(func.date(User.register_date)).order_by("period")
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        growth_data = []
        for row in rows:
            growth_data.append({
                "period": str(row.period) if row.period else "",
                "date": str(row.period) if row.period else "",
                "new_users": int(row.new_users or 0)
            })
        
        return growth_data
    
    async def get_purchase_time_distribution(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        获取购买时段分布热力图数据
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 24小时购买时段数据
        """
        # 默认查询最近7天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=6)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 按小时统计订单数和销售额
        query = select(
            func.strftime("%H", Order.order_time).label("hour"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        ).group_by(func.strftime("%H", Order.order_time)).order_by("hour")
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # 创建24小时的完整数据
        time_distribution = []
        hour_data = {int(row.hour): {
            "order_count": int(row.order_count or 0),
            "amount": float(row.amount or 0)
        } for row in rows}
        
        for hour in range(24):
            data = hour_data.get(hour, {"order_count": 0, "amount": 0})
            time_distribution.append({
                "hour": hour,
                "hour_label": f"{hour:02d}:00",
                "order_count": data["order_count"],
                "amount": round(data["amount"], 2)
            })
        
        # 计算最大订单数用于热力图颜色
        max_orders = max([d["order_count"] for d in time_distribution]) if time_distribution else 1
        
        # 添加热力图强度值
        for d in time_distribution:
            d["intensity"] = round(d["order_count"] / max_orders * 100, 2) if max_orders > 0 else 0
        
        return time_distribution
    
    async def get_weekday_distribution(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        获取按星期几的购买分布
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # SQLite中使用strftime('%w', date)获取星期几，0=周日, 1=周一...
        query = select(
            func.strftime("%w", Order.order_time).label("weekday"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.pay_amount).label("amount")
        ).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        ).group_by(func.strftime("%w", Order.order_time))
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        weekday_names = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        weekday_data = {}
        
        for row in rows:
            weekday = int(row.weekday) if row.weekday else 0
            weekday_data[weekday] = {
                "order_count": int(row.order_count or 0),
                "amount": float(row.amount or 0)
            }
        
        # 构建完整的星期数据
        # SQLite: 0=周日, 1=周一...6=周六
        # 前端期望: 1=周一, 2=周二...6=周六, 7=周日
        distribution = []
        for i in range(7):
            # i是SQLite的weekday (0=周日)
            data = weekday_data.get(i, {"order_count": 0, "amount": 0})
            # 转换为前端期望的weekday: 0->7, 1->1, 2->2...6->6
            frontend_weekday = 7 if i == 0 else i
            distribution.append({
                "weekday": i,
                "weekday_name": weekday_names[i],
                "order_count": data["order_count"],
                "amount": round(data["amount"], 2),
                "total_sales": round(data["amount"], 2)
            })
        
        return distribution
    
    async def get_top_users(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 20,
        sort_by: str = "amount"  # amount, orders
    ) -> List[Dict[str, Any]]:
        """
        获取消费排行用户
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        query = select(
            User.id,
            User.user_code,
            User.nickname,
            User.phone,
            User.user_type,
            func.count(Order.id).label("order_count"),
            func.sum(Order.pay_amount).label("total_amount"),
            func.max(Order.order_time).label("last_order_time")
        ).join(Order, User.id == Order.user_id).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        ).group_by(User.id)
        
        # 排序
        if sort_by == "orders":
            query = query.order_by(desc("order_count"))
        else:
            query = query.order_by(desc("total_amount"))
        
        query = query.limit(top_n)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        top_users = []
        user_type_names = {"normal": "普通用户", "member": "会员", "registered": "注册用户", "guest": "游客", "vip": "VIP用户"}
        
        for row in rows:
            total_amount = round(float(row.total_amount or 0), 2)
            top_users.append({
                "id": row.id,
                "user_code": row.user_code,
                "nickname": row.nickname,
                "phone": row.phone,
                "user_type": row.user_type,
                "user_type_name": user_type_names.get(row.user_type, "未知"),
                "order_count": int(row.order_count or 0),
                "total_amount": total_amount,
                "total_spent": total_amount,
                "last_order_time": str(row.last_order_time) if row.last_order_time else None
            })
        
        return top_users
    
    async def get_users_list(
        self,
        page: int = 1,
        page_size: int = 10,
        user_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户列表（支持分页和过滤）
        """
        query = select(User)
        
        # 添加过滤条件
        if user_type:
            query = query.where(User.user_type == user_type)
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    User.nickname.like(keyword_pattern),
                    User.phone.like(keyword_pattern),
                    User.user_code.like(keyword_pattern)
                )
            )
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页查询
        query = query.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        user_list = []
        user_type_names = {"normal": "普通用户", "member": "会员", "registered": "注册用户", "guest": "游客", "vip": "VIP用户"}
        
        for user in users:
            total_amount = round(float(user.total_amount or 0), 2)
            total_orders = user.total_orders or 0
            user_list.append({
                "id": user.id,
                "user_code": user.user_code,
                "phone": user.phone,
                "nickname": user.nickname,
                "user_type": user.user_type,
                "user_type_name": user_type_names.get(user.user_type, "未知"),
                "total_orders": total_orders,
                "order_count": total_orders,
                "total_amount": total_amount,
                "total_spent": total_amount,
                "register_date": str(user.register_date) if user.register_date else None,
                "last_purchase_time": str(user.last_purchase_time) if user.last_purchase_time else None,
                "last_purchase_at": str(user.last_purchase_time) if user.last_purchase_time else None,
                "created_at": str(user.created_at) if user.created_at else None,
                "updated_at": str(user.updated_at) if user.updated_at else None
            })
        
        return {
            "data": user_list,
            "items": user_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
