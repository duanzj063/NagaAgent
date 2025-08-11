# My-Neuro前端数字人移植到NagaAgent项目指南

## 项目分析概述

### 源项目（My-Neuro）特点 - 修正版
- **前端技术**: PyQt5 + OpenGL + Live2D Cubism SDK for Python
- **核心功能**: Live2D数字人渲染、情绪动作同步、嘴型同步、语音交互
- **架构**: 单一Python应用，事件驱动设计
- **通信方式**: 内部事件总线，无WebSocket通信
- **已实现功能**: 完整的Live2D控件、嘴型同步、情绪处理

### 目标项目（NagaAgent）特点
- **技术栈**: Python + PyQt5 + FastAPI
- **现有功能**: 文本对话、语音合成、API服务、工具调用
- **架构**: 模块化设计，支持插件扩展
- **UI系统**: 基于PyQt5的现代化界面

## 移植方案设计 - 修正版

### 方案一：Python模块集成（推荐）
将My-Neuro的Live2D相关模块直接集成到NagaAgent中，保持Python技术栈。

### 方案二：独立进程模式
Live2D作为独立进程运行，通过API与NagaAgent通信。

### 方案三：Web版本移植
将Live2D移植到Web版本，通过浏览器访问。

## 详细移植步骤 - 修正版

### 步骤1：项目结构规划

在NagaAgent项目中创建新的Live2D模块目录：

```
NagaAgent/
├── live2d_module/                # 新增Live2D模块
│   ├── __init__.py
│   ├── live2d_widget.py          # Live2D主控件（基于My-Neuro）
│   ├── lip_sync_thread.py        # 嘴型同步线程
│   ├── emotion_handler.py        # 情绪处理器
│   ├── audio_integration.py      # 音频集成适配器
│   ├── event_adapter.py          # 事件总线适配器
│   ├── models/                   # Live2D模型文件
│   │   ├── hiyori_pro_mic.model3.json
│   │   ├── hiyori_pro_mic.moc3
│   │   └── motions/               # 动作文件
│   └── config/                   # 配置文件
│       └── live2d_config.json
├── ui/                           # 现有UI模块
│   ├── components/               # UI组件
│   └── live2d_settings.py        # Live2D设置界面
├── apiserver/                    # API服务器
│   ├── live2d_api.py            # Live2D相关API
│   └── audio_api.py             # 音频API适配
├── config.py                     # 主配置文件
└── main.py                       # 主程序
```

### 步骤2：核心文件移植 - Python版本

#### 2.1 复制My-Neuro的核心Live2D文件

**复制Live2D控件实现**：
```bash
# 创建目标目录
mkdir -p NagaAgent/live2d_module

# 复制My-Neuro的Live2D核心文件
cp /mnt/d/code/pythonWork/my-neuro/py-my-neuro/UI/live2d_model.py NagaAgent/live2d_module/
cp /mnt/d/code/pythonWork/my-neuro/py-my-neuro/UI/lip_sync_thread.py NagaAgent/live2d_module/
cp /mnt/d/code/pythonWork/my-neuro/py-my-neuro/UI/simple_event_bus.py NagaAgent/live2d_module/event_adapter.py

# 复制Live2D模型文件
cp -r /mnt/d/code/pythonWork/my-neuro/py-my-neuro/UI/2D/* NagaAgent/live2d_module/models/
```

#### 2.2 修改Live2D控件适配NagaAgent

