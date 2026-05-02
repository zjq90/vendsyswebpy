"""
自动售后机数据统计与分析系统 - 测试数据生成脚本

此脚本用于生成测试数据，包括：
- 设备数据
- 商品数据
- 用户数据
- 订单数据
- 库存数据
- 运维记录数据

运行方式:
    python generate_test_data.py
"""
import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings
from app.models.models import (
    Base,
    Device,
    Product,
    User,
    Order,
    OrderItem,
    Inventory,
    Maintenance
)


# 随机数据生成配置
DEVICES_COUNT = 20
PRODUCTS_COUNT = 30
USERS_COUNT = 100
ORDERS_COUNT = 5000
MAINTENANCE_COUNT = 50

# 商品分类
PRODUCT_CATEGORIES = [
    "饮料", "零食", "方便食品", "日用品", "冷饮",
    "乳制品", "糕点", "糖果", "调味品", "进口食品"
]

# 商品数据模板
PRODUCT_TEMPLATES = [
    {"name": "可口可乐", "category": "饮料", "sale_price": 3.5, "cost_price": 2.0},
    {"name": "百事可乐", "category": "饮料", "sale_price": 3.5, "cost_price": 2.0},
    {"name": "农夫山泉", "category": "饮料", "sale_price": 2.0, "cost_price": 0.8},
    {"name": "怡宝矿泉水", "category": "饮料", "sale_price": 2.0, "cost_price": 0.8},
    {"name": "康师傅红茶", "category": "饮料", "sale_price": 3.0, "cost_price": 1.5},
    {"name": "绿茶", "category": "饮料", "sale_price": 3.0, "cost_price": 1.5},
    {"name": "脉动", "category": "饮料", "sale_price": 4.5, "cost_price": 2.5},
    {"name": "红牛", "category": "饮料", "sale_price": 6.0, "cost_price": 4.0},
    {"name": "乐事薯片", "category": "零食", "sale_price": 8.5, "cost_price": 4.5},
    {"name": "可比克薯片", "category": "零食", "sale_price": 7.5, "cost_price": 4.0},
    {"name": "旺旺雪饼", "category": "零食", "sale_price": 12.0, "cost_price": 6.0},
    {"name": "奥利奥饼干", "category": "零食", "sale_price": 9.5, "cost_price": 5.0},
    {"name": "康师傅红烧牛肉面", "category": "方便食品", "sale_price": 5.0, "cost_price": 2.5},
    {"name": "统一老坛酸菜", "category": "方便食品", "sale_price": 5.0, "cost_price": 2.5},
    {"name": "康师傅泡面桶", "category": "方便食品", "sale_price": 6.0, "cost_price": 3.0},
    {"name": "火腿肠", "category": "方便食品", "sale_price": 2.5, "cost_price": 1.2},
    {"name": "餐巾纸", "category": "日用品", "sale_price": 3.0, "cost_price": 1.0},
    {"name": "湿纸巾", "category": "日用品", "sale_price": 5.0, "cost_price": 2.0},
    {"name": "口香糖", "category": "日用品", "sale_price": 8.0, "cost_price": 4.0},
    {"name": "打火机", "category": "日用品", "sale_price": 1.0, "cost_price": 0.3},
    {"name": "伊利纯牛奶", "category": "乳制品", "sale_price": 3.5, "cost_price": 2.0},
    {"name": "蒙牛纯牛奶", "category": "乳制品", "sale_price": 3.5, "cost_price": 2.0},
    {"name": "旺仔牛奶", "category": "乳制品", "sale_price": 5.0, "cost_price": 2.5},
    {"name": "酸奶", "category": "乳制品", "sale_price": 6.5, "cost_price": 3.5},
    {"name": "德芙巧克力", "category": "糖果", "sale_price": 12.0, "cost_price": 6.0},
    {"name": "大白兔奶糖", "category": "糖果", "sale_price": 8.0, "cost_price": 4.0},
    {"name": "阿尔卑斯糖", "category": "糖果", "sale_price": 6.0, "cost_price": 3.0},
    {"name": "不二家棒棒糖", "category": "糖果", "sale_price": 5.0, "cost_price": 2.5},
    {"name": "梦龙冰淇淋", "category": "冷饮", "sale_price": 8.0, "cost_price": 4.0},
    {"name": "可爱多", "category": "冷饮", "sale_price": 6.0, "cost_price": 3.0},
    {"name": "巧乐兹", "category": "冷饮", "sale_price": 4.0, "cost_price": 2.0},
    {"name": "老冰棍", "category": "冷饮", "sale_price": 1.0, "cost_price": 0.3},
]

