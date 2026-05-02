"""
测试数据生成脚本
用于生成自动售货机系统的测试数据
包括：基础数据（售货机、商品、用户）、订单数据、异常订单、对账数据、发票数据
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, delete

from config import settings
from models import (
    Base, VendingMachine, Product, User, Order, OrderItem,
    AbnormalOrder, Reconciliation, ReconciliationDetail, Invoice,
    PaymentMethod, PaymentStatus, DeliveryStatus, OrderStatus,
    AbnormalType, AbnormalStatus, ReconciliationStatus, InvoiceStatus
)


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4()).replace("-", "")


def generate_order_no() -> str:
    """生成订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = str(random.randint(100000, 999999))
    return f"VM{timestamp}{random_num}"


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    """生成随机日期"""
    time_diff = end_date - start_date
    days_diff = time_diff.days
    random_days = random.randrange(days_diff + 1)
    return start_date + timedelta(days=random_days)


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        self.vending_machines: List[VendingMachine] = []
        self.products: List[Product] = []
        self.users: List[User] = []
        self.orders: List[Order] = []
    
    async def init_database(self):
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("数据库表初始化完成")
    
    async def clear_all_data(self):
        """清空所有测试数据"""
        async with self.async_session() as session:
            async with session.begin():
                await session.execute(delete(ReconciliationDetail))
                await session.execute(delete(Reconciliation))
                await session.execute(delete(Invoice))
                await session.execute(delete(AbnormalOrder))
                await session.execute(delete(OrderItem))
                await session.execute(delete(Order))
                await session.execute(delete(User))
                await session.execute(delete(Product))
                await session.execute(delete(VendingMachine))
        print("所有数据已清空")
    
    async def create_vending_machines(self) -> List[VendingMachine]:
        """创建售货机数据"""
        machine_data = [
            {
                "machine_code": "VM001",
                "machine_name": "一号售货机",
                "location": "写字楼A座1楼大厅",
                "address": "北京市朝阳区建国路88号A座1层",
                "status": "active"
            },
            {
                "machine_code": "VM002",
                "machine_name": "二号售货机",
                "location": "写字楼A座10楼茶水间",
                "address": "北京市朝阳区建国路88号A座10层",
                "status": "active"
            },
            {
                "machine_code": "VM003",
                "machine_name": "三号售货机",
                "location": "写字楼B座1楼",
                "address": "北京市朝阳区建国路88号B座1层",
                "status": "active"
            },
            {
                "machine_code": "VM004",
                "machine_name": "四号售货机",
                "location": "地铁站A出口",
                "address": "北京市朝阳区国贸站A出口",
                "status": "active"
            },
            {
                "machine_code": "VM005",
                "machine_name": "五号售货机",
                "location": "医院门诊大厅",
                "address": "北京市海淀区中关村医院门诊大厅",
                "status": "active"
            },
        ]
        
        async with self.async_session() as session:
            async with session.begin():
                for data in machine_data:
                    machine = VendingMachine(
                        id=generate_uuid(),
                        **data
                    )
                    session.add(machine)
                    self.vending_machines.append(machine)
        
        print(f"已创建 {len(self.vending_machines)} 个售货机")
        return self.vending_machines
    
    async def create_products(self) -> List[Product]:
        """创建商品数据"""
        product_data = [
            {"product_code": "P001", "product_name": "可口可乐", "category": "饮料", "price": Decimal("3.50"), "cost_price": Decimal("2.00"), "status": "active"},
            {"product_code": "P002", "product_name": "百事可乐", "category": "饮料", "price": Decimal("3.50"), "cost_price": Decimal("2.00"), "status": "active"},
            {"product_code": "P003", "product_name": "农夫山泉", "category": "饮料", "price": Decimal("2.00"), "cost_price": Decimal("1.00"), "status": "active"},
            {"product_code": "P004", "product_name": "康师傅红茶", "category": "饮料", "price": Decimal("4.00"), "cost_price": Decimal("2.50"), "status": "active"},
            {"product_code": "P005", "product_name": "统一绿茶", "category": "饮料", "price": Decimal("4.00"), "cost_price": Decimal("2.50"), "status": "active"},
            {"product_code": "P006", "product_name": "旺仔牛奶", "category": "饮料", "price": Decimal("5.50"), "cost_price": Decimal("3.50"), "status": "active"},
            {"product_code": "P007", "product_name": "乐事薯片", "category": "零食", "price": Decimal("7.50"), "cost_price": Decimal("4.00"), "status": "active"},
            {"product_code": "P008", "product_name": "奥利奥饼干", "category": "零食", "price": Decimal("8.00"), "cost_price": Decimal("5.00"), "status": "active"},
            {"product_code": "P009", "product_name": "德芙巧克力", "category": "零食", "price": Decimal("12.00"), "cost_price": Decimal("8.00"), "status": "active"},
            {"product_code": "P010", "product_name": "怡宝纯净水", "category": "饮料", "price": Decimal("2.00"), "cost_price": Decimal("1.00"), "status": "active"},
            {"product_code": "P011", "product_name": "脉动", "category": "饮料", "price": Decimal("5.00"), "cost_price": Decimal("3.00"), "status": "active"},
            {"product_code": "P012", "product_name": "红牛", "category": "饮料", "price": Decimal("6.00"), "cost_price": Decimal("4.00"), "status": "active"},
            {"product_code": "P013", "product_name": "康师傅方便面", "category": "食品", "price": Decimal("5.00"), "cost_price": Decimal("3.00"), "status": "active"},
            {"product_code": "P014", "product_name": "士力架", "category": "零食", "price": Decimal("5.00"), "cost_price": Decimal("3.00"), "status": "active"},
            {"product_code": "P015", "product_name": "王老吉", "category": "饮料", "price": Decimal("4.50"), "cost_price": Decimal("2.50"), "status": "active"},
        ]
        
        async with self.async_session() as session:
            async with session.begin():
                for data in product_data:
                    product = Product(
                        id=generate_uuid(),
                        **data
                    )
                    session.add(product)
                    self.products.append(product)
        
        print(f"已创建 {len(self.products)} 个商品")
        return self.products
    
    async def create_users(self) -> List[User]:
        """创建用户数据"""
        user_data = [
            {"user_code": "U001", "phone": "13800138001", "nickname": "张三", "wechat_openid": "wx001"},
            {"user_code": "U002", "phone": "13800138002", "nickname": "李四", "wechat_openid": "wx002"},
            {"user_code": "U003", "phone": "13800138003", "nickname": "王五", "wechat_openid": "wx003"},
            {"user_code": "U004", "phone": "13800138004", "nickname": "赵六", "wechat_openid": "wx004"},
            {"user_code": "U005", "phone": "13800138005", "nickname": "钱七", "wechat_openid": "wx005"},
            {"user_code": "U006", "phone": "13800138006", "nickname": "孙八", "wechat_openid": "wx006"},
            {"user_code": "U007", "phone": "13800138007", "nickname": "周九", "alipay_user_id": "ali001"},
            {"user_code": "U008", "phone": "13800138008", "nickname": "吴十", "alipay_user_id": "ali002"},
        ]
        
        async with self.async_session() as session:
            async with session.begin():
                for data in user_data:
                    user = User(
                        id=generate_uuid(),
                        **data
                    )
                    session.add(user)
                    self.users.append(user)
        
        print(f"已创建 {len(self.users)} 个用户")
        return self.users
    
    async def create_orders(self, count: int = 50) -> List[Order]:
        """创建订单数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        order_statuses = [
            (OrderStatus.CREATED, PaymentStatus.PENDING, DeliveryStatus.PENDING, 0.05),
            (OrderStatus.PAID, PaymentStatus.PAID, DeliveryStatus.PENDING, 0.10),
            (OrderStatus.DELIVERED, PaymentStatus.PAID, DeliveryStatus.SUCCESS, 0.65),
            (OrderStatus.CANCELLED, PaymentStatus.PENDING, DeliveryStatus.PENDING, 0.10),
            (OrderStatus.REFUNDED, PaymentStatus.REFUNDED, DeliveryStatus.PENDING, 0.10),
        ]
        
        async with self.async_session() as session:
            async with session.begin():
                for i in range(count):
                    user = random.choice(self.users)
                    machine = random.choice(self.vending_machines)
                    
                    item_count = random.randint(1, 3)
                    selected_products = random.sample(self.products, item_count)
                    
                    total_amount = Decimal("0")
                    order_items = []
                    
                    for product in selected_products:
                        quantity = random.randint(1, 2)
                        subtotal = product.price * quantity
                        total_amount += subtotal
                        
                        order_items.append({
                            "product": product,
                            "quantity": quantity,
                            "unit_price": product.price,
                            "subtotal": subtotal
                        })
                    
                    discount_amount = Decimal("0")
                    if random.random() < 0.2:
                        discount_amount = Decimal(str(round(random.uniform(0.5, 2.0), 2)))
                    
                    pay_amount = total_amount - discount_amount
                    
                    rand_val = random.random()
                    cumulative = 0
                    order_status = OrderStatus.DELIVERED
                    payment_status = PaymentStatus.PAID
                    delivery_status = DeliveryStatus.SUCCESS
                    
                    for os, ps, ds, prob in order_statuses:
                        cumulative += prob
                        if rand_val < cumulative:
                            order_status = os
                            payment_status = ps
                            delivery_status = ds
                            break
                    
                    payment_method = random.choice([PaymentMethod.WECHAT, PaymentMethod.ALIPAY])
                    
                    created_at = random_date(start_date, end_date)
                    
                    paid_at = None
                    if payment_status in [PaymentStatus.PAID, PaymentStatus.REFUNDED]:
                        paid_at = created_at + timedelta(seconds=random.randint(10, 60))
                    
                    delivered_at = None
                    if delivery_status == DeliveryStatus.SUCCESS:
                        if paid_at:
                            delivered_at = paid_at + timedelta(seconds=random.randint(30, 120))
                        else:
                            delivered_at = created_at + timedelta(seconds=random.randint(60, 180))
                    
                    order = Order(
                        id=generate_uuid(),
                        order_no=generate_order_no(),
                        user_id=user.id,
                        machine_id=machine.id,
                        total_amount=total_amount,
                        discount_amount=discount_amount,
                        pay_amount=pay_amount,
                        payment_method=payment_method,
                        payment_status=payment_status,
                        third_party_order_no=f"TP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}" if payment_status != PaymentStatus.PENDING else None,
                        delivery_status=delivery_status,
                        order_status=order_status,
                        created_at=created_at,
                        paid_at=paid_at,
                        delivered_at=delivered_at
                    )
                    
                    session.add(order)
                    await session.flush()
                    
                    for item_data in order_items:
                        item = OrderItem(
                            id=generate_uuid(),
                            order_id=order.id,
                            product_id=item_data["product"].id,
                            product_code=item_data["product"].product_code,
                            product_name=item_data["product"].product_name,
                            quantity=item_data["quantity"],
                            unit_price=item_data["unit_price"],
                            subtotal_amount=item_data["subtotal"],
                            delivery_status=delivery_status,
                            delivered_quantity=item_data["quantity"] if delivery_status == DeliveryStatus.SUCCESS else 0
                        )
                        session.add(item)
                    
                    self.orders.append(order)
        
        print(f"已创建 {len(self.orders)} 个订单")
        return self.orders
    
    async def create_abnormal_orders(self, count: int = 10) -> List[AbnormalOrder]:
        """创建异常订单数据"""
        abnormal_types = [
            AbnormalType.PAID_NO_DELIVERY,
            AbnormalType.DELIVERY_FAILED,
            AbnormalType.DUPLICATE_PAYMENT,
            AbnormalType.SYSTEM_ERROR,
            AbnormalType.OTHER,
        ]
        
        abnormal_descriptions = {
            AbnormalType.PAID_NO_DELIVERY: "用户付款成功但售货机未出货",
            AbnormalType.DELIVERY_FAILED: "售货机出货时卡货或失败",
            AbnormalType.DUPLICATE_PAYMENT: "系统检测到重复扣款",
            AbnormalType.SYSTEM_ERROR: "系统异常导致订单状态错误",
            AbnormalType.OTHER: "其他异常情况",
        }
        
        async with self.async_session() as session:
            async with session.begin():
                paid_orders = [o for o in self.orders if o.order_status in [OrderStatus.PAID, OrderStatus.DELIVERED]]
                selected_orders = random.sample(paid_orders, min(count, len(paid_orders)))
                
                for order in selected_orders:
                    abnormal_type = random.choice(abnormal_types)
                    
                    order.order_status = OrderStatus.ABNORMAL
                    
                    abnormal = AbnormalOrder(
                        id=generate_uuid(),
                        order_id=order.id,
                        abnormal_type=abnormal_type,
                        abnormal_description=abnormal_descriptions[abnormal_type],
                        abnormal_time=order.created_at + timedelta(seconds=random.randint(300, 3600)),
                        status=random.choice([
                            AbnormalStatus.PENDING,
                            AbnormalStatus.PROCESSING,
                            AbnormalStatus.REFUNDED,
                            AbnormalStatus.REDISPATCHED,
                            AbnormalStatus.CLOSED,
                        ])
                    )
                    
                    if abnormal.status == AbnormalStatus.REFUNDED:
                        abnormal.refund_amount = order.pay_amount
                        abnormal.refund_reason = "用户投诉未出货"
                        abnormal.refund_approved_at = datetime.now() - timedelta(hours=1)
                        abnormal.refund_completed_at = datetime.now()
                        abnormal.handled_by = "管理员"
                        abnormal.status = AbnormalStatus.REFUNDED
                        
                        order.payment_status = PaymentStatus.REFUNDED
                        order.order_status = OrderStatus.REFUNDED
                    
                    if abnormal.status == AbnormalStatus.REDISPATCHED:
                        abnormal.redispatch_approved_at = datetime.now() - timedelta(hours=1)
                        abnormal.redispatch_completed_at = datetime.now()
                        abnormal.handled_by = "管理员"
                        abnormal.status = AbnormalStatus.REDISPATCHED
                        
                        order.delivery_status = DeliveryStatus.SUCCESS
                        order.delivered_at = datetime.now()
                        order.order_status = OrderStatus.DELIVERED
                    
                    session.add(abnormal)
        
        print(f"已创建 {len(selected_orders)} 个异常订单")
        return []
    
    async def create_reconciliations(self) -> List[Reconciliation]:
        """创建对账数据"""
        async with self.async_session() as session:
            async with session.begin():
                recon_dates = [
                    "2025-01-15",
                    "2025-01-16",
                    "2025-01-17",
                ]
                
                for recon_date in recon_dates:
                    for payment_method in [PaymentMethod.WECHAT, PaymentMethod.ALIPAY]:
                        orders_for_recon = [
                            o for o in self.orders 
                            if o.payment_method == payment_method 
                            and o.payment_status != PaymentStatus.PENDING
                        ]
                        
                        system_count = len(orders_for_recon)
                        system_amount = sum(o.pay_amount for o in orders_for_recon)
                        system_refund_count = sum(1 for o in orders_for_recon if o.payment_status == PaymentStatus.REFUNDED)
                        system_refund_amount = sum(o.pay_amount for o in orders_for_recon if o.payment_status == PaymentStatus.REFUNDED)
                        
                        diff_factor = random.uniform(0.98, 1.02)
                        platform_count = int(system_count * diff_factor)
                        platform_amount = Decimal(str(round(float(system_amount) * diff_factor, 2)))
                        
                        diff_count = abs(system_count - platform_count)
                        diff_amount = abs(system_amount - platform_amount)
                        
                        status = ReconciliationStatus.MATCHED
                        if diff_count > 0 or diff_amount > Decimal("0.01"):
                            status = random.choice([ReconciliationStatus.UNMATCHED, ReconciliationStatus.RESOLVED])
                        
                        recon = Reconciliation(
                            id=generate_uuid(),
                            recon_date=recon_date,
                            recon_type="daily",
                            payment_method=payment_method,
                            system_total_count=system_count,
                            system_total_amount=system_amount,
                            system_refund_count=system_refund_count,
                            system_refund_amount=system_refund_amount,
                            platform_total_count=platform_count,
                            platform_total_amount=platform_amount,
                            platform_refund_count=system_refund_count,
                            platform_refund_amount=system_refund_amount,
                            diff_count=diff_count,
                            diff_amount=diff_amount,
                            status=status,
                            resolved_by="管理员" if status == ReconciliationStatus.RESOLVED else None,
                            resolved_at=datetime.now() if status == ReconciliationStatus.RESOLVED else None,
                            resolve_remark="平台漏单，已手工补录" if status == ReconciliationStatus.RESOLVED else None
                        )
                        
                        session.add(recon)
                        await session.flush()
                        
                        sample_orders = random.sample(orders_for_recon, min(5, len(orders_for_recon)))
                        for order in sample_orders:
                            is_matched = random.random() > 0.2
                            detail = ReconciliationDetail(
                                id=generate_uuid(),
                                recon_id=recon.id,
                                order_id=order.id,
                                order_no=order.order_no,
                                third_party_order_no=order.third_party_order_no,
                                system_amount=order.pay_amount,
                                system_status=order.payment_status.value if order.payment_status else None,
                                platform_amount=order.pay_amount if is_matched else order.pay_amount + Decimal("0.10"),
                                platform_status=order.payment_status.value if order.payment_status else None,
                                is_matched=is_matched,
                                diff_amount=Decimal("0") if is_matched else Decimal("0.10"),
                                is_resolved=status == ReconciliationStatus.RESOLVED,
                                resolved_by="管理员" if status == ReconciliationStatus.RESOLVED else None,
                                resolved_at=datetime.now() if status == ReconciliationStatus.RESOLVED else None,
                            )
                            session.add(detail)
        
        print("已创建对账数据")
        return []
    
    async def create_invoices(self, count: int = 8) -> List[Invoice]:
        """创建发票数据"""
        async with self.async_session() as session:
            async with session.begin():
                delivered_orders = [o for o in self.orders if o.order_status in [OrderStatus.DELIVERED, OrderStatus.PAID]]
                selected_orders = random.sample(delivered_orders, min(count, len(delivered_orders)))
                
                company_titles = [
                    {"name": "北京某某科技有限公司", "tax_no": "91110105MA00XXXXX"},
                    {"name": "上海某某贸易有限公司", "tax_no": "91310110MA00YYYYY"},
                    {"name": "广州某某信息技术有限公司", "tax_no": "91440100MA00ZZZZZ"},
                ]
                
                personal_names = ["张三", "李四", "王五", "赵六"]
                
                for i, order in enumerate(selected_orders):
                    is_company = random.random() > 0.5
                    
                    if is_company:
                        company = random.choice(company_titles)
                        title_type = "company"
                        title_name = company["name"]
                        tax_no = company["tax_no"]
                        company_address = "北京市朝阳区某某路某某号"
                        company_phone = "010-12345678"
                        bank_name = "中国工商银行北京支行"
                        bank_account = "6222020200001234567"
                    else:
                        title_type = "personal"
                        title_name = random.choice(personal_names)
                        tax_no = None
                        company_address = None
                        company_phone = None
                        bank_name = None
                        bank_account = None
                    
                    statuses = [
                        InvoiceStatus.PENDING,
                        InvoiceStatus.APPROVED,
                        InvoiceStatus.ISSUED,
                        InvoiceStatus.REJECTED,
                    ]
                    status = random.choice(statuses)
                    
                    invoice = Invoice(
                        id=generate_uuid(),
                        order_id=order.id,
                        user_id=order.user_id,
                        invoice_no=f"INV{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}" if status == InvoiceStatus.ISSUED else None,
                        invoice_type="electronic",
                        title_type=title_type,
                        title_name=title_name,
                        tax_no=tax_no,
                        company_address=company_address,
                        company_phone=company_phone,
                        bank_name=bank_name,
                        bank_account=bank_account,
                        invoice_content="商品明细",
                        invoice_amount=order.pay_amount,
                        tax_amount=order.pay_amount * Decimal("0.13") if is_company else Decimal("0"),
                        receiver_name=order.user.nickname if order.user else "用户",
                        receiver_phone=order.user.phone if order.user else None,
                        receiver_email=f"user{i+1}@example.com",
                        status=status,
                        reviewer="张会计" if status in [InvoiceStatus.APPROVED, InvoiceStatus.REJECTED] else None,
                        review_remark="审核通过" if status == InvoiceStatus.APPROVED else "信息有误，需补充" if status == InvoiceStatus.REJECTED else None,
                        reviewed_at=datetime.now() - timedelta(hours=2) if status in [InvoiceStatus.APPROVED, InvoiceStatus.REJECTED] else None,
                        issuer="李开票" if status == InvoiceStatus.ISSUED else None,
                        issued_at=datetime.now() - timedelta(hours=1) if status == InvoiceStatus.ISSUED else None,
                        invoice_url=f"https://invoice.example.com/pdf/{generate_uuid()}.pdf" if status == InvoiceStatus.ISSUED else None,
                        invoice_pdf_url=f"https://invoice.example.com/pdf/{generate_uuid()}.pdf" if status == InvoiceStatus.ISSUED else None,
                        reject_reason="发票抬头信息不完整" if status == InvoiceStatus.REJECTED else None,
                    )
                    
                    session.add(invoice)
        
        print(f"已创建 {len(selected_orders)} 个发票申请")
        return []
    
    async def generate_all_data(self, order_count: int = 50, abnormal_count: int = 10, invoice_count: int = 8):
        """生成所有测试数据"""
        print("=" * 60)
        print("开始生成测试数据...")
        print("=" * 60)
        
        await self.init_database()
        
        await self.create_vending_machines()
        await self.create_products()
        await self.create_users()
        await self.create_orders(order_count)
        await self.create_abnormal_orders(abnormal_count)
        await self.create_reconciliations()
        await self.create_invoices(invoice_count)
        
        print("=" * 60)
        print("测试数据生成完成！")
        print("=" * 60)
        print(f"统计:")
        print(f"  - 售货机: {len(self.vending_machines)} 台")
        print(f"  - 商品: {len(self.products)} 个")
        print(f"  - 用户: {len(self.users)} 个")
        print(f"  - 订单: {len(self.orders)} 个")
        print(f"  - 异常订单: {abnormal_count} 个")
        print(f"  - 发票申请: {invoice_count} 个")
        print("=" * 60)


async def main():
    """主函数"""
    import sys
    
    generator = TestDataGenerator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        print("正在清空所有数据...")
        await generator.clear_all_data()
        print("数据已清空")
    else:
        order_count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
        abnormal_count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        invoice_count = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        
        await generator.generate_all_data(
            order_count=order_count,
            abnormal_count=abnormal_count,
            invoice_count=invoice_count
        )


if __name__ == "__main__":
    asyncio.run(main())