**修改Live2D主控件**：
```python
# NagaAgent/live2d_module/live2d_widget.py
import os
import sys
import time
import win32gui
import win32con
import OpenGL.GL as gl
import numpy as np
import logging
import asyncio
from PyQt5.QtCore import QTimerEvent, Qt, pyqtSignal, QThread, QEvent, pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtGui import QMouseEvent, QCursor, QSurfaceFormat
from PyQt5.QtWidgets import QOpenGLWidget, QApplication
from PyQt5.QtGui import QGuiApplication

from .lip_sync_thread import LipSyncThread
from .event_adapter import event_bus  # 使用适配后的事件总线
import live2d.v3 as live2d
from live2d.v3 import StandardParams

logger = logging.getLogger("live2d_widget")

class NagaLive2DWidget(QOpenGLWidget):
    """NagaAgent Live2D数字人控件（基于My-Neuro实现）"""

    # 定义信号
    model_clicked = pyqtSignal(float, float)
    model_dragged = pyqtSignal(float, float)
    model_loaded = pyqtSignal()
    emotion_triggered = pyqtSignal(str, float)  # 情绪触发信号

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        
        # 配置初始化
        self.config = config or {}
        self.model_path = self.config.get("model_path", "models/hiyori_pro_mic.model3.json")
        self.scale = self.config.get("scale", 1.0)
        
        # 窗口设置（保持My-Neuro的透明窗口特性）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 设置分层窗口和穿透属性
        self.hwnd = int(self.winId())
        win32gui.SetWindowLong(
            self.hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE) |
            win32con.WS_EX_LAYERED |
            win32con.WS_EX_TRANSPARENT
        )
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 255, win32con.LWA_ALPHA)
        
        # 模型位置和状态
        self.model_offset_x = self.config.get("offset_x", 1050)
        self.model_offset_y = self.config.get("offset_y", 600)
        self.isInModelArea = False
        self.isClickingModel = False
        self.screen_size = QGuiApplication.primaryScreen().geometry()
        
        # 设置窗口大小
        self.resize(self.screen_size.width()+1, self.screen_size.height())
        self.move(
            (self.screen_size.width()-self.frameGeometry().width())//2,
            (self.screen_size.height()-self.frameGeometry().height())//2
        )
        
        # Live2D相关
        self.model = None
        self.is_talking = False
        self.is_listening = False
        self.current_expression = ""
        self.lip_sync_intensity = 3.0
        self.lip_sync_thread = None
        
        # 动作相关
        self.tapbody_motions = []
        self.current_tapbody_idx = 0
        self.is_playing_tapbody = False
        self.motion_group_name = None
        
        logger.info("NagaAgent Live2D控件初始化完成")
        
    def initializeGL(self):
        """初始化OpenGL和Live2D模型"""
        try:
            self.makeCurrent()
            
            # 初始化Live2D
            if hasattr(live2d, 'LIVE2D_VERSION') and live2d.LIVE2D_VERSION == 3:
                try:
                    live2d.glInit()
                    logger.info("Live2D glInit 成功")
                except Exception as e:
                    logger.error(f"Live2D glInit 失败: {e}")
            
            # 创建模型实例
            self.model = live2d.LAppModel()
            logger.info("Live2D 模型实例创建成功")
            
            # 加载模型
            model_loaded = False
            if os.path.exists(self.model_path):
                try:
                    self.model.LoadModelJson(self.model_path)
                    logger.info(f"从配置路径加载模型成功: {self.model_path}")
                    model_loaded = True
                except Exception as e:
                    logger.error(f"从配置路径加载模型失败: {self.model_path}, 错误: {e}")
            
            if not model_loaded:
                # 自动搜索模型文件
                search_dirs = ["models", "."]
                for search_dir in search_dirs:
                    if not os.path.exists(search_dir):
                        continue
                    
                    try:
                        for file in os.listdir(search_dir):
                            if file.endswith('.model3.json'):
                                model_path = os.path.join(search_dir, file)
                                try:
                                    self.model.LoadModelJson(model_path)
                                    logger.info(f"自动发现并加载模型: {model_path}")
                                    model_loaded = True
                                    break
                                except Exception as e:
                                    logger.error(f"加载模型失败: {model_path}, 错误: {e}")
                        
                        if model_loaded:
                            break
                    except Exception as e:
                        logger.error(f"搜索目录失败: {search_dir}, 错误: {e}")
            
            # 设置模型参数
            if self.model:
                self.model.SetScale(self.scale)
                
                # 设置模型位置
                canvas_w, canvas_h = self.model.GetCanvasSize()
                self.model.SetOffset(
                    (self.model_offset_x - canvas_w / 2) / (self.screen_size.height() / 2),
                    (-self.model_offset_y + canvas_h / 2) / (self.screen_size.height() / 2)
                )
                logger.info(f"设置模型偏移: x={self.model_offset_x}, y={self.model_offset_y}")
            
            # 初始化动作列表
            self.setup_motion_list()
            
            # 启动渲染定时器
            self.startTimer(int(1000 / 60))  # 60FPS
            
            # 发送模型加载完成信号
            self.model_loaded.emit()
            logger.info("Live2D模型初始化完成")
            
        except Exception as e:
            logger.error(f"初始化Live2D模型失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
    def setup_motion_list(self):
        """初始化动作列表"""
        if self.model:
            try:
                motions = self.model.GetMotionGroups()
                
                # 确定动作组名称
                self.motion_group_name = None
                if "TapBody" in motions:
                    self.motion_group_name = "TapBody"
                elif "Tap" in motions:
                    self.motion_group_name = "Tap"
                else:
                    print("未找到TapBody或Tap动作组")
                    return
                
                # 获取动作数量
                motion_count = motions[self.motion_group_name]
                self.tapbody_motions = list(range(motion_count))
                
                print(f"=== Live2D {self.motion_group_name}动作列表 ===")
                print(f"{self.motion_group_name}组共 {motion_count} 个动作")
                
            except Exception as e:
                logger.error(f"获取动作列表失败: {e}")
                
    def trigger_emotion(self, emotion_name, intensity=1.0):
        """触发情绪动作（适配NagaAgent）"""
        try:
            if self.model:
                # 根据情绪名称映射到动作
                emotion_map = {
                    "开心": "TapBody",
                    "生气": "TapBody", 
                    "伤心": "TapBody",
                    "惊讶": "TapBody",
                    "害羞": "TapBody"
                }
                
                motion_group = emotion_map.get(emotion_name, "TapBody")
                
                # 随机选择一个动作
                if self.tapbody_motions:
                    motion_idx = np.random.choice(self.tapbody_motions)
                    self.model.StartMotion(motion_group, motion_idx, 3)
                    self.is_playing_tapbody = True
                    
                # 设置表情
                if emotion_name in ["开心", "生气", "伤心", "惊讶", "害羞"]:
                    self.set_expression(emotion_name)
                
                # 发送情绪触发信号
                self.emotion_triggered.emit(emotion_name, intensity)
                
                logger.info(f"触发情绪: {emotion_name}, 强度: {intensity}")
                
        except Exception as e:
            logger.error(f"触发情绪失败: {e}")
            
    def start_lip_sync(self, audio_path):
        """开始嘴型同步"""
        if not audio_path or not os.path.exists(audio_path):
            logger.error(f"音频文件不存在: {audio_path}")
            return False
            
        # 停止之前的嘴型同步
        self.stop_lip_sync()
        
        try:
            # 创建并启动嘴型同步线程
            self.lip_sync_thread = LipSyncThread(audio_path, event_bus, self.lip_sync_intensity)
            
            # 连接信号
            self.lip_sync_thread.update_signal.connect(self._update_mouth)
            self.lip_sync_thread.finished_signal.connect(self.on_lip_sync_finished)
            self.lip_sync_thread.error_signal.connect(self.on_lip_sync_error)
            
            # 启动线程
            self.lip_sync_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"启动嘴型同步失败: {e}")
            return False
            
    def stop_lip_sync(self):
        """停止嘴型同步"""
        if self.lip_sync_thread:
            self.lip_sync_thread.stop()
            self.lip_sync_thread = None
            
            # 重置嘴部参数
            if self.model:
                try:
                    self.model.SetParameterValue(StandardParams.ParamMouthOpenY, 0.0)
                except Exception as e:
                    logger.error(f"重置嘴部参数失败: {e}")
                    
    @pyqtSlot(float)
    def _update_mouth(self, value):
        """更新嘴型参数"""
        if self.model:
            try:
                from live2d.v3 import StandardParams
                self.model.SetParameterValue(StandardParams.ParamMouthOpenY, value)
            except:
                pass
            
            try:
                self.model.SetParameterValue("PARAM_MOUTH_OPEN_Y", value)
            except:
                pass
                
    def set_expression(self, expression):
        """设置表情"""
        if self.model:
            try:
                self.model.SetExpression(expression)
                self.current_expression = expression
                logger.debug(f"设置表情: {expression}")
            except Exception as e:
                logger.error(f"设置表情失败: {e}")
                
    def paintGL(self):
        """渲染模型"""
        try:
            live2d.clearBuffer()
            
            if self.model:
                # 更新模型
                self.model.Update()
                
                # 处理动作状态
                if self.model.IsMotionFinished():
                    if self.is_playing_tapbody:
                        self.is_playing_tapbody = False
                        
                    # 根据状态播放对应动作
                    if self.is_talking:
                        self.model.StartMotion("Talk", 0, 2)
                    elif self.is_listening:
                        self.model.StartMotion("Listen", 0, 2)
                    else:
                        self.model.StartMotion("Idle", 0, 1)
                
                # 绘制模型
                self.model.Draw()
                
        except Exception as e:
            logger.error(f"渲染模型失败: {e}")
            
    def timerEvent(self, event):
        """定时器事件"""
        if not self.isVisible():
            return
            
        try:
            # 更新窗口穿透属性
            current_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            local_x, local_y = QCursor.pos().x() - self.x(), QCursor.pos().y() - self.y()
            
            in_model_area = self.check_in_model_area(local_x, local_y)
            
            if in_model_area:
                new_style = current_style & ~win32con.WS_EX_TRANSPARENT
                self.isInModelArea = True
            else:
                new_style = current_style | win32con.WS_EX_TRANSPARENT
                self.isInModelArea = False
                
            if new_style != current_style:
                win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, new_style)
                win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 255, win32con.LWA_ALPHA)
                
            # 请求重绘
            self.update()
            
        except Exception as e:
            logger.error(f"定时器事件处理失败: {e}")
            
    def check_in_model_area(self, x, y):
        """检查坐标是否在模型区域内"""
        try:
            systemScale = QGuiApplication.primaryScreen().devicePixelRatio()
            gl_x = int(x * systemScale)
            gl_y = int((self.height() - y) * systemScale)
            
            if (gl_x < 0 or gl_y < 0 or
                gl_x >= self.width() * systemScale or
                gl_y >= self.height() * systemScale):
                return False
                
            alpha = gl.glReadPixels(gl_x, gl_y, 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)[3]
            return alpha > 50
            
        except Exception as e:
            logger.error(f"判断模型区域失败: {e}")
            return False
            
    def set_talking(self, is_talking):
        """设置说话状态"""
        self.is_talking = is_talking
        logger.debug(f"设置说话状态: {is_talking}")
        
    def set_listening(self, is_listening):
        """设置聆听状态"""
        self.is_listening = is_listening
        logger.debug(f"设置聆听状态: {is_listening}")
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            self.stop_lip_sync()
        except:
            pass
        super().closeEvent(event)
        
    def __del__(self):
        """析构函数"""
        self.stop_lip_sync()
```

