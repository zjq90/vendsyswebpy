"""
自动售后机数据统计与分析系统 - 设备效能分析服务
提供单机产出、故障率统计、运维成本分析
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.orm import selectinload

from app.models.models import Device, Order, Maintenance, Inventory


class DevicesService:
    """设备效能分析服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_devices_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取设备效能分析
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param status: 设备状态过滤
        :return: 设备效能列表
        """
        # 默认查询最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 先获取所有设备
        device_query = select(Device)
        if status:
            device_query = device_query.where(Device.status == status)
        
        device_result = await self.db.execute(device_query)
        devices = device_result.scalars().all()
        
        devices_data = []
        
        for device in devices:
            # 查询设备的销售数据
            sales_query = select(
                func.count(Order.id).label("total_orders"),
                func.sum(Order.pay_amount).label("total_amount")
            ).where(
                and_(
                    Order.device_id == device.id,
                    Order.pay_status == "success",
                    Order.order_time >= start_datetime,
                    Order.order_time <= end_datetime
                )
            )
            
            sales_result = await self.db.execute(sales_query)
            sales_row = sales_result.fetchone()
            
            total_orders = int(sales_row.total_orders or 0)
            total_amount = float(sales_row.total_amount or 0)
            
            # 查询故障记录
            fault_query = select(
                func.count(Maintenance.id).label("fault_count"),
                func.sum(Maintenance.cost).label("maintenance_cost")
            ).where(
                and_(
                    Maintenance.device_id == device.id,
                    Maintenance.maintenance_type == "fault",
                    Maintenance.report_time >= start_datetime,
                    Maintenance.report_time <= end_datetime
                )
            )
            
            fault_result = await self.db.execute(fault_query)
            fault_row = fault_result.fetchone()
            
            fault_count = int(fault_row.fault_count or 0)
            maintenance_cost = float(fault_row.maintenance_cost or 0)
            
            # 计算日均销售额
            days_diff = (end_date - start_date).days + 1
            avg_daily_amount = total_amount / days_diff if days_diff > 0 else 0
            
            # 计算设备使用天数（从安装日期或统计开始日期）
            if device.install_date:
                install_date = device.install_date
                device_age_days = max((date.today() - install_date).days, 1)
            else:
                device_age_days = days_diff
            
            # 计算故障率（故障次数 / 运行天数）
            fault_rate = (fault_count / device_age_days) * 100 if device_age_days > 0 else 0
            
            devices_data.append({
                "id": device.id,
                "device_code": device.device_code,
                "device_name": device.device_name,
                "location": device.location,
                "status": device.status,
                "status_text": self._get_status_text(device.status),
                "capacity": device.capacity,
                "slot_count": device.slot_count,
                "install_date": str(device.install_date) if device.install_date else None,
                "last_maintenance_date": str(device.last_maintenance_date) if device.last_maintenance_date else None,
                "total_orders": total_orders,
                "order_count": total_orders,
                "total_amount": round(total_amount, 2),
                "total_sales": round(total_amount, 2),
                "avg_daily_amount": round(avg_daily_amount, 2),
                "fault_count": fault_count,
                "maintenance_cost": round(maintenance_cost, 2),
                "fault_rate": round(fault_rate, 2),
                "device_age_days": device_age_days
            })
        
        # 按销售额降序排序
        devices_data.sort(key=lambda x: x["total_amount"], reverse=True)
        
        return devices_data
    
    def _get_status_text(self, status: str) -> str:
        """获取设备状态文本"""
        status_map = {
            "normal": "正常运行",
            "maintenance": "维护中",
            "offline": "离线"
        }
        return status_map.get(status, "未知")
    
    async def get_devices_overview(self) -> Dict[str, Any]:
        """
        获取设备概览统计
        """
        total_query = select(func.count(Device.id)).where(True)
        total_result = await self.db.execute(total_query)
        total_devices = total_result.scalar() or 0
        
        status_query = select(
            Device.status,
            func.count(Device.id).label("count")
        ).group_by(Device.status)
        
        status_result = await self.db.execute(status_query)
        status_rows = status_result.fetchall()
        
        status_stats = {}
        for row in status_rows:
            status_stats[row.status] = row.count
        
        online_devices = status_stats.get("online", 0) + status_stats.get("normal", 0)
        offline_devices = status_stats.get("offline", 0)
        maintenance_devices = status_stats.get("maintenance", 0)
        fault_devices = status_stats.get("fault", 0)
        
        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "online_count": online_devices,
            "offline_devices": offline_devices,
            "offline_count": offline_devices,
            "normal_devices": status_stats.get("normal", 0) + status_stats.get("online", 0),
            "maintenance_devices": maintenance_devices,
            "maintenance_count": maintenance_devices,
            "fault_count": fault_devices,
            "online_rate": round(online_devices / total_devices * 100, 2) if total_devices > 0 else 0
        }
    
    async def get_maintenance_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取运维分析
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 运维分析数据
        """
        # 默认查询最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 按类型统计运维记录
        type_query = select(
            Maintenance.maintenance_type,
            func.count(Maintenance.id).label("count"),
            func.sum(Maintenance.cost).label("total_cost"),
            func.avg(Maintenance.duration_minutes).label("avg_duration")
        ).where(
            and_(
                Maintenance.report_time >= start_datetime,
                Maintenance.report_time <= end_datetime
            )
        ).group_by(Maintenance.maintenance_type)
        
        type_result = await self.db.execute(type_query)
        type_rows = type_result.fetchall()
        
        type_analysis = []
        type_names = {
            "fault": "故障维修",
            "routine": "例行维护",
            "repair": "设备维修",
            "upgrade": "设备升级"
        }
        
        total_maintenances = 0
        total_cost = 0
        total_duration = 0
        
        duration_query = select(
            func.sum(Maintenance.duration_minutes).label("total_duration")
        ).where(
            and_(
                Maintenance.report_time >= start_datetime,
                Maintenance.report_time <= end_datetime
            )
        )
        duration_result = await self.db.execute(duration_query)
        duration_row = duration_result.fetchone()
        total_duration = int(duration_row.total_duration or 0)
        
        for row in type_rows:
            count = int(row.count or 0)
            cost = float(row.total_cost or 0)
            avg_duration = float(row.avg_duration or 0)
            
            total_maintenances += count
            total_cost += cost
            
            type_analysis.append({
                "type": row.maintenance_type,
                "type_name": type_names.get(row.maintenance_type, row.maintenance_type),
                "count": count,
                "total_cost": round(cost, 2),
                "avg_duration": round(avg_duration, 2),
                "cost_per_hour": round(cost / (avg_duration / 60), 2) if avg_duration > 0 else 0
            })
        
        device_fault_query = select(
            Maintenance.device_id,
            Device.device_name,
            Device.location,
            func.count(Maintenance.id).label("fault_count"),
            func.sum(Maintenance.cost).label("fault_cost")
        ).join(Device, Maintenance.device_id == Device.id).where(
            and_(
                Maintenance.maintenance_type == "fault",
                Maintenance.report_time >= start_datetime,
                Maintenance.report_time <= end_datetime
            )
        ).group_by(Maintenance.device_id).order_by(desc("fault_count")).limit(10)
        
        device_fault_result = await self.db.execute(device_fault_query)
        device_fault_rows = device_fault_result.fetchall()
        
        device_fault_list = []
        for row in device_fault_rows:
            device_fault_list.append({
                "device_id": row.device_id,
                "device_name": row.device_name,
                "location": row.location,
                "fault_count": int(row.fault_count or 0),
                "fault_cost": round(float(row.fault_cost or 0), 2)
            })
        
        status_query = select(
            Maintenance.status,
            func.count(Maintenance.id).label("count")
        ).where(
            and_(
                Maintenance.report_time >= start_datetime,
                Maintenance.report_time <= end_datetime
            )
        ).group_by(Maintenance.status)
        
        status_result = await self.db.execute(status_query)
        status_rows = status_result.fetchall()
        
        status_stats = {}
        status_names = {
            "pending": "待处理",
            "processing": "处理中",
            "completed": "已完成",
            "cancelled": "已取消"
        }
        
        for row in status_rows:
            status_stats[status_names.get(row.status, row.status)] = int(row.count or 0)
        
        avg_cost = round(total_cost / total_maintenances, 2) if total_maintenances > 0 else 0
        
        return {
            "total_cost": round(total_cost, 2),
            "avg_cost": avg_cost,
            "total_duration": total_duration,
            "summary": {
                "total_maintenances": total_maintenances,
                "total_cost": round(total_cost, 2),
                "avg_cost_per_maintenance": avg_cost
            },
            "type_analysis": type_analysis,
            "top_fault_devices": device_fault_list,
            "status_stats": status_stats,
            "start_date": str(start_date),
            "end_date": str(end_date)
        }
    
    async def get_low_stock_devices(self, min_threshold: int = 3) -> List[Dict[str, Any]]:
        """
        获取库存不足的设备
        :param min_threshold: 最低库存阈值
        :return: 库存不足设备列表
        """
        query = select(
            Inventory.device_id,
            Inventory.product_id,
            Inventory.current_quantity,
            Inventory.min_quantity,
            Inventory.max_quantity,
            Inventory.slot_number,
            Device.device_name,
            Device.location,
            Device.device_code,
            Device.status,
            Product.product_name,
            Product.product_code
        ).join(Device, Inventory.device_id == Device.id).join(Product, Inventory.product_id == Product.id).where(
            and_(
                Inventory.current_quantity <= Inventory.min_quantity,
                Inventory.current_quantity <= min_threshold
            )
        ).order_by(Inventory.current_quantity.asc())
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        low_stock_list = []
        for row in rows:
            low_stock_list.append({
                "device_id": row.device_id,
                "device_code": row.device_code,
                "device_name": row.device_name,
                "location": row.location,
                "device_location": row.location,
                "device_status": row.device_status,
                "product_id": row.product_id,
                "product_code": row.product_code,
                "product_name": row.product_name,
                "slot_number": row.slot_number,
                "current_quantity": row.current_quantity,
                "current_stock": row.current_quantity,
                "min_quantity": row.min_quantity,
                "max_quantity": row.max_quantity,
                "max_stock": row.max_quantity if row.max_quantity else 100,
                "is_critical": row.current_quantity == 0
            })
        
        return low_stock_list
    
    async def get_devices_list(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取设备列表（支持分页和过滤）
        """
        query = select(Device)
        
        if status:
            query = query.where(Device.status == status)
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    Device.device_name.like(keyword_pattern),
                    Device.device_code.like(keyword_pattern),
                    Device.location.like(keyword_pattern)
                )
            )
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.order_by(desc(Device.created_at)).offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        devices = result.scalars().all()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=29)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        device_list = []
        for device in devices:
            sales_query = select(
                func.count(Order.id).label("total_orders"),
                func.sum(Order.pay_amount).label("total_amount")
            ).where(
                and_(
                    Order.device_id == device.id,
                    Order.pay_status == "success",
                    Order.order_time >= start_datetime,
                    Order.order_time <= end_datetime
                )
            )
            
            sales_result = await self.db.execute(sales_query)
            sales_row = sales_result.fetchone()
            
            total_orders = int(sales_row.total_orders or 0)
            total_amount = float(sales_row.total_amount or 0)
            
            device_list.append({
                "id": device.id,
                "device_code": device.device_code,
                "device_name": device.device_name,
                "location": device.location,
                "status": device.status,
                "status_text": self._get_status_text(device.status),
                "capacity": device.capacity,
                "slot_count": device.slot_count,
                "install_date": str(device.install_date) if device.install_date else None,
                "last_maintenance_date": str(device.last_maintenance_date) if device.last_maintenance_date else None,
                "last_online_at": str(device.last_maintenance_date) if device.last_maintenance_date else None,
                "total_orders": total_orders,
                "order_count": total_orders,
                "total_amount": round(total_amount, 2),
                "total_sales": round(total_amount, 2),
                "created_at": str(device.created_at) if device.created_at else None,
                "updated_at": str(device.updated_at) if device.updated_at else None
            })
        
        return {
            "data": device_list,
            "items": device_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