# 设备位置
DEVICE_LOCATIONS = [
    "办公楼A座大厅", "办公楼B座大厅", "办公楼C座大厅",
    "地铁站A出口", "地铁站B出口", "地铁站C出口",
    "商场1号门", "商场2号门", "商场3号门",
    "医院门诊大厅", "医院住院部", "医院急诊部",
    "学校教学楼A", "学校教学楼B", "学校食堂",
    "火车站候车室", "汽车站候车室", "机场T1航站楼",
    "产业园A区", "产业园B区", "产业园C区",
]

# 设备名称前缀
DEVICE_PREFIXES = ["智能售货机", "自动售货柜", "无人售卖机", "智能贩卖机"]

# 用户昵称
USER_NICKNAMES = [
    "小明", "小红", "小刚", "小丽", "小强", "小美", "小华", "小燕",
    "阿强", "阿美", "阿华", "阿丽", "阿明", "阿芳", "阿伟", "阿珍",
    "阳光少年", "快乐女孩", "开心果", "小猫咪", "大灰狼", "小兔子",
    "飞翔的鸟", "大海", "清风", "明月", "星辰", "阳光", "雨露",
    "追梦人", "奋斗者", "乐观派", "开心每一天", "幸福满满", "快乐至上",
]

# 支付方式
PAYMENT_METHODS = ["alipay", "wechat", "cash", "card"]
PAYMENT_WEIGHTS = [0.4, 0.45, 0.1, 0.05]

# 订单状态
ORDER_STATUSES = ["completed", "paid", "refunded", "cancelled"]
ORDER_WEIGHTS = [0.85, 0.1, 0.03, 0.02]

# 设备状态
DEVICE_STATUSES = ["online", "online", "online", "online", "offline", "maintenance", "fault"]

# 用户类型
USER_TYPES = ["registered", "registered", "registered", "registered", "guest", "vip"]


def generate_random_date(start_date: datetime, end_date: datetime) -> datetime:
    """生成随机日期"""
    time_delta = end_date - start_date
    random_days = random.randint(0, time_delta.days)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    
    return start_date + timedelta(
        days=random_days,
        hours=random_hours,
        minutes=random_minutes,
        seconds=random_seconds
    )


def generate_phone_number() -> str:
    """生成随机手机号"""
    prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                "150", "151", "152", "153", "155", "156", "157", "158", "159",
                "180", "181", "182", "183", "184", "185", "186", "187", "188", "189",
                "170", "176", "177", "178"]
    prefix = random.choice(prefixes)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


async def generate_devices(session: AsyncSession) -> List[Device]:
    """生成设备数据"""
    print(f"正在生成 {DEVICES_COUNT} 条设备数据...")
    
    devices = []
    for i in range(DEVICES_COUNT):
        device_code = f"DEV{i+1:04d}"
        device_name = f"{random.choice(DEVICE_PREFIXES)}-{device_code}"
        location = random.choice(DEVICE_LOCATIONS) if i < len(DEVICE_LOCATIONS) else f"位置{i+1}"
        
        device = Device(
            device_code=device_code,
            device_name=device_name,
            location=location,
            status=random.choice(DEVICE_STATUSES),
            capacity=random.randint(50, 200),
            last_maintenance_date=generate_random_date(
                datetime.now() - timedelta(days=7),
                datetime.now()
            ).date()
        )
        devices.append(device)
        session.add(device)
    
    await session.commit()
    print(f"[OK] 设备数据生成完成，共 {len(devices)} 条")
    return devices