#### 2.3 创建音频集成适配器

**创建音频处理模块**：
```python
# NagaAgent/live2d_module/audio_integration.py
import os
import tempfile
import logging
import requests
import aiohttp
from typing import Optional, Dict, Any
from .event_adapter import event_bus

logger = logging.getLogger("live2d_audio")

class Live2DAudioAdapter:
    """Live2D音频适配器 - 连接NagaAgent音频系统"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.tts_enabled = self.config.get("tts_enabled", True)
        self.asr_enabled = self.config.get("asr_enabled", True)
        
        # 远程服务配置
        self.tts_api_url = self.config.get("tts_api_url", "http://127.0.0.1:8000/voice/speak")
        self.asr_api_url = self.config.get("asr_api_url", "http://127.0.0.1:8000/voice/transcribe")
        
        # 本地TTS配置（如果有的话）
        self.local_tts_path = self.config.get("local_tts_path", None)
        
        logger.info("Live2D音频适配器初始化完成")
        
    async def text_to_speech(self, text: str, output_path: Optional[str] = None) -> str:
        """文本转语音，返回音频文件路径"""
        try:
            # 如果配置了本地TTS，优先使用
            if self.local_tts_path and os.path.exists(self.local_tts_path):
                return await self._local_tts(text, output_path)
            
            # 使用远程TTS API
            return await self._remote_tts(text, output_path)
            
        except Exception as e:
            logger.error(f"TTS转换失败: {e}")
            return None
            
    async def _local_tts(self, text: str, output_path: Optional[str] = None) -> str:
        """本地TTS处理"""
        try:
            # 这里可以集成NagaAgent的本地TTS模块
            # 目前先使用远程API
            return await self._remote_tts(text, output_path)
            
        except Exception as e:
            logger.error(f"本地TTS失败: {e}")
            raise
            
    async def _remote_tts(self, text: str, output_path: Optional[str] = None) -> str:
        """远程TTS API调用"""
        try:
            if not output_path:
                output_path = tempfile.mktemp(suffix='.wav')
            
            # 调用NagaAgent的TTS API
            async with aiohttp.ClientSession() as session:
                data = {
                    "text": text,
                    "text_language": "zh",
                    "format": "wav"
                }
                
                async with session.post(self.tts_api_url, json=data) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        
                        # 保存音频文件
                        with open(output_path, 'wb') as f:
                            f.write(audio_data)
                        
                        logger.info(f"TTS转换成功: {output_path}")
                        return output_path
                    else:
                        logger.error(f"TTS API调用失败: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"远程TTS失败: {e}")
            return None
            
    async def speech_to_text(self, audio_path: str) -> str:
        """语音转文本"""
        try:
            if not self.asr_enabled:
                return None
                
            async with aiohttp.ClientSession() as session:
                with open(audio_path, 'rb') as audio_file:
                    data = aiohttp.FormData()
                    data.add_field('audio', audio_file, filename=os.path.basename(audio_path))
                    
                    async with session.post(self.asr_api_url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get('text', '')
                        else:
                            logger.error(f"ASR API调用失败: {response.status}")
                            return None
                            
        except Exception as e:
            logger.error(f"ASR转换失败: {e}")
            return None
            
    def get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            import wave
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                return frames / sample_rate
                
        except Exception as e:
            logger.error(f"获取音频时长失败: {e}")
            return 0.0
```

