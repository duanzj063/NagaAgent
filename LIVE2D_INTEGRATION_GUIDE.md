# Live2D数字人集成文档

## 概述

本文档描述了Live2D数字人功能在NagaAgent中的完整集成方案。通过这套集成，NagaAgent能够显示一个生动的Live2D数字人形象，并根据对话内容展示相应的情绪和嘴型同步效果。

## 功能特性

### 核心功能
- **实时情绪显示**: 根据AI回复内容自动识别并显示对应的情绪
- **嘴型同步**: 与TTS语音同步的嘴型动画效果
- **事件驱动**: 基于事件总线的松耦合架构
- **配置灵活**: 支持丰富的配置选项

### 支持的情绪
- 开心 (Happy)
- 生气 (Angry)
- 伤心 (Sad)
- 惊讶 (Surprised)
- 害羞 (Shy)
- 害怕 (Afraid)
- 中性 (Neutral)

## 系统架构

### 模块结构
```
live2d_module/
├── __init__.py              # 模块初始化和导出
├── event_adapter.py         # 事件总线适配器
├── emotion_handler.py       # 情绪处理器
├── audio_integration.py     # 音频集成适配器
└── live2d_widget.py         # Live2D控件
```

### 核心组件

#### 1. 事件总线 (EventBus)
- 负责模块间的事件通信
- 支持异步事件处理
- 提供事件历史记录功能

#### 2. 情绪处理器 (Live2DEmotionHandler)
- 实时分析AI回复文本
- 识别情绪类型和强度
- 支持自定义情绪关键词

#### 3. 音频适配器 (Live2DAudioAdapter)
- 连接TTS和ASR服务
- 提供音频缓存功能
- 支持重试机制

#### 4. Live2D控件 (NagaLive2DWidget)
- 管理Live2D模型加载和显示
- 处理情绪和嘴型同步
- 提供控件状态管理

## 配置说明

### 配置文件
Live2D的配置集成在 `config.py` 文件中的 `Live2DConfig` 类：

```python
class Live2DConfig(BaseModel):
    enabled: bool = Field(default=False, description="是否启用Live2D数字人")
    model_path: str = Field(default="live2d_module/models/hiyori_pro_mic.model3.json", description="Live2D模型路径")
    auto_start: bool = Field(default=True, description="是否自动启动Live2D")
    emotion_analysis: bool = Field(default=True, description="是否启用情绪分析")
    lip_sync: bool = Field(default=True, description="是否启用嘴型同步")
    tts_enabled: bool = Field(default=True, description="是否启用TTS")
    asr_enabled: bool = Field(default=True, description="是否启用ASR")
    scale: float = Field(default=1.0, ge=0.1, le=3.0, description="模型缩放比例")
    offset_x: int = Field(default=1050, ge=0, le=3840, description="模型X轴偏移")
    offset_y: int = Field(default=600, ge=0, le=2160, description="模型Y轴偏移")
    frontend_type: str = Field(default="python", description="前端类型: python/electron")
    cache_enabled: bool = Field(default=True, description="是否启用音频缓存")
    cache_dir: str = Field(default="live2d_cache", description="缓存目录")
    tts_api_url: str = Field(default="http://127.0.0.1:8000/voice/speak", description="TTS API URL")
    asr_api_url: str = Field(default="http://127.0.0.1:8000/voice/transcribe", description="ASR API URL")
    emotion_weights: Dict[str, float] = Field(default={...}, description="情绪权重配置")
    emotion_duration: Dict[str, float] = Field(default={...}, description="情绪持续时间配置")
    audio_timeout: int = Field(default=30, ge=5, le=120, description="音频处理超时时间")
    max_retries: int = Field(default=3, ge=1, le=10, description="最大重试次数")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="重试延迟")
```

### 环境变量
所有Live2D配置项都有对应的全局变量，便于在代码中直接使用：

```python
# Live2D数字人配置兼容性变量
LIVE2D_ENABLED = config.ui.live2d.enabled
LIVE2D_MODEL_PATH = config.ui.live2d.model_path
LIVE2D_AUTO_START = config.ui.live2d.auto_start
LIVE2D_EMOTION_ANALYSIS = config.ui.live2d.emotion_analysis
LIVE2D_LIP_SYNC = config.ui.live2d.lip_sync
LIVE2D_TTS_ENABLED = config.ui.live2d.tts_enabled
LIVE2D_ASR_ENABLED = config.ui.live2d.asr_enabled
LIVE2D_SCALE = config.ui.live2d.scale
LIVE2D_OFFSET_X = config.ui.live2d.offset_x
LIVE2D_OFFSET_Y = config.ui.live2d.offset_y
# ... 更多配置项
```

## 安装和配置

### 1. 安装依赖项

```bash
# 基础依赖
pip install pydantic aiohttp numpy

# Live2D相关依赖（可选）
pip install live2d-v3 pyopengl pygame

# 如果使用Electron前端
pip install electron
```

### 2. 配置Live2D

编辑 `config.json` 文件：

```json
{
  "ui": {
    "live2d": {
      "enabled": true,
      "model_path": "live2d_module/models/hiyori_pro_mic.model3.json",
      "emotion_analysis": true,
      "lip_sync": true,
      "tts_enabled": true,
      "asr_enabled": true,
      "scale": 1.0,
      "offset_x": 1050,
      "offset_y": 600,
      "frontend_type": "python"
    }
  }
}
```

