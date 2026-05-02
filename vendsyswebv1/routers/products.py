"""
商品管理路由
处理商品的增删改查操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from database import get_db
from models import Product, User, Lane
from schemas import ProductCreate, ProductResponse, ProductUpdate
from routers.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/products", tags=["商品管理"])


@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    product_code: Optional[str] = None,
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取商品列表
    支持分页、搜索、筛选
    """
    query = db.query(Product)

    # 搜索筛选
    if product_code:
        query = query.filter(Product.product_code.contains(product_code))
    if product_name:
        query = query.filter(Product.product_name.contains(product_name))
    if category:
        query = query.filter(Product.category == category)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    # 排序
    query = query.order_by(desc(Product.sort_order), desc(Product.created_at))

    # 分页
    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个商品详情
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


@router.post("/", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    创建商品
    需要管理员权限
    """
    # 检查商品编码是否已存在
    existing_product = db.query(Product).filter(Product.product_code == product_data.product_code).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="商品编码已存在")

    new_product = Product(**product_data.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    更新商品信息
    需要管理员权限
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 更新字段
    update_data = product_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    删除商品
    需要管理员权限
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 检查是否被货道使用
    used_in_lanes = db.query(Lane).filter(Lane.product_id == product_id).count()
    if used_in_lanes > 0:
        raise HTTPException(status_code=400, detail=f"该商品被{used_in_lanes}个货道使用，无法删除")

    db.delete(product)
    db.commit()
    return {"message": "商品删除成功", "product_id": product_id}


@router.get("/categories/list")
def get_product_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有商品分类
    """
    from sqlalchemy import distinct
    categories = db.query(distinct(Product.category)).filter(
        Product.category.isnot(None)
    ).all()
    return {
        "categories": [c[0] for c in categories if c[0]]
    }


@router.get("/stats/summary")
def get_product_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取商品统计信息
    """
    total = db.query(Product).count()
    active = db.query(Product).filter(Product.is_active == True).count()

    # 按分类统计
    from sqlalchemy import func
    category_stats = db.query(
        Product.category,
        func.count(Product.id).label('count')
    ).filter(Product.category.isnot(None)).group_by(Product.category).all()

    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "by_category": [{"category": cs[0], "count": cs[1]} for cs in category_stats]
    }