#### 2.4 创建情绪处理器

**情绪处理模块**：
```python
# NagaAgent/live2d_module/emotion_handler.py
import logging
import re
import asyncio
from typing import Dict, List, Tuple, Any
from .event_adapter import event_bus

logger = logging.getLogger("live2d_emotion")

class Live2DEmotionHandler:
    """Live2D情绪处理器 - 适配NagaAgent对话系统"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.emotion_keywords = self._load_emotion_keywords()
        self.current_emotion = "neutral"
        self.emotion_intensity = 1.0
        
        # 订阅事件
        event_bus.subscribe("ai_response_start", self._on_ai_response_start)
        event_bus.subscribe("ai_text_chunk", self._on_ai_text_chunk)
        event_bus.subscribe("ai_response_end", self._on_ai_response_end)
        
        logger.info("Live2D情绪处理器初始化完成")
        
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """加载情绪关键词"""
        return {
            "开心": [
                "开心", "高兴", "快乐", "哈哈", "呵呵", "嘻嘻", 
                "😊", "🙂", "😄", "😃", "happy", "哈哈", "笑",
                "太好了", "棒极了", "太棒了", "完美", "优秀"
            ],
            "生气": [
                "生气", "愤怒", "讨厌", "气死", "恼火", 
                "😠", "😡", "mad", "angry", "怒",
                "混蛋", "可恶", "烦死了", "气人"
            ],
            "伤心": [
                "伤心", "难过", "悲伤", "哭", "难过", 
                "😢", "😭", "😞", "😔", "sad", "cry",
                "痛苦", "心痛", "心疼", "遗憾"
            ],
            "惊讶": [
                "惊讶", "震惊", "哇", "天啊", "不会吧", 
                "😮", "😲", "😯", "wow", "amazing",
                "真的吗", "难以置信", "太意外了"
            ],
            "害羞": [
                "害羞", "不好意思", "脸红", "羞涩", 
                "😳", "😊", "shy", "embarrassed",
                "羞羞", "不好意思", "难为情"
            ],
            "害怕": [
                "害怕", "恐惧", "怕", "吓人", 
                "😨", "😰", "scared", "afraid",
                "恐怖", "可怕", "吓死了"
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
        if text.strip():
            emotion, intensity = self.analyze_emotion(text)
            
            # 更新当前情绪
            if emotion != "neutral" and emotion != self.current_emotion:
                self.current_emotion = emotion
                self.emotion_intensity = intensity
                
                # 发布情绪事件
                await event_bus.publish("live2d_emotion_detected", {
                    "emotion": emotion,
                    "intensity": intensity,
                    "text": text
                })
                
    async def _on_ai_response_end(self, data=None):
        """AI响应结束事件"""
        # 重置到中性情绪
        await asyncio.sleep(1.0)  # 保持情绪1秒
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
            for keyword in keywords:
                # 使用正则表达式进行模糊匹配
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(text)
                score += len(matches)
            
            if score > 0:
                emotion_scores[emotion] = score
        
        # 如果没有检测到情绪，返回中性
        if not emotion_scores:
            return "neutral", 1.0
            
        # 找到得分最高的情绪
        max_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[max_emotion]
        
        # 计算强度（基于得分）
        intensity = min(max_score / 3.0, 2.0)  # 最大强度为2.0
        
        return max_emotion, intensity
        
    def get_current_emotion(self) -> Tuple[str, float]:
        """获取当前情绪"""
        return self.current_emotion, self.emotion_intensity
        
    def set_enabled(self, enabled: bool):
        """启用/禁用情绪处理"""
        self.enabled = enabled
        logger.info(f"情绪处理{'启用' if enabled else '禁用'}")
```

### 步骤3：API接口适配 - 集成到NagaAgent

#### 3.1 创建Live2D API端点