### 3. 准备Live2D模型

将Live2D模型文件放置在指定目录：

```
live2d_module/models/
├── hiyori_pro_mic.model3.json
├── hiyori_pro_mic.2048/
├── hiyori_pro_mic.2048/texture_00.png
└── ...
```

## 使用方法

### 1. 启动NagaAgent

```bash
python main.py
```

启动时会显示Live2D模块的初始化状态：

```
==============================================================
正在初始化Live2D模块...
✅ Live2D模块初始化成功
   版本: 1.0.0
   控件可用: 是
   情绪处理: 可用
   音频适配: 可用
   事件总线: 可用
==============================================================
```

### 2. 在对话中使用

当用户与NagaAgent对话时，Live2D数字人会：

1. **显示情绪**: 根据AI回复内容自动识别并显示情绪
2. **嘴型同步**: 如果启用了TTS，会与语音同步显示嘴型动画
3. **状态变化**: 在对话开始、进行中、结束时显示不同的状态

### 3. 自定义情绪关键词

可以通过代码扩展情绪关键词：

```python
from live2d_module.emotion_handler import Live2DEmotionHandler

handler = Live2DEmotionHandler()
handler.add_emotion_keywords("开心", ["哈哈", "笑死", "太棒了"])
handler.add_emotion_keywords("生气", ["气死", "烦人", "混蛋"])
```

## 事件系统

### 事件类型
- `ai_response_start`: AI响应开始
- `ai_text_chunk`: AI文本块生成
- `ai_response_end`: AI响应结束
- `live2d_emotion_detected`: 情绪检测到
- `tts_completed`: TTS转换完成
- `asr_completed`: ASR转换完成

### 事件监听

```python
from live2d_module import event_bus

async def on_emotion_detected(data):
    emotion = data.get("emotion")
    intensity = data.get("intensity")
    print(f"检测到情绪: {emotion} (强度: {intensity})")

event_bus.subscribe("live2d_emotion_detected", on_emotion_detected)
```

### 事件发布

```python
from live2d_module import event_bus, create_emotion_event

emotion_event = create_emotion_event("开心", 1.0, "今天真开心！")
await event_bus.publish("live2d_emotion_detected", emotion_event)
```

## 测试

### 运行集成测试

```bash
python test_live2d_integration.py
```

测试包括：
- 模块导入测试
- 配置检查测试
- 依赖项检查测试
- 事件系统测试
- 情绪处理器测试
- 音频适配器测试
- 对话集成测试
- 主程序集成测试

### 测试报告

测试完成后会生成详细的测试报告 `live2d_test_report.json`。

## 故障排除

### 常见问题

1. **Live2D模块不可用**
   - 检查依赖项是否安装
   - 确认模型文件路径是否正确

2. **情绪分析不工作**
   - 检查 `emotion_analysis` 配置项
   - 查看日志中的错误信息

3. **嘴型同步失效**
   - 确认TTS服务正在运行
   - 检查 `tts_api_url` 配置

4. **事件发布失败**
   - 检查事件总线是否正确初始化
   - 确认异步事件处理正常

### 日志查看

Live2D模块的日志级别可以通过 `config.py` 中的 `log_level` 配置：

```python
LOG_LEVEL = config.system.log_level  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 性能优化

### 1. 音频缓存
启用音频缓存可以减少重复的TTS调用：

```python
LIVE2D_CACHE_ENABLED = True
LIVE2D_CACHE_DIR = "live2d_cache"
```

### 2. 情绪持续时间
调整情绪持续时间可以优化用户体验：

```python
LIVE2D_EMOTION_DURATION = {
    "开心": 2.0,
    "生气": 1.5,
    "伤心": 3.0,
    # ...
}
```

### 3. 重试机制
配置网络请求的重试参数：

```python
LIVE2D_MAX_RETRIES = 3
LIVE2D_RETRY_DELAY = 1.0
```

## 扩展开发

### 添加新的情绪类型

1. 在 `emotion_handler.py` 中添加新的情绪关键词
2. 更新 `emotion_weights` 和 `emotion_duration` 配置
3. 在Live2D模型中添加对应的动作

### 自定义事件处理器

```python
from live2d_module import event_bus

class CustomEventHandler:
    async def handle_emotion(self, data):
        # 自定义情绪处理逻辑
        pass
    
    async def handle_audio(self, data):
        # 自定义音频处理逻辑
        pass

handler = CustomEventHandler()
event_bus.subscribe("live2d_emotion_detected", handler.handle_emotion)
event_bus.subscribe("tts_completed", handler.handle_audio)
```

### 集成其他前端框架

当前支持Python和Electron前端，可以通过修改 `frontend_type` 配置来切换：

```python
LIVE2D_FRONTEND_TYPE = "electron"  # 或 "python"
```

## 版本历史

- v1.0.0: 初始版本，支持基本情绪显示和事件系统
- v1.1.0: 添加音频集成和嘴型同步功能
- v1.2.0: 优化性能和缓存机制

## 许可证

本模块遵循NagaAgent项目的许可证。

## 贡献

欢迎提交Issue和Pull Request来改进Live2D集成功能。

## 联系方式

如有问题，请通过以下方式联系：
- 项目Issues: [GitHub Issues](https://github.com/your-repo/nagaagent/issues)
- 邮箱: your-email@example.com