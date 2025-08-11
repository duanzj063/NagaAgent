#!/usr/bin/env python3
"""
Live2D情绪处理器
为NagaAgent提供情绪分析和处理功能
"""

import logging
import re
import asyncio
from typing import Dict, List, Tuple, Any, Optional, Callable
import numpy as np

from .event_adapter import event_bus, create_emotion_event

logger = logging.getLogger("live2d_emotion")

class Live2DEmotionHandler:
    """Live2D情绪处理器 - 适配NagaAgent对话系统"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.emotion_keywords = self._load_emotion_keywords()
        self.current_emotion = "neutral"
        self.emotion_intensity = 1.0
        self.emotion_history = []
        self.max_history = 50
        
        # 情绪权重配置
        self.emotion_weights = self.config.get("emotion_weights", {
            "开心": 1.0,
            "生气": 1.2,
            "伤心": 1.1,
            "惊讶": 1.3,
            "害羞": 0.9,
            "害怕": 1.0
        })
        
        # 情绪持续配置
        self.emotion_duration = self.config.get("emotion_duration", {
            "开心": 2.0,
            "生气": 1.5,
            "伤心": 3.0,
            "惊讶": 1.0,
            "害羞": 2.5,
            "害怕": 2.0,
            "neutral": 1.0
        })
        
        # 订阅事件
        event_bus.subscribe("ai_response_start", self._on_ai_response_start)
        event_bus.subscribe("ai_text_chunk", self._on_ai_text_chunk)
        event_bus.subscribe("ai_response_end", self._on_ai_response_end)
        
        logger.info("Live2D情绪处理器初始化完成")
        
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """加载情绪关键词"""
        return {
            "开心": [
                "开心", "高兴", "快乐", "哈哈", "呵呵", "嘻嘻", "笑", 
                "😊", "🙂", "😄", "😃", "happy", "哈哈", "笑",
                "太好了", "棒极了", "太棒了", "完美", "优秀", "赞", "不错",
                "兴奋", "愉快", "欢乐", "欣喜", "喜悦", "满足", "欣慰"
            ],
            "生气": [
                "生气", "愤怒", "讨厌", "气死", "恼火", "怒", 
                "😠", "😡", "mad", "angry", "怒",
                "混蛋", "可恶", "烦死了", "气人", "气愤", "愤慨", "恼怒",
                "暴躁", "火大", "不爽", "郁闷", "窝火", "愤愤不平"
            ],
            "伤心": [
                "伤心", "难过", "悲伤", "哭", "难过", 
                "😢", "😭", "😞", "😔", "sad", "cry",
                "痛苦", "心痛", "心疼", "遗憾", "哀伤", "悲痛", "忧伤",
                "沮丧", "失落", "绝望", "痛苦", "哀愁", "悲戚"
            ],
            "惊讶": [
                "惊讶", "震惊", "哇", "天啊", "不会吧", 
                "😮", "😲", "😯", "wow", "amazing",
                "真的吗", "难以置信", "太意外了", "吃惊", "诧异", "惊奇",
                "意外", "惊奇", "震惊", "惊愕", "目瞪口呆", "大吃一惊"
            ],
            "害羞": [
                "害羞", "不好意思", "脸红", "羞涩", 
                "😳", "😊", "shy", "embarrassed",
                "羞羞", "不好意思", "难为情", "腼腆", "忸怩", "局促",
                "脸红", "羞怯", "羞赧", "不好意思", "难为情"
            ],
            "害怕": [
                "害怕", "恐惧", "怕", "吓人", 
                "😨", "😰", "scared", "afraid",
                "恐怖", "可怕", "吓死了", "恐惧", "畏惧", "恐慌", "忧虑",
                "担心", "忧虑", "不安", "紧张", "惊恐", "胆怯", "畏惧"
            ]
        }
        
    async def _on_ai_response_start(self, data=None):
        """AI响应开始事件"""
        self.current_emotion = "neutral"
        self.emotion_intensity = 1.0
        
    async def _on_ai_text_chunk(self, data):
        """AI文本块事件 - 实时情绪分析"""
        if not self.enabled:
            return
            
        text = data.get("text", "")
        session_id = data.get("session_id")
        
        if text.strip():
            emotion, intensity = self.analyze_emotion(text)
            
            # 更新当前情绪
            if emotion != "neutral" and emotion != self.current_emotion:
                self.current_emotion = emotion
                self.emotion_intensity = intensity
                
                # 发布情绪事件
                emotion_event = create_emotion_event(emotion, intensity, text, session_id)
                await event_bus.publish("live2d_emotion_detected", emotion_event)
                
    async def _on_ai_response_end(self, data=None):
        """AI响应结束事件"""
        # 重置到中性情绪
        await asyncio.sleep(self.emotion_duration.get(self.current_emotion, 1.0))
        self.current_emotion = "neutral"
        self.emotion_intensity = 1.0
        
    def analyze_emotion(self, text: str) -> Tuple[str, float]:
        """分析文本情绪"""
        if not text.strip():
            return "neutral", 1.0
            
        text = text.lower()
        emotion_scores = {}
        
        # 计算每种情绪的得分
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                # 使用正则表达式进行模糊匹配
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(text)
                match_count = len(matches)
                
                if match_count > 0:
                    score += match_count
                    matched_keywords.extend([keyword] * match_count)
            
            if score > 0:
                # 应用情绪权重
                weight = self.emotion_weights.get(emotion, 1.0)
                emotion_scores[emotion] = score * weight
                
        # 如果没有检测到情绪，返回中性
        if not emotion_scores:
            return "neutral", 1.0
            
        # 找到得分最高的情绪
        max_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[max_emotion]
        
        # 计算强度（基于得分和权重）
        base_intensity = min(max_score / 3.0, 2.0)  # 基础强度
        weight_multiplier = self.emotion_weights.get(max_emotion, 1.0)
        intensity = base_intensity * weight_multiplier
        
        # 记录情绪历史
        self._record_emotion(max_emotion, intensity, text)
        
        return max_emotion, intensity
        
    def _record_emotion(self, emotion: str, intensity: float, text: str):
        """记录情绪历史"""
        import time
        emotion_record = {
            "emotion": emotion,
            "intensity": intensity,
            "text": text,
            "timestamp": time.time()
        }
        
        self.emotion_history.append(emotion_record)
        
        # 保持历史记录在限制范围内
        if len(self.emotion_history) > self.max_history:
            self.emotion_history.pop(0)
            
    def get_emotion_statistics(self) -> Dict[str, Any]:
        """获取情绪统计信息"""
        if not self.emotion_history:
            return {"total": 0, "emotions": {}}
            
        emotion_counts = {}
        total_intensity = {}
        
        for record in self.emotion_history:
            emotion = record["emotion"]
            intensity = record["intensity"]
            
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_intensity[emotion] = total_intensity.get(emotion, 0) + intensity
            
        # 计算平均强度
        avg_intensity = {}
        for emotion in emotion_counts:
            avg_intensity[emotion] = total_intensity[emotion] / emotion_counts[emotion]
            
        return {
            "total": len(self.emotion_history),
            "emotions": {
                emotion: {
                    "count": count,
                    "avg_intensity": avg_intensity[emotion],
                    "percentage": (count / len(self.emotion_history)) * 100
                }
                for emotion, count in emotion_counts.items()
            }
        }
        
    def get_current_emotion(self) -> Tuple[str, float]:
        """获取当前情绪"""
        return self.current_emotion, self.emotion_intensity
        
    def set_enabled(self, enabled: bool):
        """启用/禁用情绪处理"""
        self.enabled = enabled
        logger.info(f"情绪处理{'启用' if enabled else '禁用'}")
        
    def add_emotion_keywords(self, emotion: str, keywords: List[str]):
        """添加情绪关键词"""
        if emotion in self.emotion_keywords:
            self.emotion_keywords[emotion].extend(keywords)
        else:
            self.emotion_keywords[emotion] = keywords
        logger.info(f"已添加 {len(keywords)} 个关键词到情绪 '{emotion}'")
        
    def remove_emotion_keywords(self, emotion: str, keywords: List[str]):
        """移除情绪关键词"""
        if emotion in self.emotion_keywords:
            for keyword in keywords:
                if keyword in self.emotion_keywords[emotion]:
                    self.emotion_keywords[emotion].remove(keyword)
            logger.info(f"已从情绪 '{emotion}' 移除 {len(keywords)} 个关键词")
            
    def set_emotion_weight(self, emotion: str, weight: float):
        """设置情绪权重"""
        self.emotion_weights[emotion] = weight
        logger.info(f"已设置情绪 '{emotion}' 的权重为 {weight}")
        
    def set_emotion_duration(self, emotion: str, duration: float):
        """设置情绪持续时间"""
        self.emotion_duration[emotion] = duration
        logger.info(f"已设置情绪 '{emotion}' 的持续时间为 {duration} 秒")
        
    def clear_history(self):
        """清空情绪历史"""
        self.emotion_history.clear()
        logger.info("情绪历史已清空")
        
    def get_recent_emotions(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的情绪记录"""
        return self.emotion_history[-count:] if self.emotion_history else []
        
    def analyze_text_emotions(self, text: str) -> List[Dict[str, Any]]:
        """分析文本中的所有情绪"""
        emotions = []
        text_lower = text.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            matched_keywords = []
            for keyword in keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(text_lower)
                if matches:
                    matched_keywords.extend([keyword] * len(matches))
            
            if matched_keywords:
                score = len(matched_keywords)
                weight = self.emotion_weights.get(emotion, 1.0)
                intensity = min(score / 3.0, 2.0) * weight
                
                emotions.append({
                    "emotion": emotion,
                    "intensity": intensity,
                    "score": score,
                    "matched_keywords": list(set(matched_keywords)),
                    "weight": weight
                })
        
        # 按强度排序
        emotions.sort(key=lambda x: x["intensity"], reverse=True)
        return emotions
        
    def get_dominant_emotion(self, text: str) -> Optional[Dict[str, Any]]:
        """获取文本中的主导情绪"""
        emotions = self.analyze_text_emotions(text)
        return emotions[0] if emotions else None
        
    def is_emotional_text(self, text: str, threshold: float = 0.5) -> bool:
        """判断文本是否包含情绪"""
        emotions = self.analyze_text_emotions(text)
        return any(e["intensity"] > threshold for e in emotions)
        
    def get_emotion_transition(self) -> List[Dict[str, Any]]:
        """获取情绪转换历史"""
        if len(self.emotion_history) < 2:
            return []
            
        transitions = []
        for i in range(1, len(self.emotion_history)):
            prev = self.emotion_history[i-1]
            curr = self.emotion_history[i]
            
            if prev["emotion"] != curr["emotion"]:
                transitions.append({
                    "from_emotion": prev["emotion"],
                    "to_emotion": curr["emotion"],
                    "from_intensity": prev["intensity"],
                    "to_intensity": curr["intensity"],
                    "timestamp": curr["timestamp"],
                    "text": curr["text"]
                })
        
        return transitions