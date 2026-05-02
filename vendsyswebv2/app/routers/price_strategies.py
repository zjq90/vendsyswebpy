from datetime import datetime, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import PriceStrategy, Product, VendingMachine, AisleProduct
from app.schemas import (
    PriceStrategyCreate,
    PriceStrategyUpdate,
    PriceStrategyResponse,
    ApiResponse,
)

router = APIRouter(prefix="/price-strategies", tags=["价格策略管理"])


@router.post("/", response_model=PriceStrategyResponse, summary="创建价格策略")
def create_price_strategy(strategy: PriceStrategyCreate, db: Session = Depends(get_db)):
    """
    创建新的价格策略
    
    支持三种策略类型：
    - **time_based**: 分时段定价
    - **region_based**: 区域差异化定价
    - **promotion**: 促销活动价格
    
    折扣类型：
    - **percentage**: 百分比折扣（如80表示8折）
    - **fixed**: 固定金额折扣
    - **fixed_price**: 固定价格
    """
    # 如果指定了商品ID，检查商品是否存在
    if strategy.product_id:
        product = db.query(Product).filter(Product.id == strategy.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {strategy.product_id} 不存在")
    
    # 验证时段设置
    if strategy.start_time and strategy.end_time:
        if strategy.start_time >= strategy.end_time:
            raise HTTPException(
                status_code=400,
                detail="开始时间必须早于结束时间"
            )
    
    # 验证促销日期
    if strategy.strategy_type == "promotion":
        if strategy.start_date and strategy.end_date:
            if strategy.start_date >= strategy.end_date:
                raise HTTPException(
                    status_code=400,
                    detail="促销开始日期必须早于结束日期"
                )
    
    db_strategy = PriceStrategy(**strategy.model_dump())
    try:
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建价格策略失败")


@router.get("/", response_model=List[PriceStrategyResponse], summary="获取价格策略列表")
def get_price_strategies(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
    strategy_type: Optional[str] = Query(None, description="策略类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    product_id: Optional[int] = Query(None, description="商品ID筛选"),
    db: Session = Depends(get_db),
):
    """
    获取价格策略列表，支持筛选
    """
    query = db.query(PriceStrategy)
    
    if strategy_type:
        query = query.filter(PriceStrategy.strategy_type == strategy_type)
    
    if status:
        query = query.filter(PriceStrategy.status == status)
    
    if product_id:
        query = query.filter(
            (PriceStrategy.product_id == product_id) |
            (PriceStrategy.product_id.is_(None))
        )
    
    # 按优先级和创建时间排序
    query = query.order_by(
        PriceStrategy.priority.desc(),
        PriceStrategy.created_at.desc()
    )
    
    strategies = query.offset(skip).limit(limit).all()
    return strategies


@router.get("/{strategy_id}", response_model=PriceStrategyResponse, summary="获取单个价格策略")
def get_price_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个价格策略详情
    """
    strategy = db.query(PriceStrategy).filter(PriceStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail=f"价格策略 ID {strategy_id} 不存在")
    return strategy


@router.put("/{strategy_id}", response_model=PriceStrategyResponse, summary="更新价格策略")
def update_price_strategy(
    strategy_id: int,
    strategy: PriceStrategyUpdate,
    db: Session = Depends(get_db),
):
    """
    更新价格策略信息
    """
    db_strategy = db.query(PriceStrategy).filter(PriceStrategy.id == strategy_id).first()
    if not db_strategy:
        raise HTTPException(status_code=404, detail=f"价格策略 ID {strategy_id} 不存在")
    
    update_data = strategy.model_dump(exclude_unset=True)
    
    # 检查商品是否存在
    if "product_id" in update_data and update_data["product_id"]:
        product = db.query(Product).filter(Product.id == update_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {update_data['product_id']} 不存在")
    
    # 验证时段设置
    start_time = update_data.get("start_time", db_strategy.start_time)
    end_time = update_data.get("end_time", db_strategy.end_time)
    if start_time and end_time and start_time >= end_time:
        raise HTTPException(status_code=400, detail="开始时间必须早于结束时间")
    
    # 更新字段
    for key, value in update_data.items():
        setattr(db_strategy, key, value)
    
    try:
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="更新价格策略失败")


@router.delete("/{strategy_id}", response_model=ApiResponse, summary="删除价格策略")
def delete_price_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """
    删除价格策略
    """
    db_strategy = db.query(PriceStrategy).filter(PriceStrategy.id == strategy_id).first()
    if not db_strategy:
        raise HTTPException(status_code=404, detail=f"价格策略 ID {strategy_id} 不存在")
    
    try:
        db.delete(db_strategy)
        db.commit()
        return ApiResponse(success=True, message=f"价格策略 '{db_strategy.name}' 删除成功")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="删除价格策略失败")


@router.post("/calculate-price/", response_model=dict, summary="计算当前价格")
def calculate_current_price(
    product_id: int = Query(..., description="商品ID"),
    machine_id: int = Query(..., description="售货机ID"),
    current_time_str: Optional[str] = Query(None, description="当前时间（格式HH:MM），默认为当前系统时间"),
    db: Session = Depends(get_db),
):
    """
    计算商品在指定售货机的当前价格，考虑所有适用的价格策略
    
    价格策略优先级：
    1. 促销活动（promotion）
    2. 分时段定价（time_based）
    3. 区域定价（region_based）
    
    同类型策略中，优先级数值高的优先
    """
    # 检查商品是否存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品 ID {product_id} 不存在")
    
    # 检查售货机是否存在
    machine = db.query(VendingMachine).filter(VendingMachine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {machine_id} 不存在")
    
    # 获取基础价格（优先取货道设置的价格）
    binding = db.query(AisleProduct).filter(
        AisleProduct.product_id == product_id,
        AisleProduct.aisle.has(vending_machine_id=machine_id)
    ).first()
    
    base_price = float(product.retail_price)
    if binding and binding.sale_price:
        base_price = float(binding.sale_price)
    
    # 解析当前时间
    if current_time_str:
        try:
            current_time = datetime.strptime(current_time_str, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式错误，请使用HH:MM格式")
    else:
        current_time = datetime.utcnow().time()
    
    # 获取当前星期几（1=周一，7=周日）
    current_day = datetime.utcnow().isoweekday()
    
    # 获取所有启用的价格策略
    all_strategies = db.query(PriceStrategy).filter(
        PriceStrategy.status == "active"
    ).order_by(PriceStrategy.priority.desc()).all()
    
    # 按策略类型分组
    promotion_strategies = []
    time_based_strategies = []
    region_based_strategies = []
    
    for strategy in all_strategies:
        # 检查是否适用于该商品（product_id为None表示适用于所有商品）
        if strategy.product_id is not None and strategy.product_id != product_id:
            continue
        
        # 检查是否适用
        is_applicable = False
        
        if strategy.strategy_type == "promotion":
            # 检查促销日期
            now = datetime.utcnow()
            if strategy.start_date and now < strategy.start_date:
                continue
            if strategy.end_date and now > strategy.end_date:
                continue
            is_applicable = True
            promotion_strategies.append(strategy)
        
        elif strategy.strategy_type == "time_based":
            # 检查时段
            if strategy.start_time and strategy.end_time:
                if strategy.start_time <= current_time <= strategy.end_time:
                    # 检查星期
                    if strategy.applicable_days:
                        days = [int(d.strip()) for d in strategy.applicable_days.split(",")]
                        if current_day in days:
                            is_applicable = True
                    else:
                        is_applicable = True
            if is_applicable:
                time_based_strategies.append(strategy)
        
        elif strategy.strategy_type == "region_based":
            # 检查区域
            if strategy.applicable_region and machine.region == strategy.applicable_region:
                is_applicable = True
                region_based_strategies.append(strategy)
    
    # 确定适用的策略（按优先级）
    applicable_strategy = None
    
    # 1. 促销活动优先级最高
    if promotion_strategies:
        applicable_strategy = promotion_strategies[0]
    # 2. 分时段定价
    elif time_based_strategies:
        applicable_strategy = time_based_strategies[0]
    # 3. 区域定价
    elif region_based_strategies:
        applicable_strategy = region_based_strategies[0]
    
    # 计算最终价格
    final_price = base_price
    applied_strategy_name = None
    applied_strategy_type = None
    
    if applicable_strategy:
        final_price = applicable_strategy.calculate_price(base_price)
        applied_strategy_name = applicable_strategy.name
        applied_strategy_type = applicable_strategy.strategy_type
    
    # 确保价格不低于0
    final_price = max(0, round(final_price, 2))
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "machine_id": machine_id,
        "machine_name": machine.name,
        "base_price": base_price,
        "final_price": final_price,
        "discount_amount": round(base_price - final_price, 2),
        "applied_strategy": applied_strategy_name,
        "strategy_type": applied_strategy_type,
        "current_time": current_time.strftime("%H:%M"),
        "current_day": current_day,
    }
