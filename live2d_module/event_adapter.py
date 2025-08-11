#!/usr/bin/env python3
"""
Live2D事件总线适配器
为Live2D模块提供事件通信机制
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("live2d_events")

class EventType(Enum):
    """事件类型枚举"""
    AI_RESPONSE_START = "ai_response_start"
    AI_TEXT_CHUNK = "ai_text_chunk"
    AI_RESPONSE_END = "ai_response_end"
    LIVE2D_EMOTION_DETECTED = "live2d_emotion_detected"
    LIVE2D_EMOTION_TRIGGERED = "live2d_emotion_triggered"
    LIVE2D_EMOTION_ANALYZED = "live2d_emotion_analyzed"
    LIVE2D_LIP_SYNC_STARTED = "live2d_lip_sync_started"
    LIVE2D_LIP_SYNC_STOPPED = "live2d_lip_sync_stopped"
    LIVE2D_MODEL_LOADED = "live2d_model_loaded"
    LIVE2D_CONFIG_UPDATED = "live2d_config_updated"
    TTS_STARTED = "tts_started"
    TTS_COMPLETED = "tts_completed"
    ASR_STARTED = "asr_started"
    ASR_COMPLETED = "asr_completed"

@dataclass
class Event:
    """事件数据结构"""
    type: EventType
    data: Dict[str, Any]
    timestamp: float
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "session_id": self.session_id
        }

class EventBus:
    """事件总线 - 简化版本，支持异步事件处理"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000  # 最大历史记录数
        self.logger = logging.getLogger("event_bus")
        
    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"订阅事件: {event_type}")
        
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅事件"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                self.logger.debug(f"取消订阅事件: {event_type}")
            except ValueError:
                pass  # 回调函数不存在于列表中
                
    async def publish(self, event_type: str, data: Dict[str, Any], session_id: Optional[str] = None):
        """发布事件"""
        try:
            # 创建事件对象
            event = Event(
                type=EventType(event_type),
                data=data,
                timestamp=asyncio.get_event_loop().time(),
                session_id=session_id
            )
            
            # 添加到历史记录
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
            
            # 异步调用订阅者
            if event_type in self.subscribers:
                tasks = []
                for callback in self.subscribers[event_type]:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(callback(data))
                    else:
                        # 如果是同步函数，在线程池中执行
                        tasks.append(asyncio.get_event_loop().run_in_executor(None, callback, data))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            
            self.logger.debug(f"发布事件: {event_type}, 数据: {data}")
            
        except Exception as e:
            self.logger.error(f"发布事件失败: {e}")
            
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取事件历史"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.type.value == event_type]
        
        # 返回最近的limit个事件
        recent_events = events[-limit:]
        return [event.to_dict() for event in recent_events]
    
    def clear_history(self):
        """清空事件历史"""
        self.event_history.clear()
        self.logger.info("事件历史已清空")
    
    def get_subscriber_count(self, event_type: str) -> int:
        """获取事件订阅者数量"""
        return len(self.subscribers.get(event_type, []))
    
    def get_all_event_types(self) -> List[str]:
        """获取所有已注册的事件类型"""
        return list(self.subscribers.keys())

# 全局事件总线实例
event_bus = EventBus()

# 便捷函数
def subscribe(event_type: str, callback: Callable):
    """便捷的订阅函数"""
    event_bus.subscribe(event_type, callback)

def unsubscribe(event_type: str, callback: Callable):
    """便捷的取消订阅函数"""
    event_bus.unsubscribe(event_type, callback)

async def publish(event_type: str, data: Dict[str, Any], session_id: Optional[str] = None):
    """便捷的发布函数"""
    await event_bus.publish(event_type, data, session_id)

def get_event_history(event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """便捷的获取历史函数"""
    return event_bus.get_event_history(event_type, limit)

# 事件工具函数
def create_ai_response_event(session_id: str, message: str) -> Dict[str, Any]:
    """创建AI响应事件数据"""
    return {
        "session_id": session_id,
        "message": message,
        "timestamp": asyncio.get_event_loop().time()
    }

def create_emotion_event(emotion: str, intensity: float, text: str = "", session_id: str = None) -> Dict[str, Any]:
    """创建情绪事件数据"""
    return {
        "emotion": emotion,
        "intensity": intensity,
        "text": text,
        "session_id": session_id,
        "timestamp": asyncio.get_event_loop().time()
    }

def create_lip_sync_event(audio_path: str, intensity: float, duration: float = 0) -> Dict[str, Any]:
    """创建嘴型同步事件数据"""
    return {
        "audio_path": audio_path,
        "intensity": intensity,
        "duration": duration,
        "timestamp": asyncio.get_event_loop().time()
    }

def create_tts_event(text: str, audio_path: str, duration: float, success: bool = True) -> Dict[str, Any]:
    """创建TTS事件数据"""
    return {
        "text": text,
        "audio_path": audio_path,
        "duration": duration,
        "success": success,
        "timestamp": asyncio.get_event_loop().time()
    }

def create_asr_event(audio_path: str, text: str, confidence: float, success: bool = True) -> Dict[str, Any]:
    """创建ASR事件数据"""
    return {
        "audio_path": audio_path,
        "text": text,
        "confidence": confidence,
        "success": success,
        "timestamp": asyncio.get_event_loop().time()
    }

# 事件过滤器
class EventFilter:
    """事件过滤器"""
    
    def __init__(self):
        self.filters: Dict[str, Callable] = {}
    
    def add_filter(self, event_type: str, filter_func: Callable[[Dict[str, Any]], bool]):
        """添加事件过滤器"""
        self.filters[event_type] = filter_func
    
    def remove_filter(self, event_type: str):
        """移除事件过滤器"""
        if event_type in self.filters:
            del self.filters[event_type]
    
    def should_process(self, event_type: str, data: Dict[str, Any]) -> bool:
        """判断是否应该处理事件"""
        if event_type in self.filters:
            return self.filters[event_type](data)
        return True

# 全局事件过滤器
event_filter = EventFilter()

# 带过滤器的事件发布函数
async def publish_with_filter(event_type: str, data: Dict[str, Any], session_id: Optional[str] = None):
    """带过滤器的事件发布"""
    if event_filter.should_process(event_type, data):
        await event_bus.publish(event_type, data, session_id)
    else:
        logger.debug(f"事件被过滤器阻止: {event_type}")

# 初始化日志
logger.info("Live2D事件总线适配器已初始化")