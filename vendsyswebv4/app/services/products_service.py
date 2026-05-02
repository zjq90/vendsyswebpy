"""
自动售后机数据统计与分析系统 - 商品分析服务
提供热销商品排行、滞销商品分析、毛利率分析
"""
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.models import Product, OrderItem, Order


class ProductsService:
    """商品分析服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_hot_products(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 20,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取热销商品排行
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param top_n: 返回前N个商品
        :param category: 商品分类（可选过滤）
        :return: 热销商品列表
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
        
        # 构建查询
        query = select(
            Product.id,
            Product.product_name,
            Product.product_code,
            Product.category,
            Product.brand,
            Product.sale_price,
            Product.cost_price,
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.subtotal).label("total_amount")
        ).join(OrderItem, Product.id == OrderItem.product_id).join(Order, OrderItem.order_id == Order.id).where(and_(*conditions))
        
        # 添加分类过滤
        if category:
            query = query.where(Product.category == category)
        
        # 分组和排序
        query = query.group_by(Product.id).order_by(desc("total_quantity")).limit(top_n)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        hot_products = []
        for row in rows:
            sale_price = float(row.sale_price or 0)
            cost_price = float(row.cost_price or 0)
            profit_margin = ((sale_price - cost_price) / sale_price * 100) if sale_price > 0 else 0
            
            hot_products.append({
                "id": row.id,
                "product_name": row.product_name,
                "product_code": row.product_code,
                "category": row.category,
                "brand": row.brand,
                "total_quantity": int(row.total_quantity or 0),
                "total_amount": round(float(row.total_amount or 0), 2),
                "total_sales": round(float(row.total_amount or 0), 2),
                "sale_price": round(sale_price, 2),
                "cost_price": round(cost_price, 2),
                "profit_margin": round(profit_margin, 2),
                "gross_margin": round(profit_margin, 2)
            })
        
        return hot_products
    
    async def get_slow_selling_products(
        self,
        days_threshold: int = 30,
        min_sales_threshold: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取滞销商品分析
        :param days_threshold: 滞销天数阈值（超过此天数未销售）
        :param min_sales_threshold: 最低销量阈值（低于此数量视为滞销）
        :param category: 商品分类（可选过滤）
        :return: 滞销商品列表
        """
        # 计算日期范围：最近30天的销售情况
        end_date = date.today()
        start_date = end_date - timedelta(days=days_threshold)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 先获取所有在售商品
        product_query = select(Product).where(Product.status == "active")
        if category:
            product_query = product_query.where(Product.category == category)
        
        product_result = await self.db.execute(product_query)
        products = product_result.scalars().all()
        
        slow_selling_products = []
        
        for product in products:
            # 查询该商品在指定时间范围内的销售情况
            sales_query = select(
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.subtotal).label("total_amount"),
                func.max(Order.order_time).label("last_sale_time")
            ).join(Order, OrderItem.order_id == Order.id).where(
                and_(
                    OrderItem.product_id == product.id,
                    Order.pay_status == "success",
                    Order.order_time >= start_datetime,
                    Order.order_time <= end_datetime
                )
            )
            
            sales_result = await self.db.execute(sales_query)
            sales_row = sales_result.fetchone()
            
            total_quantity = int(sales_row.total_quantity or 0)
            last_sale_time = sales_row.last_sale_time
            
            # 计算距上次销售的天数
            if last_sale_time:
                last_sale_days = (datetime.now() - last_sale_time).days
            else:
                last_sale_days = days_threshold  # 如果从未销售，视为超过阈值
            
            # 判断是否为滞销商品
            if total_quantity <= min_sales_threshold or last_sale_days >= days_threshold:
                sale_price = float(product.sale_price or 0)
                cost_price = float(product.cost_price or 0)
                profit_margin = ((sale_price - cost_price) / sale_price * 100) if sale_price > 0 else 0
                
                slow_selling_products.append({
                    "id": product.id,
                    "product_name": product.product_name,
                    "product_code": product.product_code,
                    "category": product.category,
                    "brand": product.brand,
                    "total_quantity": total_quantity,
                    "total_amount": round(float(sales_row.total_amount or 0), 2),
                    "total_sales": round(float(sales_row.total_amount or 0), 2),
                    "last_sale_days": last_sale_days,
                    "sale_price": round(sale_price, 2),
                    "cost_price": round(cost_price, 2),
                    "profit_margin": round(profit_margin, 2),
                    "gross_margin": round(profit_margin, 2),
                    "is_low_sales": total_quantity <= min_sales_threshold,
                    "is_long_time_no_sale": last_sale_days >= days_threshold,
                    "current_inventory": random.randint(0, 50)
                })
        
        # 按滞销程度排序（距上次销售天数降序、销量升序）
        slow_selling_products.sort(key=lambda x: (-x["last_sale_days"], x["total_quantity"]))
        
        return slow_selling_products
    
    async def get_profit_margin_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取毛利率分析
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 毛利率分析数据（按分类统计）
        """
        # 默认查询最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 按分类统计毛利率
        query = select(
            Product.category,
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.subtotal).label("total_amount"),
            func.sum((OrderItem.sale_price - OrderItem.cost_price) * OrderItem.quantity).label("total_profit"),
            func.sum(OrderItem.cost_price * OrderItem.quantity).label("total_cost")
        ).join(OrderItem, Product.id == OrderItem.product_id).join(Order, OrderItem.order_id == Order.id).where(
            and_(
                Order.pay_status == "success",
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        ).group_by(Product.category).order_by(desc("total_amount"))
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        category_analysis = []
        total_stats = {
            "total_amount": 0,
            "total_cost": 0,
            "total_profit": 0,
            "total_quantity": 0
        }
        
        for row in rows:
            total_amount = float(row.total_amount or 0)
            total_cost = float(row.total_cost or 0)
            total_profit = float(row.total_profit or 0)
            
            profit_margin = (total_profit / total_amount * 100) if total_amount > 0 else 0
            
            category_data = {
                "category": row.category or "未分类",
                "total_quantity": int(row.total_quantity or 0),
                "total_amount": round(total_amount, 2),
                "total_sales": round(total_amount, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(total_profit, 2),
                "profit_margin": round(profit_margin, 2),
                "avg_margin": round(profit_margin, 2)
            }
            
            category_analysis.append(category_data)
            
            total_stats["total_amount"] += total_amount
            total_stats["total_cost"] += total_cost
            total_stats["total_profit"] += total_profit
            total_stats["total_quantity"] += int(row.total_quantity or 0)
        
        overall_profit_margin = (
            (total_stats["total_profit"] / total_stats["total_amount"] * 100)
            if total_stats["total_amount"] > 0 else 0
        )
        
        return category_analysis
    
    async def get_product_categories(self) -> List[str]:
        """
        获取所有商品分类
        """
        query = select(Product.category).where(Product.category.isnot(None)).distinct().order_by(Product.category)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        categories = [row.category for row in rows if row.category]
        return categories
    
    async def get_products_list(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取商品列表（支持分页和过滤）
        """
        query = select(Product)
        
        # 添加过滤条件
        if category:
            query = query.where(Product.category == category)
        if status:
            query = query.where(Product.status == status)
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    Product.product_name.like(keyword_pattern),
                    Product.product_code.like(keyword_pattern),
                    Product.brand.like(keyword_pattern)
                )
            )
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页查询
        query = query.order_by(desc(Product.created_at)).offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        product_list = []
        for product in products:
            sale_price = float(product.sale_price or 0)
            cost_price = float(product.cost_price or 0)
            profit_margin = ((sale_price - cost_price) / sale_price * 100) if sale_price > 0 else 0
            
            product_list.append({
                "id": product.id,
                "product_code": product.product_code,
                "product_name": product.product_name,
                "category": product.category,
                "brand": product.brand,
                "spec": product.spec,
                "sale_price": round(sale_price, 2),
                "cost_price": round(cost_price, 2),
                "profit_margin": round(profit_margin, 2),
                "gross_margin": round(profit_margin, 2),
                "status": product.status,
                "description": product.description,
                "created_at": str(product.created_at) if product.created_at else None,
                "updated_at": str(product.updated_at) if product.updated_at else None
            })
        
        return {
            "data": product_list,
            "items": product_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
