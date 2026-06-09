from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from backend.database import get_config, set_config, get_all_configs, delete_config

router = APIRouter()


class ConfigItem(BaseModel):
    key: str
    value: Any
    description: Optional[str] = ""
    is_sensitive: Optional[bool] = False


class ConfigUpdate(BaseModel):
    value: Any
    description: Optional[str] = ""
    is_sensitive: Optional[bool] = False


@router.get("/configs")
async def list_configs(include_sensitive: bool = False):
    """获取所有配置"""
    try:
        configs = get_all_configs(include_sensitive=include_sensitive)
        return {"configs": configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs/{key}")
async def get_config_item(key: str):
    """获取单个配置"""
    value = get_config(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")
    return {"key": key, "value": value}


@router.post("/configs")
async def create_config(item: ConfigItem):
    """创建或更新配置"""
    try:
        set_config(
            key=item.key,
            value=item.value,
            description=item.description or "",
            is_sensitive=item.is_sensitive or False
        )
        return {"message": "Config saved successfully", "key": item.key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/configs/{key}")
async def update_config(key: str, update: ConfigUpdate):
    """更新配置"""
    try:
        set_config(
            key=key,
            value=update.value,
            description=update.description or "",
            is_sensitive=update.is_sensitive or False
        )
        return {"message": "Config updated successfully", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/configs/{key}")
async def delete_config_item(key: str):
    """删除配置"""
    try:
        delete_config(key)
        return {"message": "Config deleted successfully", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