async def generate_products(session: AsyncSession) -> List[Product]:
    """生成商品数据"""
    print(f"正在生成商品数据...")
    
    products = []
    templates = PRODUCT_TEMPLATES[:PRODUCTS_COUNT] if PRODUCTS_COUNT < len(PRODUCT_TEMPLATES) else PRODUCT_TEMPLATES
    
    for i, template in enumerate(templates):
        product_code = f"PRD{i+1:05d}"
        
        price_variation = random.uniform(0.9, 1.1)
        sale_price = round(template["sale_price"] * price_variation, 2)
        cost_price = round(template["cost_price"] * price_variation, 2)
        
        product = Product(
            product_code=product_code,
            product_name=template["name"],
            category=template["category"],
            sale_price=Decimal(str(sale_price)),
            cost_price=Decimal(str(cost_price)),
            status="active" if random.random() > 0.1 else "inactive"
        )
        products.append(product)
        session.add(product)
    
    await session.commit()
    print(f"[OK] 商品数据生成完成，共 {len(products)} 条")
    return products


async def generate_users(session: AsyncSession) -> List[User]:
    """生成用户数据"""
    print(f"正在生成 {USERS_COUNT} 条用户数据...")
    
    users = []
    used_phones = set()
    
    for i in range(USERS_COUNT):
        while True:
            phone = generate_phone_number()
            if phone not in used_phones:
                used_phones.add(phone)
                break
        
        user_code = f"USR{i+1:06d}"
        nickname = random.choice(USER_NICKNAMES) if i < len(USER_NICKNAMES) else f"用户{i+1}"
        user_type = random.choices(USER_TYPES)[0]
        
        created_at = generate_random_date(
            datetime.now() - timedelta(days=365),
            datetime.now()
        )
        
        user = User(
            user_code=user_code,
            phone=phone,
            nickname=nickname,
            user_type=user_type,
            created_at=created_at
        )
        users.append(user)
        session.add(user)
    
    await session.commit()
    print(f"[OK] 用户数据生成完成，共 {len(users)} 条")
    return users


async def generate_inventories(session: AsyncSession, devices: List[Device], products: List[Product]):
    """生成库存数据"""
    print("正在生成库存数据...")
    
    inventories = []
    for device in devices:
        for product in products:
            if random.random() > 0.3:
                max_stock = random.randint(20, 100)
                current_stock = random.randint(0, max_stock)
                
                inventory = Inventory(
                    device_id=device.id,
                    product_id=product.id,
                    current_quantity=current_stock,
                    max_quantity=max_stock
                )
                inventories.append(inventory)
                session.add(inventory)
    
    await session.commit()
    print(f"[OK] 库存数据生成完成，共 {len(inventories)} 条")


async def generate_orders(session: AsyncSession, devices: List[Device], users: List[User], products: List[Product]):
    """生成订单数据"""
    print(f"正在生成 {ORDERS_COUNT} 条订单数据...")
    
    start_date = datetime.now() - timedelta(days=180)
    end_date = datetime.now()
    
    orders_count = 0
    order_items_count = 0
    
    for i in range(ORDERS_COUNT):
        order_no = f"ORD{datetime.now().strftime('%Y%m%d')}{i+1:08d}"
        created_at = generate_random_date(start_date, end_date)
        
        device = random.choice(devices)
        user = random.choice(users) if random.random() > 0.2 else None
        
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]
        status = random.choices(ORDER_STATUSES, weights=ORDER_WEIGHTS)[0]
        
        item_count = random.randint(1, 5)
        total_amount = Decimal("0")
        total_items = 0
        
        order = Order(
            order_no=order_no,
            device_id=device.id,
            user_id=user.id if user else None,
            total_amount=total_amount,
            pay_amount=total_amount,
            total_quantity=total_items,
            pay_method=payment_method,
            pay_status="success" if status in ["completed", "paid"] else status,
            order_time=created_at
        )
        session.add(order)
        await session.flush()
        
        order_items = []
        selected_products = random.sample(products, min(item_count, len(products)))
        
        for product in selected_products:
            quantity = random.randint(1, 3)
            sale_price = product.sale_price
            cost_price = product.cost_price
            subtotal = sale_price * Decimal(quantity)
            
            total_amount += subtotal
            total_items += quantity
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.product_name,
                product_code=product.product_code,
                quantity=quantity,
                sale_price=sale_price,
                cost_price=cost_price,
                subtotal=subtotal
            )
            order_items.append(order_item)
            session.add(order_item)
            order_items_count += 1
        
        order.total_amount = total_amount
        order.pay_amount = total_amount
        order.total_quantity = total_items
        orders_count += 1
        
        if (i + 1) % 500 == 0:
            await session.commit()
            print(f"  已处理 {i+1}/{ORDERS_COUNT} 条订单...")
    
    await session.commit()
    print(f"[OK] 订单数据生成完成，共 {orders_count} 条订单，{order_items_count} 条订单明细")


