from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.model_config import ModelConfig
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
)

router = APIRouter(prefix="/api/model-configs", tags=["model-configs"])


@router.get("", response_model=List[ModelConfigResponse])
def get_model_configs(db: Session = Depends(get_db)):
    """获取所有模型配置"""
    configs = db.query(ModelConfig).order_by(ModelConfig.is_default.desc(), ModelConfig.id).all()
    return configs


@router.get("/{config_id}", response_model=ModelConfigResponse)
def get_model_config(config_id: int, db: Session = Depends(get_db)):
    """获取单个模型配置"""
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.post("", response_model=ModelConfigResponse)
def create_model_config(config: ModelConfigCreate, db: Session = Depends(get_db)):
    """创建模型配置"""
    # 检查名称是否已存在
    existing = db.query(ModelConfig).filter(ModelConfig.name == config.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置名称已存在")

    # 如果设为默认，先取消其他默认
    if config.is_default:
        db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})

    db_config = ModelConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.put("/{config_id}", response_model=ModelConfigResponse)
def update_model_config(config_id: int, config: ModelConfigUpdate, db: Session = Depends(get_db)):
    """更新模型配置"""
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = config.model_dump(exclude_unset=True)

    # 如果设为默认，先取消其他默认
    if update_data.get("is_default"):
        db.query(ModelConfig).filter(ModelConfig.is_default == True, ModelConfig.id != config_id).update({"is_default": False})

    for key, value in update_data.items():
        setattr(db_config, key, value)

    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/{config_id}")
def delete_model_config(config_id: int, db: Session = Depends(get_db)):
    """删除模型配置"""
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    db.delete(db_config)
    db.commit()
    return {"message": "删除成功"}


@router.post("/set-default/{config_id}")
def set_default_config(config_id: int, db: Session = Depends(get_db)):
    """设为默认配置"""
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 取消其他默认
    db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})

    db_config.is_default = True
    db.commit()
    return {"message": "设置成功"}
