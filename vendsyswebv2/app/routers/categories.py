from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Category
from app.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    ApiResponse,
)

router = APIRouter(prefix="/categories", tags=["商品分类管理"])


@router.post("/", response_model=CategoryResponse, summary="创建分类")
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """
    创建新的商品分类
    
    - **name**: 分类名称（必填，唯一）
    - **description**: 分类描述（可选）
    """
    # 检查分类名是否已存在
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail=f"分类名称 '{category.name}' 已存在")
    
    db_category = Category(**category.model_dump())
    try:
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建分类失败，可能是名称重复")


@router.get("/", response_model=List[CategoryResponse], summary="获取分类列表")
def get_categories(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db),
):
    """
    获取商品分类列表，支持分页
    """
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories


@router.get("/{category_id}", response_model=CategoryResponse, summary="获取单个分类")
def get_category(category_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个分类详情
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"分类 ID {category_id} 不存在")
    return category


@router.put("/{category_id}", response_model=CategoryResponse, summary="更新分类")
def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
):
    """
    更新分类信息
    
    - **name**: 分类名称（可选）
    - **description**: 分类描述（可选）
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail=f"分类 ID {category_id} 不存在")
    
    # 检查新名称是否与其他分类重复
    if category.name and category.name != db_category.name:
        existing = db.query(Category).filter(Category.name == category.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"分类名称 '{category.name}' 已存在")
    
    # 更新字段
    update_data = category.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    try:
        db.commit()
        db.refresh(db_category)
        return db_category
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="更新分类失败")


@router.delete("/{category_id}", response_model=ApiResponse, summary="删除分类")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    删除分类（注意：如果分类下有商品，删除将失败）
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail=f"分类 ID {category_id} 不存在")
    
    # 检查分类下是否有商品
    if len(db_category.products) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"分类 '{db_category.name}' 下存在 {len(db_category.products)} 个商品，无法删除"
        )
    
    try:
        db.delete(db_category)
        db.commit()
        return ApiResponse(success=True, message=f"分类 '{db_category.name}' 删除成功")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="删除分类失败")