**在NagaAgent中添加Live2D专用的API端点**：
```python
# NagaAgent/apiserver/live2d_api.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, Optional
import os
import tempfile
import json
import logging
from pydantic import BaseModel

# 导入Live2D模块
try:
    from live2d_module.live2d_widget import NagaLive2DWidget
    from live2d_module.emotion_handler import Live2DEmotionHandler
    from live2d_module.audio_integration import Live2DAudioAdapter
    LIVE2D_AVAILABLE = True
except ImportError:
    LIVE2D_AVAILABLE = False
    
router = APIRouter()
logger = logging.getLogger("live2d_api")

# 请求模型
class EmotionRequest(BaseModel):
    emotion: str
    intensity: float = 1.0
    
class TTSRequest(BaseModel):
    text: str
    output_path: Optional[str] = None
    
class Live2DConfigRequest(BaseModel):
    enabled: bool = True
    model_path: Optional[str] = None
    scale: Optional[float] = None
    offset_x: Optional[int] = None
    offset_y: Optional[int] = None
    tts_enabled: Optional[bool] = None
    asr_enabled: Optional[bool] = None
    tts_api_url: Optional[str] = None
    asr_api_url: Optional[str] = None

# 全局Live2D实例
live2d_widget: Optional[NagaLive2DWidget] = None
emotion_handler: Optional[Live2DEmotionHandler] = None
audio_adapter: Optional[Live2DAudioAdapter] = None

def init_live2d_services(config: Dict[str, Any] = None):
    """初始化Live2D服务"""
    global live2d_widget, emotion_handler, audio_adapter
    
    if not LIVE2D_AVAILABLE:
        logger.warning("Live2D模块不可用")
        return False
        
    try:
        # 初始化情绪处理器
        emotion_handler = Live2DEmotionHandler(config.get("emotion", {}))
        
        # 初始化音频适配器
        audio_config = {
            "tts_enabled": config.get("tts_enabled", True),
            "asr_enabled": config.get("asr_enabled", True),
            "tts_api_url": config.get("tts_api_url", "http://127.0.0.1:8000/voice/speak"),
            "asr_api_url": config.get("asr_api_url", "http://127.0.0.1:8000/voice/transcribe")
        }
        audio_adapter = Live2DAudioAdapter(audio_config)
        
        logger.info("Live2D服务初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"Live2D服务初始化失败: {e}")
        return False

@router.get("/status")
async def get_live2d_status():
    """获取Live2D状态"""
    return {
        "available": LIVE2D_AVAILABLE,
        "initialized": live2d_widget is not None,
        "emotion_handler_enabled": emotion_handler is not None and emotion_handler.enabled,
        "audio_adapter_enabled": audio_adapter is not None
    }

@router.post("/emotion/trigger")
async def trigger_emotion(request: EmotionRequest):
    """触发Live2D情绪动作"""
    if not live2d_widget:
        raise HTTPException(status_code=400, detail="Live2D控件未初始化")
        
    try:
        live2d_widget.trigger_emotion(request.emotion, request.intensity)
        return {
            "status": "success", 
            "emotion": request.emotion,
            "intensity": request.intensity
        }
    except Exception as e:
        logger.error(f"触发情绪失败: {e}")
        raise HTTPException(status_code=500, detail=f"触发情绪失败: {str(e)}")

@router.post("/text-to-speech")
async def text_to_speech(request: TTSRequest):
    """文本转语音"""
    if not audio_adapter:
        raise HTTPException(status_code=400, detail="音频适配器未初始化")
        
    try:
        audio_path = await audio_adapter.text_to_speech(request.text, request.output_path)
        if audio_path:
            return {
                "status": "success",
                "audio_path": audio_path,
                "duration": audio_adapter.get_audio_duration(audio_path)
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
                "text": text
            }
        else:
            raise HTTPException(status_code=500, detail="语音识别失败")
            
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")

@router.post("/start-lip-sync")
async def start_lip_sync(audio_file: UploadFile = File(...)):
    """开始嘴型同步"""
    if not live2d_widget:
        raise HTTPException(status_code=400, detail="Live2D控件未初始化")
        
    try:
        # 保存上传的音频文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(await audio_file.read())
            temp_path = temp_file.name
            
        # 开始嘴型同步
        success = live2d_widget.start_lip_sync(temp_path)
        
        if success:
            return {
                "status": "success",
                "audio_path": temp_path
            }
        else:
            os.unlink(temp_path)
            raise HTTPException(status_code=500, detail="嘴型同步启动失败")
            
    except Exception as e:
        logger.error(f"嘴型同步失败: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"嘴型同步失败: {str(e)}")

@router.post("/config/update")
async def update_config(request: Live2DConfigRequest):
    """更新Live2D配置"""
    try:
        config_updates = request.dict(exclude_unset=True)
        
        # 更新Live2D控件配置
        if live2d_widget:
            if "scale" in config_updates:
                live2d_widget.scale = config_updates["scale"]
            if "offset_x" in config_updates:
                live2d_widget.model_offset_x = config_updates["offset_x"]
            if "offset_y" in config_updates:
                live2d_widget.model_offset_y = config_updates["offset_y"]
                
        # 更新情绪处理器配置
        if emotion_handler:
            if "enabled" in config_updates:
                emotion_handler.set_enabled(config_updates["enabled"])
                
        # 更新音频适配器配置
        if audio_adapter:
            if "tts_enabled" in config_updates:
                audio_adapter.tts_enabled = config_updates["tts_enabled"]
            if "asr_enabled" in config_updates:
                audio_adapter.asr_enabled = config_updates["asr_enabled"]
            if "tts_api_url" in config_updates:
                audio_adapter.tts_api_url = config_updates["tts_api_url"]
            if "asr_api_url" in config_updates:
                audio_adapter.asr_api_url = config_updates["asr_api_url"]
                
        return {"status": "success", "updated_fields": list(config_updates.keys())}
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.get("/config")
async def get_config():
    """获取当前Live2D配置"""
    try:
        config = {
            "available": LIVE2D_AVAILABLE,
            "widget_config": {},
            "emotion_config": {},
            "audio_config": {}
        }
        
        if live2d_widget:
            config["widget_config"] = {
                "scale": live2d_widget.scale,
                "offset_x": live2d_widget.model_offset_x,
                "offset_y": live2d_widget.model_offset_y,
                "model_path": live2d_widget.model_path
            }
            
        if emotion_handler:
            config["emotion_config"] = {
                "enabled": emotion_handler.enabled,
                "current_emotion": emotion_handler.current_emotion,
                "emotion_intensity": emotion_handler.emotion_intensity
            }
            
        if audio_adapter:
            config["audio_config"] = {
                "tts_enabled": audio_adapter.tts_enabled,
                "asr_enabled": audio_adapter.asr_enabled,
                "tts_api_url": audio_adapter.tts_api_url,
                "asr_api_url": audio_adapter.asr_api_url
            }
            
        return config
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")
```