async def generate_maintenance(session: AsyncSession, devices: List[Device]):
    """生成运维记录数据"""
    print(f"正在生成 {MAINTENANCE_COUNT} 条运维记录数据...")
    
    maintenance_types = ["repair", "maintenance", "check", "part_replacement"]
    maintenance_names = {
        "repair": "故障维修",
        "maintenance": "日常维护",
        "check": "设备巡检",
        "part_replacement": "配件更换"
    }
    
    statuses = ["pending", "processing", "completed"]
    
    maintenances = []
    start_date = datetime.now() - timedelta(days=180)
    end_date = datetime.now()
    
    for i in range(MAINTENANCE_COUNT):
        device = random.choice(devices)
        maintenance_type = random.choice(maintenance_types)
        
        created_at = generate_random_date(start_date, end_date)
        duration_minutes = random.randint(15, 240)
        cost = Decimal(str(round(random.uniform(50, 2000), 2)))
        
        status = "completed" if created_at < datetime.now() - timedelta(hours=duration_minutes / 60) else random.choice(statuses)
        
        maintenance = Maintenance(
            device_id=device.id,
            maintenance_type=maintenance_type,
            title=f"{maintenance_names[maintenance_type]} - 设备:{device.device_name}",
            description=f"{maintenance_names[maintenance_type]} - 设备:{device.device_name}",
            cost=cost,
            duration_minutes=duration_minutes,
            status=status,
            report_time=created_at
        )
        maintenances.append(maintenance)
        session.add(maintenance)
    
    await session.commit()
    print(f"[OK] 运维记录数据生成完成，共 {len(maintenances)} 条")


async def clear_old_data(session: AsyncSession):
    """清除旧数据"""
    print("正在清除旧数据...")
    
    await session.execute(delete(Maintenance))
    await session.execute(delete(OrderItem))
    await session.execute(delete(Order))
    await session.execute(delete(Inventory))
    await session.execute(delete(User))
    await session.execute(delete(Product))
    await session.execute(delete(Device))
    
    await session.commit()
    print("[OK] 旧数据清除完成")


async def main():
    """主函数"""
    print("=" * 60)
    print("自动售后机数据统计与分析系统 - 测试数据生成脚本")
    print("=" * 60)
    print(f"数据库地址: {settings.DATABASE_URL}")
    print()
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        await clear_old_data(session)
        print()
        
        devices = await generate_devices(session)
        products = await generate_products(session)
        users = await generate_users(session)
        
        await generate_inventories(session, devices, products)
        await generate_orders(session, devices, users, products)
        await generate_maintenance(session, devices)
        
        print()
        print("=" * 60)
        print("[OK] 测试数据生成完成！")
        print("=" * 60)
        print()
        print("数据统计:")
        print(f"  - 设备数: {DEVICES_COUNT}")
        print(f"  - 商品数: {len(PRODUCT_TEMPLATES)}")
        print(f"  - 用户数: {USERS_COUNT}")
        print(f"  - 订单数: {ORDERS_COUNT}")
        print(f"  - 运维记录数: {MAINTENANCE_COUNT}")
        print()
        print("提示:")
        print("  - 订单数据覆盖过去 180 天")
        print("  - 用户数据包含注册用户、游客和VIP用户")
        print("  - 支付方式包含支付宝(40%)、微信(45%)、现金(10%)、银行卡(5%)")
        print()
        print("请运行以下命令启动服务器:")
        print("  python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
