from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.tag import Tag
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
)

router = APIRouter(prefix="/api/tags", tags=["tags"])


# ==================== 标签 CRUD ====================

@router.get("", response_model=List[TagResponse])
def get_tags(db: Session = Depends(get_db)):
    """获取所有标签"""
    tags = db.query(Tag).order_by(Tag.created_at.desc()).all()
    return tags


@router.post("", response_model=TagResponse)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """创建标签"""
    # 检查是否已存在
    existing = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")

    db_tag = Tag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, tag: TagUpdate, db: Session = Depends(get_db)):
    """更新标签"""
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    if tag.name is not None:
        # 检查新名称是否与其他标签冲突
        existing = db.query(Tag).filter(Tag.name == tag.name, Tag.id != tag_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="标签名称已存在")
        db_tag.name = tag.name

    db.commit()
    db.refresh(db_tag)
    return db_tag


@router.delete("/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """删除标签"""
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    db.delete(db_tag)
    db.commit()
    return {"message": "删除成功"}


# ==================== 批量操作 ====================

@router.post("/batch")
def batch_create_tags(names: List[str], db: Session = Depends(get_db)):
    """批量创建标签"""
    created = []
    skipped = []

    for name in names:
        name = name.strip()
        if not name:
            continue

        existing = db.query(Tag).filter(Tag.name == name).first()
        if existing:
            skipped.append(name)
        else:
            db_tag = Tag(name=name)
            db.add(db_tag)
            created.append(name)

    db.commit()
    return {"created": created, "skipped": skipped}