#### 3.2 集成到NagaAgent主服务器

**修改API服务器**：
```python
# NagaAgent/apiserver/api_server.py
from fastapi import FastAPI
from .live2d_api import router as live2d_router, init_live2d_services
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(title="NagaAgent API Server")
    
    # 包含现有的路由
    # app.include_router(other_router, prefix="/api/v1", tags=["other"])
    
    # 包含Live2D路由
    app.include_router(live2d_router, prefix="/api/live2d", tags=["Live2D"])
    
    # 添加启动事件
    @app.on_event("startup")
    async def startup_event():
        logger.info("启动NagaAgent API服务器")
        
        # 初始化Live2D服务
        live2d_config = {
            "emotion": {"enabled": True},
            "tts_enabled": True,
            "asr_enabled": True,
            "tts_api_url": "http://127.0.0.1:8000/voice/speak",
            "asr_api_url": "http://127.0.0.1:8000/voice/transcribe"
        }
        
        init_live2d_services(live2d_config)
        
    return app
```

#### 3.2 对话系统集成

**修改对话核心以支持Live2D情绪分析**：
```python
# NagaAgent/conversation_core.py
class NagaConversation:
    def __init__(self):
        self.live2d_enabled = True  # 是否启用Live2D
        
    async def generate_response(self, message: str, session_id: str = None):
        """生成响应并处理Live2D情绪"""
        # 原有的对话逻辑
        response = await self.llm_generate(message, session_id)
        
        # 如果启用了Live2D，分析情绪并触发动作
        if self.live2d_enabled:
            await self.analyze_and_trigger_emotion(response)
            
        return response
        
    async def analyze_and_trigger_emotion(self, text: str):
        """分析文本情绪并触发Live2D动作"""
        # 简单的情绪分析（可以替换为更复杂的NLP分析）
        emotion_keywords = {
            "开心": ["开心", "高兴", "快乐", "哈哈", "😊", "🙂"],
            "生气": ["生气", "愤怒", "讨厌", "😠", "😡"],
            "伤心": ["伤心", "难过", "悲伤", "😢", "😭"],
            "惊讶": ["惊讶", "震惊", "哇", "天啊", "😮", "😲"],
            "害羞": ["害羞", "不好意思", "脸红", "😳"]
        }
        
        detected_emotion = "neutral"
        max_score = 0
        
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > max_score:
                max_score = score
                detected_emotion = emotion
                
        # 触发Live2D情绪
        await self.trigger_live2d_emotion(detected_emotion)
        
    async def trigger_live2d_emotion(self, emotion: str, intensity: float = 1.0):
        """触发Live2D情绪动作"""
        try:
            # 通过HTTP API触发情绪
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://127.0.0.1:8000/live2d/emotion/trigger",
                    json={"emotion": emotion, "intensity": intensity}
                ) as response:
                    if response.status == 200:
                        print(f"Live2D情绪触发成功: {emotion}")
        except Exception as e:
            print(f"Live2D情绪触发失败: {e}")
```

### 步骤4：UI集成

#### 4.1 方案一：独立Electron应用

**创建启动脚本**：
```python
# NagaAgent/live2d_frontend/js_version/start_live2d.py
import subprocess
import os
import sys
from pathlib import Path

def start_live2d_frontend():
    """启动Live2D前端应用"""
    live2d_dir = Path(__file__).parent / "js_version"
    
    # 检查Node.js环境
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("请先安装Node.js")
        return
        
    # 安装依赖
    os.chdir(live2d_dir)
    if not (live2d_dir / "node_modules").exists():
        print("安装Live2D前端依赖...")
        subprocess.run(["npm", "install"], check=True)
        
    # 启动应用
    print("启动Live2D前端...")
    subprocess.run(["npm", "start"])

if __name__ == "__main__":
    start_live2d_frontend()
```

**集成到NagaAgent主程序**：
```python
# NagaAgent/main.py
import threading
import time
from live2d_frontend.js_version.start_live2d import start_live2d_frontend

class NagaAgent:
    def __init__(self):
        self.live2d_process = None
        
    def start_live2d_frontend(self):
        """启动Live2D前端"""
        def run_live2d():
            start_live2d_frontend()
            
        self.live2d_thread = threading.Thread(target=run_live2d, daemon=True)
        self.live2d_thread.start()
        
    def start(self):
        """启动NagaAgent"""
        # 启动Live2D前端
        if config.live2d.enabled:
            self.start_live2d_frontend()
            time.sleep(2)  # 等待Live2D前端启动
            
        # 启动其他服务...
```

#### 4.2 方案二：集成到PyQt界面

**修改主聊天窗口**：
```python
# NagaAgent/ui/pyqt_chat_window.py
from ..live2d_frontend.py_version.live2d_widget import Live2DWidget

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # 创建主布局
        self.main_layout = QHBoxLayout()
        
        # 创建Live2D控件
        self.live2d_widget = Live2DWidget()
        self.live2d_widget.setFixedSize(400, 600)
        
        # 创建聊天区域
        self.chat_area = QWidget()
        
        # 添加到布局
        self.main_layout.addWidget(self.live2d_widget, 1)  # 30%宽度
        self.main_layout.addWidget(self.chat_area, 2)       # 70%宽度
        
        self.setLayout(self.main_layout)
        
    def on_message_received(self, message):
        """收到消息时的处理"""
        # 显示消息
        self.display_message(message)
        
        # 触发Live2D情绪
        emotion = self.analyze_emotion(message)
        self.live2d_widget.trigger_emotion(emotion)
```

