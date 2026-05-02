from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Aisle, VendingMachine, AisleProduct, Product
from app.schemas import (
    AisleCreate,
    AisleUpdate,
    AisleResponse,
    AisleProductCreate,
    AisleProductUpdate,
    BatchAisleProductCreate,
    AisleProductResponse,
    ApiResponse,
)

router = APIRouter(tags=["货道管理"])


@router.post("/aisles/", response_model=AisleResponse, summary="创建货道")
def create_aisle(aisle: AisleCreate, db: Session = Depends(get_db)):
    """
    创建新货道
    
    - **vending_machine_id**: 售货机ID（必填）
    - **aisle_code**: 货道编号（必填，如A1, B2等）
    - **row_number**: 行号（必填）
    - **column_number**: 列号（必填）
    - **max_capacity**: 最大容量（默认10）
    - **status**: 货道状态（默认empty）
    """
    # 检查售货机是否存在
    machine = db.query(VendingMachine).filter(VendingMachine.id == aisle.vending_machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {aisle.vending_machine_id} 不存在")
    
    # 检查同一售货机下货道编号是否已存在
    existing = db.query(Aisle).filter(
        Aisle.vending_machine_id == aisle.vending_machine_id,
        Aisle.aisle_code == aisle.aisle_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"售货机中货道编号 '{aisle.aisle_code}' 已存在"
        )
    
    db_aisle = Aisle(**aisle.model_dump())
    try:
        db.add(db_aisle)
        db.commit()
        db.refresh(db_aisle)
        return db_aisle
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建货道失败")


@router.get("/vending-machines/{machine_id}/aisles/", response_model=List[AisleResponse], summary="获取售货机货道列表")
def get_machine_aisles(
    machine_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db),
):
    """
    获取指定售货机的所有货道
    """
    # 检查售货机是否存在
    machine = db.query(VendingMachine).filter(VendingMachine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {machine_id} 不存在")
    
    query = db.query(Aisle).filter(Aisle.vending_machine_id == machine_id)
    
    if status:
        query = query.filter(Aisle.status == status)
    
    # 按行号和列号排序
    query = query.order_by(Aisle.row_number, Aisle.column_number)
    
    aisles = query.all()
    return aisles


@router.get("/aisles/{aisle_id}", response_model=AisleResponse, summary="获取单个货道")
def get_aisle(aisle_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个货道详情
    """
    aisle = db.query(Aisle).filter(Aisle.id == aisle_id).first()
    if not aisle:
        raise HTTPException(status_code=404, detail=f"货道 ID {aisle_id} 不存在")
    return aisle


@router.put("/aisles/{aisle_id}", response_model=AisleResponse, summary="更新货道")
def update_aisle(
    aisle_id: int,
    aisle: AisleUpdate,
    db: Session = Depends(get_db),
):
    """
    更新货道信息
    """
    db_aisle = db.query(Aisle).filter(Aisle.id == aisle_id).first()
    if not db_aisle:
        raise HTTPException(status_code=404, detail=f"货道 ID {aisle_id} 不存在")
    
    update_data = aisle.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_aisle, key, value)
    
    try:
        db.commit()
        db.refresh(db_aisle)
        return db_aisle
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="更新货道失败")


@router.post("/aisle-products/", response_model=AisleProductResponse, summary="创建货道商品绑定")
def create_aisle_product(binding: AisleProductCreate, db: Session = Depends(get_db)):
    """
    创建货道与商品的绑定
    
    - **aisle_id**: 货道ID（必填，唯一）
    - **product_id**: 商品ID（必填）
    - **current_stock**: 当前库存量（默认0）
    - **stock_threshold**: 库存阈值（默认5）
    - **sale_price**: 销售价格（可选，为空则使用商品零售价）
    - **status**: 绑定状态（默认active）
    """
    # 检查货道是否存在
    aisle = db.query(Aisle).filter(Aisle.id == binding.aisle_id).first()
    if not aisle:
        raise HTTPException(status_code=404, detail=f"货道 ID {binding.aisle_id} 不存在")
    
    # 检查商品是否存在
    product = db.query(Product).filter(Product.id == binding.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品 ID {binding.product_id} 不存在")
    
    # 检查货道是否已绑定商品
    existing = db.query(AisleProduct).filter(AisleProduct.aisle_id == binding.aisle_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"货道 ID {binding.aisle_id} 已绑定商品，请先解除绑定"
        )
    
    db_binding = AisleProduct(**binding.model_dump())
    try:
        db.add(db_binding)
        db.commit()
        db.refresh(db_binding)
        # 加载关联信息
        db_binding = db.query(AisleProduct).options(
            joinedload(AisleProduct.product),
            joinedload(AisleProduct.aisle)
        ).filter(AisleProduct.id == db_binding.id).first()
        return db_binding
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建货道商品绑定失败")


@router.post("/aisle-products/batch/", response_model=List[AisleProductResponse], summary="批量创建货道商品绑定")
def batch_create_aisle_products(batch_data: BatchAisleProductCreate, db: Session = Depends(get_db)):
    """
    批量创建货道商品绑定（用于批量设置货道商品）
    
    - **vending_machine_id**: 售货机ID
    - **bindings**: 绑定列表
    """
    # 检查售货机是否存在
    machine = db.query(VendingMachine).filter(VendingMachine.id == batch_data.vending_machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {batch_data.vending_machine_id} 不存在")
    
    created_bindings = []
    
    for binding_data in batch_data.bindings:
        # 检查货道是否属于该售货机
        aisle = db.query(Aisle).filter(
            Aisle.id == binding_data.aisle_id,
            Aisle.vending_machine_id == batch_data.vending_machine_id
        ).first()
        if not aisle:
            raise HTTPException(
                status_code=404,
                detail=f"货道 ID {binding_data.aisle_id} 不属于售货机 ID {batch_data.vending_machine_id}"
            )
        
        # 检查商品是否存在
        product = db.query(Product).filter(Product.id == binding_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {binding_data.product_id} 不存在")
        
        # 检查是否已绑定，已绑定则更新，否则创建
        existing = db.query(AisleProduct).filter(AisleProduct.aisle_id == binding_data.aisle_id).first()
        
        if existing:
            # 更新现有绑定
            for key, value in binding_data.model_dump(exclude_unset=True).items():
                setattr(existing, key, value)
            created_bindings.append(existing)
        else:
            # 创建新绑定
            new_binding = AisleProduct(**binding_data.model_dump())
            db.add(new_binding)
            created_bindings.append(new_binding)
    
    try:
        db.commit()
        # 重新加载所有绑定并返回
        result = []
        for binding in created_bindings:
            db.refresh(binding)
            binding_with_relations = db.query(AisleProduct).options(
                joinedload(AisleProduct.product),
                joinedload(AisleProduct.aisle)
            ).filter(AisleProduct.id == binding.id).first()
            result.append(binding_with_relations)
        return result
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="批量创建货道商品绑定失败")


@router.get("/vending-machines/{machine_id}/aisle-products/", response_model=List[AisleProductResponse], summary="获取售货机货道商品绑定列表")
def get_machine_aisle_products(
    machine_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    low_stock_only: bool = Query(False, description="仅显示低库存"),
    db: Session = Depends(get_db),
):
    """
    获取指定售货机的所有货道商品绑定信息
    """
    # 检查售货机是否存在
    machine = db.query(VendingMachine).filter(VendingMachine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {machine_id} 不存在")
    
    query = db.query(AisleProduct).options(
        joinedload(AisleProduct.product),
        joinedload(AisleProduct.aisle)
    ).join(Aisle).filter(Aisle.vending_machine_id == machine_id)
    
    if status:
        query = query.filter(AisleProduct.status == status)
    
    if low_stock_only:
        query = query.filter(AisleProduct.current_stock <= AisleProduct.stock_threshold)
    
    # 按货道行号和列号排序
    query = query.order_by(Aisle.row_number, Aisle.column_number)
    
    bindings = query.all()
    return bindings


@router.put("/aisle-products/{binding_id}", response_model=AisleProductResponse, summary="更新货道商品绑定")
def update_aisle_product(
    binding_id: int,
    binding: AisleProductUpdate,
    db: Session = Depends(get_db),
):
    """
    更新货道商品绑定信息
    """
    db_binding = db.query(AisleProduct).filter(AisleProduct.id == binding_id).first()
    if not db_binding:
        raise HTTPException(status_code=404, detail=f"货道商品绑定 ID {binding_id} 不存在")
    
    update_data = binding.model_dump(exclude_unset=True)
    
    # 检查商品是否存在
    if "product_id" in update_data:
        product = db.query(Product).filter(Product.id == update_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {update_data['product_id']} 不存在")
    
    for key, value in update_data.items():
        setattr(db_binding, key, value)
    
    try:
        db.commit()
        db.refresh(db_binding)
        # 加载关联信息
        db_binding = db.query(AisleProduct).options(
            joinedload(AisleProduct.product),
            joinedload(AisleProduct.aisle)
        ).filter(AisleProduct.id == binding_id).first()
        return db_binding
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="更新货道商品绑定失败")


@router.delete("/aisle-products/{binding_id}", response_model=ApiResponse, summary="删除货道商品绑定")
def delete_aisle_product(binding_id: int, db: Session = Depends(get_db)):
    """
    删除货道商品绑定（解除货道与商品的绑定）
    """
    db_binding = db.query(AisleProduct).filter(AisleProduct.id == binding_id).first()
    if not db_binding:
        raise HTTPException(status_code=404, detail=f"货道商品绑定 ID {binding_id} 不存在")
    
    try:
        db.delete(db_binding)
        db.commit()
        return ApiResponse(success=True, message="货道商品绑定解除成功")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="解除货道商品绑定失败")
