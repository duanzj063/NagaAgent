#!/usr/bin/env python3
"""
Live2D API模块
为NagaAgent提供Live2D数字人功能的API接口
"""

import os
import tempfile
import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import aiohttp
import asyncio
import wave
import numpy as np

# 导入事件总线适配器
from .event_adapter import event_bus

logger = logging.getLogger("live2d_api")

# 请求模型
class EmotionRequest(BaseModel):
    emotion: str = Field(..., description="情绪名称")
    intensity: float = Field(default=1.0, ge=0.0, le=2.0, description="情绪强度")
    
class TTSRequest(BaseModel):
    text: str = Field(..., description="要转换的文本")
    output_path: Optional[str] = Field(None, description="输出音频文件路径")
    voice_id: Optional[str] = Field(None, description="语音ID")
    
class LipSyncRequest(BaseModel):
    audio_path: str = Field(..., description="音频文件路径")
    intensity: float = Field(default=3.0, ge=0.5, le=5.0, description="嘴型同步强度")
    
class Live2DConfigRequest(BaseModel):
    enabled: bool = Field(default=True, description="是否启用Live2D")
    model_path: Optional[str] = Field(None, description="Live2D模型路径")
    scale: Optional[float] = Field(None, ge=0.1, le=3.0, description="模型缩放比例")
    offset_x: Optional[int] = Field(None, description="X轴偏移")
    offset_y: Optional[int] = Field(None, description="Y轴偏移")
    tts_enabled: Optional[bool] = Field(None, description="是否启用TTS")
    asr_enabled: Optional[bool] = Field(None, description="是否启用ASR")
    tts_api_url: Optional[str] = Field(None, description="TTS API URL")
    asr_api_url: Optional[str] = Field(None, description="ASR API URL")
    emotion_analysis: Optional[bool] = Field(None, description="是否启用情绪分析")
    lip_sync_enabled: Optional[bool] = Field(None, description="是否启用嘴型同步")

class EmotionAnalysisRequest(BaseModel):
    text: str = Field(..., description="要分析的文本")
    session_id: Optional[str] = Field(None, description="会话ID")

# 响应模型
class Live2DStatusResponse(BaseModel):
    available: bool = Field(..., description="Live2D是否可用")
    initialized: bool = Field(..., description="是否已初始化")
    model_loaded: bool = Field(..., description="模型是否已加载")
    current_emotion: str = Field(..., description="当前情绪")
    emotion_analysis_enabled: bool = Field(..., description="情绪分析是否启用")
    lip_sync_enabled: bool = Field(..., description="嘴型同步是否启用")
    tts_enabled: bool = Field(..., description="TTS是否启用")
    asr_enabled: bool = Field(..., description="ASR是否启用")

class EmotionAnalysisResponse(BaseModel):
    emotion: str = Field(..., description="检测到的情绪")
    intensity: float = Field(..., description="情绪强度")
    confidence: float = Field(..., description="置信度")
    keywords: List[str] = Field(..., description="匹配的关键词")

class Live2DConfigResponse(BaseModel):
    enabled: bool = Field(..., description="是否启用Live2D")
    model_path: Optional[str] = Field(None, description="Live2D模型路径")
    scale: float = Field(..., description="模型缩放比例")
    offset_x: int = Field(..., description="X轴偏移")
    offset_y: int = Field(..., description="Y轴偏移")
    tts_enabled: bool = Field(..., description="是否启用TTS")
    asr_enabled: bool = Field(..., description="是否启用ASR")
    tts_api_url: str = Field(..., description="TTS API URL")
    asr_api_url: str = Field(..., description="ASR API URL")
    emotion_analysis: bool = Field(..., description="是否启用情绪分析")
    lip_sync_enabled: bool = Field(..., description="是否启用嘴型同步")

# 全局Live2D实例
live2d_widget = None
emotion_handler = None
audio_adapter = None

# 路由器
router = APIRouter(prefix="/api/live2d", tags=["Live2D"])