### 步骤5：配置系统集成

#### 5.1 扩展配置文件

**在NagaAgent配置中添加Live2D相关配置**：
```python
# NagaAgent/config.py
class Live2DConfig(BaseModel):
    """Live2D配置"""
    enabled: bool = Field(default=True, description="是否启用Live2D")
    frontend_type: str = Field(default="electron", description="前端类型: electron/pyqt")
    model_path: str = Field(default="live2d_frontend/shared/models/hiyori_pro_mic.model3.json", description="Live2D模型路径")
    auto_start: bool = Field(default=True, description="是否自动启动")
    emotion_analysis: bool = Field(default=True, description="是否启用情绪分析")
    lip_sync: bool = Field(default=True, description="是否启用嘴型同步")
    scale: float = Field(default=0.25, description="模型缩放比例")
    position: Dict[str, float] = Field(default={"x": 0.5, "y": 0.5}, description="模型位置")

class UIConfig(BaseModel):
    """UI配置"""
    bg_alpha: float = Field(default=0.3, description="背景透明度")
    window_bg_alpha: float = Field(default=0.95, description="窗口背景透明度")
    user_name: str = Field(default="用户", description="用户名")
    live2d: Live2DConfig = Field(default_factory=Live2DConfig, description="Live2D配置")
```

#### 5.2 创建配置管理工具

**Live2D配置管理界面**：
```python
# NagaAgent/ui/live2d_settings.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QCheckBox, QSlider, QPushButton)
from config import config

class Live2DSettingsWidget(QWidget):
    """Live2D设置控件"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 前端类型选择
        frontend_layout = QHBoxLayout()
        frontend_layout.addWidget(QLabel("前端类型:"))
        self.frontend_combo = QComboBox()
        self.frontend_combo.addItems(["electron", "pyqt"])
        self.frontend_combo.setCurrentText(config.ui.live2d.frontend_type)
        frontend_layout.addWidget(self.frontend_combo)
        layout.addLayout(frontend_layout)
        
        # 启用开关
        self.enabled_checkbox = QCheckBox("启用Live2D")
        self.enabled_checkbox.setChecked(config.ui.live2d.enabled)
        layout.addWidget(self.enabled_checkbox)
        
        # 情绪分析开关
        self.emotion_checkbox = QCheckBox("情绪分析")
        self.emotion_checkbox.setChecked(config.ui.live2d.emotion_analysis)
        layout.addWidget(self.emotion_checkbox)
        
        # 嘴型同步开关
        self.lip_sync_checkbox = QCheckBox("嘴型同步")
        self.lip_sync_checkbox.setChecked(config.ui.live2d.lip_sync)
        layout.addWidget(self.lip_sync_checkbox)
        
        # 缩放滑块
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("缩放比例:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(10, 100)
        self.scale_slider.setValue(int(config.ui.live2d.scale * 100))
        scale_layout.addWidget(self.scale_slider)
        layout.addLayout(scale_layout)
        
        # 保存按钮
        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def save_settings(self):
        """保存设置"""
        config.ui.live2d.frontend_type = self.frontend_combo.currentText()
        config.ui.live2d.enabled = self.enabled_checkbox.isChecked()
        config.ui.live2d.emotion_analysis = self.emotion_checkbox.isChecked()
        config.ui.live2d.lip_sync = self.lip_sync_checkbox.isChecked()
        config.ui.live2d.scale = self.scale_slider.value() / 100
        
        # 保存到文件
        config.save_config()
```

### 步骤6：依赖管理

#### 6.1 更新依赖文件

**在requirements.txt中添加Live2D相关依赖**：
```
# Live2D相关依赖
# 如果使用Python版本的Live2D
live2d-v3>=0.1.0
pyopengl>=3.1.0
pyopengl-accelerate>=3.1.0

# 如果使用JavaScript版本，需要Node.js环境
# npm依赖在live2d_frontend/js_version/package.json中管理

# 音频处理依赖
pyaudio>=0.2.11
numpy>=1.21.0

# WebSocket支持
websockets>=10.0
aiohttp>=3.8.0
```

**创建JavaScript版本的package.json**：
```json
{
  "name": "nagaagent-live2d",
  "version": "1.0.0",
  "description": "NagaAgent Live2D Frontend",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "dev": "electron . --dev"
  },
  "dependencies": {
    "electron": "^25.0.0",
    "pixi.js": "^7.3.0",
    "pixi-live2d-display": "^0.4.0",
    "live2d-widget": "^3.2.0"
  },
  "devDependencies": {
    "electron-builder": "^24.0.0"
  }
}
```

### 步骤7：测试和调试

#### 7.1 单元测试

**创建测试脚本**：
```python
# NagaAgent/tests/test_live2d.py
import unittest
import asyncio
from unittest.mock import Mock, patch

class TestLive2DIntegration(unittest.TestCase):
    """Live2D集成测试"""
    
    def setUp(self):
        self.conversation = NagaConversation()
        
    def test_emotion_analysis(self):
        """测试情绪分析"""
        test_cases = [
            ("今天真开心！", "开心"),
            ("我生气了", "生气"),
            ("太震惊了", "惊讶")
        ]
        
        for text, expected_emotion in test_cases:
            with patch.object(self.conversation, 'trigger_live2d_emotion') as mock_trigger:
                asyncio.run(self.conversation.analyze_and_trigger_emotion(text))
                mock_trigger.assert_called_once()
                
    def test_live2d_api_integration(self):
        """测试Live2D API集成"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            
            asyncio.run(self.conversation.trigger_live2d_emotion("开心"))
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn("emotion", call_args[1]['json'])

if __name__ == "__main__":
    unittest.main()
```

