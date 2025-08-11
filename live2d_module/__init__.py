#!/usr/bin/env python3
"""
Live2D模块初始化文件
为NagaAgent提供Live2D数字人功能
"""

import logging
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger("live2d_module")

# 模块版本
__version__ = "1.0.0"
__author__ = "NagaAgent Team"
__description__ = "Live2D数字人集成模块"

# 导出的类和函数
from .event_adapter import (
    EventBus, Event, EventType, event_bus, 
    subscribe, unsubscribe, publish, get_event_history,
    create_ai_response_event, create_emotion_event,
    create_lip_sync_event, create_tts_event, create_asr_event
)

from .emotion_handler import Live2DEmotionHandler
from .audio_integration import Live2DAudioAdapter

# 尝试导入Live2D控件（如果可用）
try:
    from .live2d_widget import NagaLive2DWidget
    LIVE2D_WIDGET_AVAILABLE = True
    logger.info("Live2D控件模块可用")
except ImportError as e:
    LIVE2D_WIDGET_AVAILABLE = False
    logger.warning(f"Live2D控件模块不可用: {e}")

def init_live2d_module(config: Dict[str, Any] = None) -> bool:
    """初始化Live2D模块"""
    try:
        if not LIVE2D_WIDGET_AVAILABLE:
            logger.warning("Live2D控件模块不可用，仅提供事件和音频功能")
            return True
            
        # 这里可以添加更多的初始化逻辑
        logger.info("Live2D模块初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"Live2D模块初始化失败: {e}")
        return False

def get_live2d_status() -> Dict[str, Any]:
    """获取Live2D模块状态"""
    return {
        "version": __version__,
        "widget_available": LIVE2D_WIDGET_AVAILABLE,
        "emotion_handler_available": True,
        "audio_adapter_available": True,
        "event_bus_available": True
    }

def check_dependencies() -> Dict[str, Any]:
    """检查依赖项"""
    dependencies = {
        "live2d_v3": False,
        "pyopengl": False,
        "numpy": False,
        "aiohttp": False,
        "pydantic": False
    }
    
    try:
        import live2d.v3
        dependencies["live2d_v3"] = True
    except ImportError:
        pass
        
    try:
        import OpenGL
        dependencies["pyopengl"] = True
    except ImportError:
        pass
        
    try:
        import numpy
        dependencies["numpy"] = True
    except ImportError:
        pass
        
    try:
        import aiohttp
        dependencies["aiohttp"] = True
    except ImportError:
        pass
        
    try:
        import pydantic
        dependencies["pydantic"] = True
    except ImportError:
        pass
        
    return dependencies

def get_missing_dependencies() -> List[str]:
    """获取缺失的依赖项"""
    deps = check_dependencies()
    missing = [dep for dep, available in deps.items() if not available]
    return missing

# 模块级别的配置
DEFAULT_CONFIG = {
    "enabled": True,
    "emotion_analysis": True,
    "lip_sync": True,
    "tts_enabled": True,
    "asr_enabled": True,
    "model_path": "models/hiyori_pro_mic.model3.json",
    "scale": 1.0,
    "offset_x": 1050,
    "offset_y": 600,
    "cache_enabled": True,
    "cache_dir": "live2d_cache"
}

def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """验证配置"""
    validated = DEFAULT_CONFIG.copy()
    validated.update(config)
    
    # 验证数值范围
    validated["scale"] = max(0.1, min(3.0, validated.get("scale", 1.0)))
    validated["offset_x"] = max(0, min(3840, validated.get("offset_x", 1050)))
    validated["offset_y"] = max(0, min(2160, validated.get("offset_y", 600)))
    
    return validated

# 便捷函数
def create_live2d_config(
    enabled: bool = True,
    model_path: str = "models/hiyori_pro_mic.model3.json",
    scale: float = 1.0,
    offset_x: int = 1050,
    offset_y: int = 600,
    emotion_analysis: bool = True,
    lip_sync: bool = True,
    tts_enabled: bool = True,
    asr_enabled: bool = True
) -> Dict[str, Any]:
    """创建Live2D配置"""
    return {
        "enabled": enabled,
        "model_path": model_path,
        "scale": scale,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "emotion_analysis": emotion_analysis,
        "lip_sync": lip_sync,
        "tts_enabled": tts_enabled,
        "asr_enabled": asr_enabled
    }

# 模块信息
__all__ = [
    "EventBus", "Event", "EventType", "event_bus",
    "subscribe", "unsubscribe", "publish", "get_event_history",
    "create_ai_response_event", "create_emotion_event",
    "create_lip_sync_event", "create_tts_event", "create_asr_event",
    "Live2DEmotionHandler", "Live2DAudioAdapter",
    "init_live2d_module", "get_live2d_status", "check_dependencies",
    "get_missing_dependencies", "get_default_config", "validate_config",
    "create_live2d_config", "LIVE2D_WIDGET_AVAILABLE"
]

# 初始化日志
logger.info(f"Live2D模块已加载，版本: {__version__}")
if not LIVE2D_WIDGET_AVAILABLE:
    logger.warning("Live2D控件模块不可用，某些功能可能受限")