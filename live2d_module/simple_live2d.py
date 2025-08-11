"""
简化版Live2D模块 - 无需外部依赖
仅提供事件系统和基本功能框架
"""

import os
import sys
import json
import logging
import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class Live2DEventType(Enum):
    """Live2D事件类型"""
    MODEL_LOAD = "model_load"
    EMOTION_CHANGE = "emotion_change"
    MOTION_PLAY = "motion_play"
    LIP_SYNC = "lip_sync"
    AUDIO_PLAY = "audio_play"
    STATE_CHANGE = "state_change"

class Live2DEvent:
    """Live2D事件"""
    def __init__(self, event_type: Live2DEventType, data: Dict[str, Any] = None):
        self.type = event_type
        self.data = data or {}
        self.timestamp = datetime.now()
        self.id = f"{event_type.value}_{int(time.time() * 1000)}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }

class SimpleEventBus:
    """简化版事件总线"""
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Live2DEvent] = []
        self.max_history = 1000
        self._lock = threading.Lock()
        
    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        with self._lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
        logger.info(f"订阅事件: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        with self._lock:
            if event_type in self.subscribers:
                try:
                    self.subscribers[event_type].remove(callback)
                    logger.info(f"取消订阅事件: {event_type}")
                except ValueError:
                    pass
    
    def publish(self, event_type: str, event: Live2DEvent):
        """发布事件"""
        with self._lock:
            # 记录事件历史
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
            
            # 通知订阅者
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"事件回调失败: {e}")
        
        logger.debug(f"发布事件: {event_type} - {event.id}")
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Live2DEvent]:
        """获取事件历史"""
        with self._lock:
            if event_type:
                events = [e for e in self.event_history if e.type.value == event_type]
            else:
                events = self.event_history.copy()
            
            return events[-limit:] if limit else events

class SimpleEmotionAnalyzer:
    """简化版情绪分析器"""
    def __init__(self):
        self.emotion_keywords = {
            "开心": ["开心", "高兴", "快乐", "兴奋", "愉快", "哈哈", "😊", "😄", "🎉"],
            "生气": ["生气", "愤怒", "气愤", "恼火", "讨厌", "😠", "😡"],
            "伤心": ["伤心", "难过", "悲伤", "失望", "哭", "😢", "😭"],
            "惊讶": ["惊讶", "吃惊", "意外", "震惊", "哇", "😮", "😲"],
            "害羞": ["害羞", "不好意思", "尴尬", "脸红", "😳", "🙈"],
            "害怕": ["害怕", "恐惧", "担心", "紧张", "😨", "😰"]
        }
    
    def analyze_emotion(self, text: str) -> tuple[str, float]:
        """分析文本情绪"""
        if not text or not text.strip():
            return "neutral", 1.0
        
        text = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            best_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[best_emotion] / len(self.emotion_keywords[best_emotion])
            return best_emotion, min(confidence, 1.0)
        
        return "neutral", 0.5