def init_live2d_services(config: Dict[str, Any] = None) -> bool:
    """初始化Live2D服务"""
    global live2d_widget, emotion_handler, audio_adapter
    
    try:
        # 尝试导入Live2D模块
        try:
            from live2d_module.live2d_widget import NagaLive2DWidget
            from live2d_module.emotion_handler import Live2DEmotionHandler
            from live2d_module.audio_integration import Live2DAudioAdapter
            LIVE2D_AVAILABLE = True
        except ImportError as e:
            logger.warning(f"Live2D模块不可用: {e}")
            LIVE2D_AVAILABLE = False
            return False
        
        if not LIVE2D_AVAILABLE:
            logger.warning("Live2D模块不可用")
            return False
        
        # 初始化情绪处理器
        emotion_config = config.get("emotion", {}) if config else {}
        emotion_handler = Live2DEmotionHandler(emotion_config)
        
        # 初始化音频适配器
        audio_config = {
            "tts_enabled": config.get("tts_enabled", True) if config else True,
            "asr_enabled": config.get("asr_enabled", True) if config else True,
            "tts_api_url": config.get("tts_api_url", "http://127.0.0.1:8000/voice/speak") if config else "http://127.0.0.1:8000/voice/speak",
            "asr_api_url": config.get("asr_api_url", "http://127.0.0.1:8000/voice/transcribe") if config else "http://127.0.0.1:8000/voice/transcribe"
        }
        audio_adapter = Live2DAudioAdapter(audio_config)
        
        # 注意：Live2D控件需要在主线程初始化，这里只做配置
        logger.info("Live2D服务初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"Live2D服务初始化失败: {e}")
        return False

def set_live2d_widget(widget):
    """设置Live2D控件实例"""
    global live2d_widget
    live2d_widget = widget
    logger.info("Live2D控件实例已设置")

@router.get("/status", response_model=Live2DStatusResponse)
async def get_live2d_status():
    """获取Live2D状态"""
    try:
        available = live2d_widget is not None
        
        return Live2DStatusResponse(
            available=available,
            initialized=available,
            model_loaded=live2d_widget.model is not None if available else False,
            current_emotion=emotion_handler.current_emotion if emotion_handler else "neutral",
            emotion_analysis_enabled=emotion_handler.enabled if emotion_handler else False,
            lip_sync_enabled=live2d_widget.lip_sync_thread is not None if available else False,
            tts_enabled=audio_adapter.tts_enabled if audio_adapter else False,
            asr_enabled=audio_adapter.asr_enabled if audio_adapter else False
        )
    except Exception as e:
        logger.error(f"获取Live2D状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.post("/emotion/trigger")
async def trigger_emotion(request: EmotionRequest):
    """触发Live2D情绪动作"""
    if not live2d_widget:
        raise HTTPException(status_code=400, detail="Live2D控件未初始化")
        
    try:
        # 触发情绪动作
        live2d_widget.trigger_emotion(request.emotion, request.intensity)
        
        # 发布事件
        await event_bus.publish("live2d_emotion_triggered", {
            "emotion": request.emotion,
            "intensity": request.intensity
        })
        
        return {
            "status": "success", 
            "emotion": request.emotion,
            "intensity": request.intensity,
            "message": f"情绪 '{request.emotion}' 触发成功"
        }
    except Exception as e:
        logger.error(f"触发情绪失败: {e}")
        raise HTTPException(status_code=500, detail=f"触发情绪失败: {str(e)}")

@router.post("/emotion/analyze", response_model=EmotionAnalysisResponse)
async def analyze_emotion(request: EmotionAnalysisRequest):
    """分析文本情绪"""
    if not emotion_handler:
        raise HTTPException(status_code=400, detail="情绪处理器未初始化")
        
    try:
        # 分析情绪
        emotion, intensity = emotion_handler.analyze_emotion(request.text)
        
        # 获取匹配的关键词
        keywords = []
        for keyword_list in emotion_handler.emotion_keywords.get(emotion, []):
            if keyword_list.lower() in request.text.lower():
                keywords.append(keyword_list)
        
        # 发布事件
        await event_bus.publish("live2d_emotion_analyzed", {
            "text": request.text,
            "emotion": emotion,
            "intensity": intensity,
            "session_id": request.session_id
        })
        
        return EmotionAnalysisResponse(
            emotion=emotion,
            intensity=intensity,
            confidence=min(intensity / 2.0, 1.0),  # 将强度转换为置信度
            keywords=keywords
        )
    except Exception as e:
        logger.error(f"情绪分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"情绪分析失败: {str(e)}")

@router.post("/text-to-speech")
async def text_to_speech(request: TTSRequest):
    """文本转语音"""
    if not audio_adapter:
        raise HTTPException(status_code=400, detail="音频适配器未初始化")
        
    try:
        # 转换文本为语音
        audio_path = await audio_adapter.text_to_speech(request.text, request.output_path)
        
        if audio_path:
            # 获取音频时长
            duration = audio_adapter.get_audio_duration(audio_path)
            
            return {
                "status": "success",
                "audio_path": audio_path,
                "duration": duration,
                "text": request.text,
                "message": "TTS转换成功"
            }
        else:
            raise HTTPException(status_code=500, detail="TTS转换失败")
            
    except Exception as e:
        logger.error(f"TTS转换失败: {e}")
        raise HTTPException(status_code=500, detail=f"TTS转换失败: {str(e)}")

@router.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """语音转文本"""
    if not audio_adapter:
        raise HTTPException(status_code=400, detail="音频适配器未初始化")
        
    try:
        # 保存上传的音频文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(await audio_file.read())
            temp_path = temp_file.name
            
        # 进行语音识别
        text = await audio_adapter.speech_to_text(temp_path)
        
        # 清理临时文件
        os.unlink(temp_path)
        
        if text:
            return {
                "status": "success",
                "text": text,
                "message": "语音识别成功"
            }
        else:
            raise HTTPException(status_code=500, detail="语音识别失败")
            
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")

@router.post("/start-lip-sync")
async def start_lip_sync(request: LipSyncRequest):
    """开始嘴型同步"""
    if not live2d_widget:
        raise HTTPException(status_code=400, detail="Live2D控件未初始化")
        
    try:
        # 检查音频文件是否存在
        if not os.path.exists(request.audio_path):
            raise HTTPException(status_code=400, detail="音频文件不存在")
        
        # 开始嘴型同步
        success = live2d_widget.start_lip_sync(request.audio_path)
        
        if success:
            # 发布事件
            await event_bus.publish("live2d_lip_sync_started", {
                "audio_path": request.audio_path,
                "intensity": request.intensity
            })
            
            return {
                "status": "success",
                "audio_path": request.audio_path,
                "intensity": request.intensity,
                "message": "嘴型同步启动成功"
            }
        else:
            raise HTTPException(status_code=500, detail="嘴型同步启动失败")
            
    except Exception as e:
        logger.error(f"嘴型同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"嘴型同步失败: {str(e)}")

@router.post("/stop-lip-sync")
async def stop_lip_sync():
    """停止嘴型同步"""
    if not live2d_widget:
        raise HTTPException(status_code=400, detail="Live2D控件未初始化")
        
    try:
        live2d_widget.stop_lip_sync()
        
        # 发布事件
        await event_bus.publish("live2d_lip_sync_stopped", {})
        
        return {
            "status": "success",
            "message": "嘴型同步已停止"
        }
    except Exception as e:
        logger.error(f"停止嘴型同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止嘴型同步失败: {str(e)}")

@router.post("/config/update", response_model=Dict[str, Any])
async def update_config(request: Live2DConfigRequest):
    """更新Live2D配置"""
    try:
        config_updates = request.dict(exclude_unset=True)
        updated_fields = []
        
        # 更新Live2D控件配置
        if live2d_widget:
            if "scale" in config_updates:
                live2d_widget.scale = config_updates["scale"]
                updated_fields.append("scale")
            if "offset_x" in config_updates:
                live2d_widget.model_offset_x = config_updates["offset_x"]
                updated_fields.append("offset_x")
            if "offset_y" in config_updates:
                live2d_widget.model_offset_y = config_updates["offset_y"]
                updated_fields.append("offset_y")
                
        # 更新情绪处理器配置
        if emotion_handler:
            if "emotion_analysis" in config_updates:
                emotion_handler.set_enabled(config_updates["emotion_analysis"])
                updated_fields.append("emotion_analysis")
                
        # 更新音频适配器配置
        if audio_adapter:
            if "tts_enabled" in config_updates:
                audio_adapter.tts_enabled = config_updates["tts_enabled"]
                updated_fields.append("tts_enabled")
            if "asr_enabled" in config_updates:
                audio_adapter.asr_enabled = config_updates["asr_enabled"]
                updated_fields.append("asr_enabled")
            if "tts_api_url" in config_updates:
                audio_adapter.tts_api_url = config_updates["tts_api_url"]
                updated_fields.append("tts_api_url")
            if "asr_api_url" in config_updates:
                audio_adapter.asr_api_url = config_updates["asr_api_url"]
                updated_fields.append("asr_api_url")
                
        # 发布配置更新事件
        await event_bus.publish("live2d_config_updated", {
            "updated_fields": updated_fields,
            "config": config_updates
        })
        
        return {
            "status": "success", 
            "updated_fields": updated_fields,
            "message": f"已更新 {len(updated_fields)} 个配置项"
        }
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.get("/config", response_model=Live2DConfigResponse)
async def get_config():
    """获取当前Live2D配置"""
    try:
        return Live2DConfigResponse(
            enabled=live2d_widget is not None,
            model_path=live2d_widget.model_path if live2d_widget else None,
            scale=live2d_widget.scale if live2d_widget else 1.0,
            offset_x=live2d_widget.model_offset_x if live2d_widget else 1050,
            offset_y=live2d_widget.model_offset_y if live2d_widget else 600,
            tts_enabled=audio_adapter.tts_enabled if audio_adapter else False,
            asr_enabled=audio_adapter.asr_enabled if audio_adapter else False,
            tts_api_url=audio_adapter.tts_api_url if audio_adapter else "http://127.0.0.1:8000/voice/speak",
            asr_api_url=audio_adapter.asr_api_url if audio_adapter else "http://127.0.0.1:8000/voice/transcribe",
            emotion_analysis=emotion_handler.enabled if emotion_handler else False,
            lip_sync_enabled=live2d_widget.lip_sync_thread is not None if live2d_widget else False
        )
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.get("/models/list")
async def list_models():
    """获取可用的Live2D模型列表"""
    try:
        model_dirs = ["models", "live2d_module/models"]
        models = []
        
        for model_dir in model_dirs:
            dir_path = Path(model_dir)
            if dir_path.exists():
                for file in dir_path.glob("*.model3.json"):
                    models.append({
                        "name": file.stem,
                        "path": str(file),
                        "size": file.stat().st_size if file.exists() else 0,
                        "modified": file.stat().st_mtime if file.exists() else 0
                    })
        
        return {
            "status": "success",
            "models": models,
            "count": len(models)
        }
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.post("/model/load")
async def load_model(model_path: str):
    """加载Live2D模型"""
    if not live2d_widget:
        raise HTTPException(status_code=400, detail="Live2D控件未初始化")
        
    try:
        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            raise HTTPException(status_code=400, detail="模型文件不存在")
        
        # 加载模型
        if live2d_widget.model:
            # 先卸载当前模型
            live2d_widget.model = None
        
        # 创建新模型实例
        import live2d.v3 as live2d
        live2d_widget.model = live2d.LAppModel()
        live2d_widget.model.LoadModelJson(model_path)
        live2d_widget.model_path = model_path
        
        # 重新设置模型参数
        live2d_widget.model.SetScale(live2d_widget.scale)
        
        # 设置模型位置
        canvas_w, canvas_h = live2d_widget.model.GetCanvasSize()
        live2d_widget.model.SetOffset(
            (live2d_widget.model_offset_x - canvas_w / 2) / (live2d_widget.screen_size.height() / 2),
            (-live2d_widget.model_offset_y + canvas_h / 2) / (live2d_widget.screen_size.height() / 2)
        )
        
        # 重新初始化动作列表
        live2d_widget.setup_motion_list()
        
        # 发布模型加载事件
        await event_bus.publish("live2d_model_loaded", {
            "model_path": model_path
        })
        
        return {
            "status": "success",
            "model_path": model_path,
            "message": "模型加载成功"
        }
        
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载模型失败: {str(e)}")

@router.get("/events/subscribe")
async def subscribe_events():
    """订阅Live2D事件（WebSocket端点）"""
    # 这个端点将在WebSocket实现中使用
    return {
        "status": "info",
        "message": "请使用WebSocket连接 /ws/live2d-events 订阅事件"
    }

# 事件处理函数
async def on_ai_response_start(data=None):
    """AI响应开始事件处理"""
    if emotion_handler:
        await emotion_handler._on_ai_response_start(data)

async def on_ai_text_chunk(data):
    """AI文本块事件处理"""
    if emotion_handler:
        await emotion_handler._on_ai_text_chunk(data)

async def on_ai_response_end(data=None):
    """AI响应结束事件处理"""
    if emotion_handler:
        await emotion_handler._on_ai_response_end(data)

# 初始化事件订阅
def setup_event_subscriptions():
    """设置事件订阅"""
    event_bus.subscribe("ai_response_start", on_ai_response_start)
    event_bus.subscribe("ai_text_chunk", on_ai_text_chunk)
    event_bus.subscribe("ai_response_end", on_ai_response_end)
    logger.info("Live2D事件订阅已设置")