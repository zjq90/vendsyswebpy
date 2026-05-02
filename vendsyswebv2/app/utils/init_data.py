"""
数据库初始化和测试数据生成模块
用于初始化数据库表结构和生成测试数据
"""

from datetime import datetime, time
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.models import (
    Category,
    Product,
    VendingMachine,
    Aisle,
    AisleProduct,
    PriceStrategy,
    ReplenishmentOrder,
)


def init_database():
    """
    初始化数据库
    创建所有表结构
    """
    Base.metadata.create_all(bind=engine)
    print("数据库表结构创建完成")


def generate_test_data():
    """
    生成测试数据
    """
    db: Session = SessionLocal()
    
    try:
        # 1. 创建商品分类
        categories_data = [
            {"name": "饮料", "description": "各类瓶装、罐装饮料"},
            {"name": "零食", "description": "各类休闲零食"},
            {"name": "方便食品", "description": "方便面、盒饭等"},
            {"name": "日用品", "description": "纸巾、口罩等日常用品"},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat = Category(**cat_data)
            db.add(cat)
            categories.append(cat)
        
        db.commit()
        print(f"已创建 {len(categories)} 个商品分类")
        
        # 2. 创建商品
        products_data = [
            # 饮料类
            {"name": "可口可乐 330ml", "barcode": "6901939621103", "specification": "330ml/罐", 
             "cost_price": 2.5, "retail_price": 3.5, "category_id": 1, "status": "active"},
            {"name": "百事可乐 330ml", "barcode": "6921168509256", "specification": "330ml/罐", 
             "cost_price": 2.5, "retail_price": 3.5, "category_id": 1, "status": "active"},
            {"name": "农夫山泉 550ml", "barcode": "6921168500017", "specification": "550ml/瓶", 
             "cost_price": 1.5, "retail_price": 2.5, "category_id": 1, "status": "active"},
            {"name": "康师傅冰红茶 500ml", "barcode": "6921316911234", "specification": "500ml/瓶", 
             "cost_price": 2.8, "retail_price": 4.0, "category_id": 1, "status": "active"},
            
            # 零食类
            {"name": "乐事薯片 原味 75g", "barcode": "6924743915010", "specification": "75g/袋", 
             "cost_price": 5.5, "retail_price": 8.5, "category_id": 2, "status": "active"},
            {"name": "奥利奥饼干 97g", "barcode": "6901668002471", "specification": "97g/盒", 
             "cost_price": 6.0, "retail_price": 9.9, "category_id": 2, "status": "active"},
            {"name": "德芙巧克力 43g", "barcode": "6923644266684", "specification": "43g/块", 
             "cost_price": 7.5, "retail_price": 12.0, "category_id": 2, "status": "active"},
            
            # 方便食品类
            {"name": "康师傅红烧牛肉面", "barcode": "6920208880181", "specification": "108g/桶", 
             "cost_price": 3.5, "retail_price": 5.5, "category_id": 3, "status": "active"},
            {"name": "统一老坛酸菜牛肉面", "barcode": "6925303771107", "specification": "120g/桶", 
             "cost_price": 3.8, "retail_price": 6.0, "category_id": 3, "status": "active"},
            
            # 日用品类
            {"name": "维达抽纸 3层", "barcode": "6922868281103", "specification": "3层*100抽", 
             "cost_price": 4.5, "retail_price": 7.0, "category_id": 4, "status": "active"},
            {"name": "一次性口罩 10只装", "barcode": "6971234567890", "specification": "10只/包", 
             "cost_price": 3.0, "retail_price": 5.0, "category_id": 4, "status": "active"},
        ]
        
        products = []
        for prod_data in products_data:
            prod = Product(**prod_data)
            db.add(prod)
            products.append(prod)
        
        db.commit()
        print(f"已创建 {len(products)} 个商品")
        
        # 3. 创建售货机
        machines_data = [
            {"name": "写字楼A座1号机", "serial_number": "VM001", 
             "location": "写字楼A座1楼大厅", "region": "downtown", 
             "status": "online", "row_count": 6, "column_count": 8},
            {"name": "地铁站B口2号机", "serial_number": "VM002", 
             "location": "地铁1号线B出口", "region": "subway", 
             "status": "online", "row_count": 6, "column_count": 8},
            {"name": "医院门诊3号机", "serial_number": "VM003", 
             "location": "人民医院门诊大厅", "region": "hospital", 
             "status": "online", "row_count": 6, "column_count": 8},
        ]
        
        machines = []
        for mach_data in machines_data:
            mach = VendingMachine(**mach_data)
            db.add(mach)
            machines.append(mach)
        
        db.commit()
        print(f"已创建 {len(machines)} 个售货机")
        
        # 4. 为每个售货机创建货道
        aisles = []
        for machine in machines:
            # 为售货机创建6行8列的货道
            for row in range(1, machine.row_count + 1):
                for col in range(1, machine.column_count + 1):
                    # 生成货道编号（A1, A2, ..., H8）
                    row_letter = chr(ord('A') + row - 1)
                    aisle_code = f"{row_letter}{col}"
                    
                    aisle = Aisle(
                        vending_machine_id=machine.id,
                        aisle_code=aisle_code,
                        row_number=row,
                        column_number=col,
                        max_capacity=10,
                        status="empty"
                    )
                    db.add(aisle)
                    aisles.append(aisle)
        
        db.commit()
        print(f"已创建 {len(aisles)} 个货道")
        
        # 5. 将商品绑定到货道（为每个售货机绑定部分商品）
        bindings = []
        
        # 为第一个售货机绑定商品
        machine1_aisles = db.query(Aisle).filter(Aisle.vending_machine_id == 1).all()
        # 商品ID列表
        product_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        
        # 为前11个货道绑定商品
        for i, aisle in enumerate(machine1_aisles[:11]):
            product_idx = i % len(product_ids)
            binding = AisleProduct(
                aisle_id=aisle.id,
                product_id=product_ids[product_idx],
                current_stock=8 if i != 5 else 3,  # 第6个货道设为低库存
                stock_threshold=5,
                status="active"
            )
            db.add(binding)
            bindings.append(binding)
            # 更新货道状态
            aisle.status = "normal"
        
        db.commit()
        print(f"已创建 {len(bindings)} 个货道商品绑定")
        
        # 6. 创建价格策略
        price_strategies_data = [
            # 夜间折扣（分时段定价）
            {
                "name": "夜间折扣8折",
                "strategy_type": "time_based",
                "start_time": time(22, 0),
                "end_time": time(6, 0),
                "discount_type": "percentage",
                "discount_value": 80,
                "priority": 2,
                "status": "active",
                "description": "每晚22:00至次日6:00，所有商品8折"
            },
            # 地铁站区域溢价（区域定价）
            {
                "name": "地铁站区域溢价",
                "strategy_type": "region_based",
                "applicable_region": "subway",
                "discount_type": "percentage",
                "discount_value": 110,
                "priority": 1,
                "status": "active",
                "description": "地铁站区域商品价格上浮10%"
            },
            # 促销活动
            {
                "name": "五一促销活动",
                "strategy_type": "promotion",
                "start_date": datetime(2026, 5, 1),
                "end_date": datetime(2026, 5, 7),
                "discount_type": "percentage",
                "discount_value": 85,
                "priority": 3,
                "status": "active",
                "description": "五一假期促销，所有商品85折"
            },
            # 特定商品固定价格
            {
                "name": "矿泉水特价",
                "strategy_type": "time_based",
                "product_id": 3,  # 农夫山泉
                "start_time": time(8, 0),
                "end_time": time(10, 0),
                "applicable_days": "1,2,3,4,5",  # 工作日
                "discount_type": "fixed_price",
                "discount_value": 2.0,
                "priority": 2,
                "status": "active",
                "description": "工作日早8点至10点，矿泉水特价2元"
            },
        ]
        
        for strat_data in price_strategies_data:
            strat = PriceStrategy(**strat_data)
            db.add(strat)
        
        db.commit()
        print(f"已创建 {len(price_strategies_data)} 个价格策略")
        
        # 7. 为低库存商品创建补货单
        low_stock_bindings = db.query(AisleProduct).filter(
            AisleProduct.current_stock <= AisleProduct.stock_threshold
        ).all()
        
        for binding in low_stock_bindings:
            replenishment_order = ReplenishmentOrder(
                order_number=f"RO{datetime.utcnow().strftime('%Y%m%d')}{binding.id:03d}",
                vending_machine_id=binding.aisle.vending_machine_id,
                aisle_product_id=binding.id,
                current_stock=binding.current_stock,
                stock_threshold=binding.stock_threshold,
                suggested_quantity=binding.aisle.max_capacity - binding.current_stock,
                priority="high" if binding.current_stock == 0 else "medium",
                status="pending"
            )
            db.add(replenishment_order)
        
        db.commit()
        print(f"已创建 {len(low_stock_bindings)} 个补货单")
        
        print("\n测试数据生成完成！")
        print("=" * 50)
        print(f"商品分类: {len(categories)} 个")
        print(f"商品: {len(products)} 个")
        print(f"售货机: {len(machines)} 个")
        print(f"货道: {len(aisles)} 个")
        print(f"货道商品绑定: {len(bindings)} 个")
        print(f"价格策略: {len(price_strategies_data)} 个")
        print(f"补货单: {len(low_stock_bindings)} 个")
        
    except Exception as e:
        db.rollback()
        print(f"生成测试数据时出错: {e}")
        raise
    finally:
        db.close()


def reset_database():
    """
    重置数据库
    删除所有表并重新创建
    """
    Base.metadata.drop_all(bind=engine)
    print("所有表已删除")
    init_database()


if __name__ == "__main__":
    print("开始初始化数据库...")
    init_database()
    print("\n开始生成测试数据...")
    generate_test_data()