class SimpleAudioManager:
    """简化版音频管理器"""
    def __init__(self):
        self.cache_dir = Path("live2d_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.audio_cache = {}
        
    def get_cached_audio(self, text: str) -> Optional[str]:
        """获取缓存的音频"""
        cache_key = hash(text)
        return self.audio_cache.get(cache_key)
    
    def cache_audio(self, text: str, audio_path: str):
        """缓存音频"""
        cache_key = hash(text)
        self.audio_cache[cache_key] = audio_path
        logger.info(f"缓存音频: {text[:50]}...")
    
    def cleanup_cache(self, max_age_hours: int = 24):
        """清理过期缓存"""
        # 简化版本，只记录日志
        logger.info(f"清理音频缓存 (最大时长: {max_age_hours}小时)")

class SimpleLive2DManager:
    """简化版Live2D管理器"""
    def __init__(self):
        self.event_bus = SimpleEventBus()
        self.emotion_analyzer = SimpleEmotionAnalyzer()
        self.audio_manager = SimpleAudioManager()
        
        # 状态管理
        self.is_initialized = False
        self.current_emotion = "neutral"
        self.current_motion = "idle"
        self.model_loaded = False
        
        # 模型路径
        self.model_path = "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.model3.json"
        
        logger.info("简化版Live2D管理器已初始化")
    
    def initialize(self) -> bool:
        """初始化Live2D管理器"""
        try:
            # 检查模型文件
            if os.path.exists(self.model_path):
                self.model_loaded = True
                event = Live2DEvent(Live2DEventType.MODEL_LOAD, {
                    "model_path": self.model_path,
                    "success": True
                })
                self.event_bus.publish("model_load", event)
                logger.info("Live2D模型加载成功")
            else:
                logger.warning(f"Live2D模型文件不存在: {self.model_path}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Live2D初始化失败: {e}")
            return False
    
    def analyze_emotion(self, text: str) -> tuple[str, float]:
        """分析情绪"""
        emotion, confidence = self.emotion_analyzer.analyze_emotion(text)
        
        if emotion != self.current_emotion:
            self.current_emotion = emotion
            event = Live2DEvent(Live2DEventType.EMOTION_CHANGE, {
                "emotion": emotion,
                "confidence": confidence,
                "text": text[:100]  # 只保存前100个字符
            })
            self.event_bus.publish("emotion_change", event)
        
        return emotion, confidence
    
    def play_motion(self, motion_name: str) -> bool:
        """播放动作"""
        try:
            self.current_motion = motion_name
            event = Live2DEvent(Live2DEventType.MOTION_PLAY, {
                "motion_name": motion_name,
                "success": True
            })
            self.event_bus.publish("motion_play", event)
            logger.info(f"播放动作: {motion_name}")
            return True
        except Exception as e:
            logger.error(f"播放动作失败: {e}")
            return False
    
    def process_ai_response(self, text: str):
        """处理AI响应"""
        # 分析情绪
        emotion, confidence = self.analyze_emotion(text)
        
        # 根据情绪播放动作
        motion_mapping = {
            "开心": "Hiyori_m01",
            "生气": "Hiyori_m05", 
            "伤心": "Hiyori_m03",
            "惊讶": "Hiyori_m02",
            "害羞": "Hiyori_m07",
            "害怕": "Hiyori_m09"
        }
        
        if emotion in motion_mapping:
            self.play_motion(motion_mapping[emotion])
        
        logger.info(f"处理AI响应: 情绪={emotion}, 置信度={confidence:.2f}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "initialized": self.is_initialized,
            "model_loaded": self.model_loaded,
            "current_emotion": self.current_emotion,
            "current_motion": self.current_motion,
            "event_history_count": len(self.event_bus.event_history),
            "model_path": self.model_path
        }

# 全局实例
live2d_manager = SimpleLive2DManager()

def init_live2d() -> bool:
    """初始化Live2D系统"""
    return live2d_manager.initialize()

def process_ai_response(text: str):
    """处理AI响应"""
    live2d_manager.process_ai_response(text)

def get_live2d_status() -> Dict[str, Any]:
    """获取Live2D状态"""
    return live2d_manager.get_status()

# 便利函数
def create_ai_response_event(character: str, text: str) -> Live2DEvent:
    """创建AI响应事件"""
    return Live2DEvent(Live2DEventType.STATE_CHANGE, {
        "character": character,
        "text": text,
        "type": "ai_response"
    })

if __name__ == "__main__":
    # 测试简化版Live2D管理器
    print("测试简化版Live2D管理器...")
    
    # 初始化
    if init_live2d():
        print("✅ Live2D初始化成功")
    else:
        print("❌ Live2D初始化失败")
    
    # 测试情绪分析
    test_texts = [
        "今天真开心！",
        "这让我很生气。",
        "我好难过啊。",
        "哇！太惊讶了！",
        "有点害羞...",
        "我好害怕..."
    ]
    
    for text in test_texts:
        emotion, confidence = live2d_manager.analyze_emotion(text)
        print(f"文本: {text} -> 情绪: {emotion} (置信度: {confidence:.2f})")
    
    # 显示状态
    status = get_live2d_status()
    print(f"\nLive2D状态: {status}")