#### 7.2 集成测试

**创建完整的测试流程**：
```python
# NagaAgent/tests/test_integration.py
import pytest
import subprocess
import time
import requests

class TestLive2DFullIntegration:
    """Live2D完整集成测试"""
    
    @pytest.fixture(scope="class")
    def nagaagent_server(self):
        """启动NagaAgent服务器"""
        server_process = subprocess.Popen(["python", "main.py"])
        time.sleep(5)  # 等待服务器启动
        yield server_process
        server_process.terminate()
        
    @pytest.fixture(scope="class")
    def live2d_frontend(self):
        """启动Live2D前端"""
        frontend_process = subprocess.Popen([
            "python", 
            "live2d_frontend/js_version/start_live2d.py"
        ])
        time.sleep(3)  # 等待前端启动
        yield frontend_process
        frontend_process.terminate()
        
    def test_end_to_end_integration(self, nagaagent_server, live2d_frontend):
        """端到端集成测试"""
        # 测试API健康检查
        response = requests.get("http://127.0.0.1:8000/health")
        assert response.status_code == 200
        
        # 测试对话功能
        chat_response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"message": "你好，测试一下"}
        )
        assert chat_response.status_code == 200
        
        # 测试Live2D情绪触发
        emotion_response = requests.post(
            "http://127.0.0.1:8000/live2d/emotion/trigger",
            json={"emotion": "happy", "intensity": 1.0}
        )
        assert emotion_response.status_code == 200
```

### 步骤8：部署和打包

#### 8.1 创建安装脚本

**Windows安装脚本**：
```batch
@echo off
echo 正在安装Live2D前端依赖...

cd /d NagaAgent\live2d_frontend\js_version

echo 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 请先安装Node.js
    pause
    exit /b 1
)

echo 安装npm依赖...
call npm install

echo 安装完成!
pause
```

**创建启动脚本**：
```batch
@echo off
echo 启动NagaAgent with Live2D...

cd /d NagaAgent

:: 启动Live2D前端
start "Live2D Frontend" cmd /k "python live2d_frontend/js_version/start_live2d.py"

:: 等待前端启动
timeout /t 3

:: 启动NagaAgent主程序
start "NagaAgent" cmd /k "python main.py"

echo 所有服务已启动!
pause
```

#### 8.2 打包配置

**修改Electron打包配置**：
```json
{
  "build": {
    "appId": "com.nagaagent.live2d",
    "productName": "NagaAgent Live2D",
    "directories": {
      "output": "dist"
    },
    "files": [
      "**/*",
      "!**/node_modules/*/{CHANGELOG.md,README.md,README,readme.md,readme}",
      "!**/node_modules/*/{test,__tests__,tests,powered-test,example,examples}",
      "!**/node_modules/*.d.ts",
      "!**/node_modules/.bin",
      "!**/*.{iml,o,hprof,orig,pyc,pyo,rbc,swp,csproj,sln,xproj}",
      "!.editorconfig",
      "!**/._*",
      "!**/{.DS_Store,.git,.hg,.svn,CVS,RCS,SCCS,.gitignore,.gitattributes}",
      "!**/{__pycache__,thumbs.db,.flowconfig,.idea,.vs,.nyc_output}",
      "!**/{appveyor.yml,.travis.yml,circle.yml}",
      "!**/{npm-debug.log,yarn.lock,.yarn-integrity,.yarn-metadata.json}"
    ],
    "extraResources": [
      {
        "from": "../shared/models",
        "to": "models",
        "filter": ["**/*"]
      }
    ]
  }
}
```

## 推荐实施方案

基于项目复杂度和维护性考虑，**推荐使用方案一（JavaScript版本）**，理由如下：

### 优势：
1. **保持原有功能**：My-Neuro的Live2D实现已经很成熟，直接移植减少开发风险
2. **独立维护**：Live2D前端作为独立模块，不影响NagaAgent核心功能
3. **技术成熟**：Electron + PIXI.js的Live2D实现比Python版本更稳定
4. **扩展性好**：未来可以独立升级Live2D前端而不影响后端

### 实施优先级：
1. **第一阶段**：移植JavaScript版本，实现基本Live2D显示
2. **第二阶段**：集成情绪分析和动作触发
3. **第三阶段**：实现嘴型同步和音频集成
4. **第四阶段**：优化性能和用户体验

## 注意事项

1. **Live2D SDK许可**：确保Live2D SDK的使用符合许可协议
2. **模型文件版权**：Live2D模型文件可能有版权限制，需要确认使用权限
3. **性能优化**：Live2D渲染可能占用较多系统资源，需要做好性能优化
4. **错误处理**：做好Live2D前端与后端通信的错误处理和降级方案
5. **用户体验**：提供开关选项，让用户可以选择是否启用Live2D功能

## 故障排除

### 常见问题：
1. **Node.js版本不兼容**：确保使用Node.js 16+
2. **Live2D模型加载失败**：检查模型文件路径和格式
3. **WebSocket连接失败**：检查防火墙和端口设置
4. **音频同步问题**：检查音频格式和播放器兼容性

### 调试工具：
1. **开发者工具**：Electron应用可以使用Chrome开发者工具
2. **日志系统**：启用详细的调试日志
3. **性能监控**：使用Chrome Performance面板监控渲染性能

通过以上步骤，你可以成功将My-Neuro的前端数字人功能移植到NagaAgent项目中，为用户提供更加丰富的交互体验。