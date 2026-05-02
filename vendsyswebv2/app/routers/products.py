from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Product, Category
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ApiResponse,
)

router = APIRouter(prefix="/products", tags=["商品管理"])


@router.post("/", response_model=ProductResponse, summary="创建商品")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    创建新商品
    
    - **name**: 商品名称（必填）
    - **image_url**: 商品图片URL（可选）
    - **specification**: 商品规格（可选）
    - **barcode**: 条形码（可选，唯一）
    - **category_id**: 分类ID（必填）
    - **cost_price**: 成本价（必填）
    - **retail_price**: 零售价（必填）
    - **description**: 商品描述（可选）
    - **status**: 状态（默认active）
    """
    # 检查分类是否存在
    category = db.query(Category).filter(Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"分类 ID {product.category_id} 不存在")
    
    # 检查条形码是否已存在（如果提供了）
    if product.barcode:
        existing = db.query(Product).filter(Product.barcode == product.barcode).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"条形码 '{product.barcode}' 已存在")
    
    db_product = Product(**product.model_dump())
    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        # 加载关联的分类信息
        db_product = db.query(Product).options(joinedload(Product.category)).filter(Product.id == db_product.id).first()
        return db_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建商品失败，可能是条形码重复")


@router.get("/", response_model=List[ProductResponse], summary="获取商品列表")
def get_products(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（名称、条形码）"),
    db: Session = Depends(get_db),
):
    """
    获取商品列表，支持分页、分类筛选、状态筛选和关键词搜索
    """
    query = db.query(Product).options(joinedload(Product.category))
    
    # 分类筛选
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    
    # 状态筛选
    if status:
        query = query.filter(Product.status == status)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            (Product.name.contains(keyword)) |
            (Product.barcode.contains(keyword))
        )
    
    # 排序：按创建时间倒序
    query = query.order_by(Product.created_at.desc())
    
    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse, summary="获取单个商品")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个商品详情
    """
    product = db.query(Product).options(joinedload(Product.category)).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品 ID {product_id} 不存在")
    return product


@router.put("/{product_id}", response_model=ProductResponse, summary="更新商品")
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
):
    """
    更新商品信息
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail=f"商品 ID {product_id} 不存在")
    
    update_data = product.model_dump(exclude_unset=True)
    
    # 检查分类是否存在
    if "category_id" in update_data:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail=f"分类 ID {update_data['category_id']} 不存在")
    
    # 检查条形码是否与其他商品重复
    if "barcode" in update_data and update_data["barcode"] != db_product.barcode:
        existing = db.query(Product).filter(
            Product.barcode == update_data["barcode"],
            Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"条形码 '{update_data['barcode']}' 已存在")
    
    # 更新字段
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    try:
        db.commit()
        db.refresh(db_product)
        # 加载关联信息
        db_product = db.query(Product).options(joinedload(Product.category)).filter(Product.id == product_id).first()
        return db_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="更新商品失败")


@router.delete("/{product_id}", response_model=ApiResponse, summary="删除商品")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    删除商品（注意：如果商品已绑定到货道，删除将失败）
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail=f"商品 ID {product_id} 不存在")
    
    # 检查商品是否已绑定到货道
    if len(db_product.aisle_bindings) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"商品 '{db_product.name}' 已绑定到 {len(db_product.aisle_bindings)} 个货道，无法删除"
        )
    
    try:
        db.delete(db_product)
        db.commit()
        return ApiResponse(success=True, message=f"商品 '{db_product.name}' 删除成功")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="删除商品失败")
