#!/usr/bin/env python3
"""
Live2D音频集成适配器
为Live2D模块提供音频处理功能
"""

import os
import tempfile
import logging
import wave
import asyncio
import aiohttp
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path

# 定义HTTPException类
class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")

from .event_adapter import event_bus, create_tts_event, create_asr_event

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
        
        # 音频处理配置
        self.audio_format = self.config.get("audio_format", "wav")
        self.sample_rate = self.config.get("sample_rate", 22050)
        self.channels = self.config.get("channels", 1)
        
        # 缓存配置
        self.enable_cache = self.config.get("enable_cache", True)
        self.cache_dir = Path(self.config.get("cache_dir", "audio_cache"))
        self.cache_dir.mkdir(exist_ok=True)
        
        # 超时配置
        self.tts_timeout = self.config.get("tts_timeout", 30)
        self.asr_timeout = self.config.get("asr_timeout", 30)
        
        # 重试配置
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1)
        
        logger.info("Live2D音频适配器初始化完成")
        
    async def text_to_speech(self, text: str, output_path: Optional[str] = None) -> str:
        """文本转语音，返回音频文件路径"""
        try:
            # 检查缓存
            if self.enable_cache:
                cached_path = self._get_cached_audio(text)
                if cached_path:
                    logger.info(f"使用缓存的音频: {cached_path}")
                    return cached_path
            
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
            
            # 创建重试机制
            for attempt in range(self.max_retries):
                try:
                    # 调用NagaAgent的TTS API
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.tts_timeout)) as session:
                        data = {
                            "text": text,
                            "text_language": "zh",
                            "format": self.audio_format
                        }
                        
                        async with session.post(self.tts_api_url, json=data) as response:
                            if response.status == 200:
                                audio_data = await response.read()
                                
                                # 保存音频文件
                                with open(output_path, 'wb') as f:
                                    f.write(audio_data)
                                
                                # 缓存音频文件
                                if self.enable_cache:
                                    self._cache_audio(text, output_path)
                                
                                # 获取音频时长
                                duration = self.get_audio_duration(output_path)
                                
                                # 发布TTS完成事件
                                tts_event = create_tts_event(text, output_path, duration, True)
                                await event_bus.publish("tts_completed", tts_event)
                                
                                logger.info(f"TTS转换成功: {output_path}, 时长: {duration:.2f}s")
                                return output_path
                            else:
                                error_text = await response.text()
                                logger.error(f"TTS API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {response.status} - {error_text}")
                                if attempt == self.max_retries - 1:
                                    raise HTTPException(status_code=response.status, detail=f"TTS API调用失败: {error_text}")
                                
                except aiohttp.ClientError as e:
                    logger.error(f"TTS网络错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(self.retry_delay)
                except Exception as e:
                    logger.error(f"TTS处理错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(self.retry_delay)
                        
        except Exception as e:
            logger.error(f"远程TTS失败: {e}")
            raise
            
    async def speech_to_text(self, audio_path: str) -> str:
        """语音转文本"""
        try:
            if not self.asr_enabled:
                return None
                
            # 检查音频文件
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            # 获取音频信息
            audio_info = self.get_audio_info(audio_path)
            if not audio_info:
                raise ValueError(f"无法读取音频文件信息: {audio_path}")
            
            # 创建重试机制
            for attempt in range(self.max_retries):
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.asr_timeout)) as session:
                        with open(audio_path, 'rb') as audio_file:
                            data = aiohttp.FormData()
                            data.add_field('audio', audio_file, filename=os.path.basename(audio_path))
                            
                            async with session.post(self.asr_api_url, data=data) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    text = result.get('text', '')
                                    
                                    # 发布ASR完成事件
                                    asr_event = create_asr_event(audio_path, text, 0.9, True)
                                    await event_bus.publish("asr_completed", asr_event)
                                    
                                    logger.info(f"ASR转换成功: {text}")
                                    return text
                                else:
                                    error_text = await response.text()
                                    logger.error(f"ASR API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {response.status} - {error_text}")
                                    if attempt == self.max_retries - 1:
                                        raise HTTPException(status_code=response.status, detail=f"ASR API调用失败: {error_text}")
                                    
                except aiohttp.ClientError as e:
                    logger.error(f"ASR网络错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(self.retry_delay)
                except Exception as e:
                    logger.error(f"ASR处理错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(self.retry_delay)
                    
        except Exception as e:
            logger.error(f"ASR转换失败: {e}")
            return None
            
    def get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                return frames / sample_rate
                
        except Exception as e:
            logger.error(f"获取音频时长失败: {e}")
            return 0.0
            
    def get_audio_info(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """获取音频文件信息"""
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                return {
                    "channels": wav_file.getnchannels(),
                    "sample_width": wav_file.getsampwidth(),
                    "sample_rate": wav_file.getframerate(),
                    "frames": wav_file.getnframes(),
                    "duration": wav_file.getnframes() / wav_file.getframerate(),
                    "compression_type": wav_file.getcomptype(),
                    "compression_name": wav_file.getcompname()
                }
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return None
            
    def _get_cached_audio(self, text: str) -> Optional[str]:
        """获取缓存的音频文件"""
        try:
            # 生成缓存文件名
            cache_key = hash(text)
            cache_file = self.cache_dir / f"{cache_key}.wav"
            
            if cache_file.exists():
                return str(cache_file)
            return None
            
        except Exception as e:
            logger.error(f"获取缓存音频失败: {e}")
            return None
            
    def _cache_audio(self, text: str, audio_path: str):
        """缓存音频文件"""
        try:
            if not self.enable_cache:
                return
                
            # 生成缓存文件名
            cache_key = hash(text)
            cache_file = self.cache_dir / f"{cache_key}.wav"
            
            # 复制音频文件到缓存
            import shutil
            shutil.copy2(audio_path, cache_file)
            
            logger.debug(f"音频文件已缓存: {cache_file}")
            
        except Exception as e:
            logger.error(f"缓存音频文件失败: {e}")
            
    def clear_cache(self):
        """清空音频缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.wav"):
                cache_file.unlink()
            logger.info("音频缓存已清空")
        except Exception as e:
            logger.error(f"清空音频缓存失败: {e}")
            
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            cache_files = list(self.cache_dir.glob("*.wav"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "enabled": self.enable_cache,
                "cache_dir": str(self.cache_dir),
                "file_count": len(cache_files),
                "total_size": total_size,
                "total_size_mb": total_size / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {"enabled": self.enable_cache, "error": str(e)}
            
    def validate_audio_file(self, audio_path: str) -> bool:
        """验证音频文件"""
        try:
            if not os.path.exists(audio_path):
                return False
                
            # 检查文件大小
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                return False
                
            # 检查音频格式
            try:
                with wave.open(audio_path, 'rb') as wav_file:
                    # 检查基本参数
                    if wav_file.getnchannels() not in [1, 2]:
                        return False
                    if wav_file.getsampwidth() not in [1, 2, 4]:
                        return False
                    if wav_file.getframerate() <= 0:
                        return False
                        
                return True
            except:
                return False
                
        except Exception as e:
            logger.error(f"验证音频文件失败: {e}")
            return False
            
    def convert_audio_format(self, input_path: str, output_path: str, 
                           target_sample_rate: int = 22050, 
                           target_channels: int = 1) -> bool:
        """转换音频格式"""
        try:
            # 这里可以使用pydub或其他音频处理库
            # 由于依赖问题，这里只是一个框架
            logger.warning("音频格式转换功能需要额外的音频处理库")
            return False
            
        except Exception as e:
            logger.error(f"转换音频格式失败: {e}")
            return False
            
    def set_tts_enabled(self, enabled: bool):
        """设置TTS启用状态"""
        self.tts_enabled = enabled
        logger.info(f"TTS已{'启用' if enabled else '禁用'}")
        
    def set_asr_enabled(self, enabled: bool):
        """设置ASR启用状态"""
        self.asr_enabled = enabled
        logger.info(f"ASR已{'启用' if enabled else '禁用'}")
        
    def set_tts_api_url(self, url: str):
        """设置TTS API URL"""
        self.tts_api_url = url
        logger.info(f"TTS API URL已设置为: {url}")
        
    def set_asr_api_url(self, url: str):
        """设置ASR API URL"""
        self.asr_api_url = url
        logger.info(f"ASR API URL已设置为: {url}")
        
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "tts_enabled": self.tts_enabled,
            "asr_enabled": self.asr_enabled,
            "tts_api_url": self.tts_api_url,
            "asr_api_url": self.asr_api_url,
            "audio_format": self.audio_format,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "enable_cache": self.enable_cache,
            "cache_dir": str(self.cache_dir),
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "tts_timeout": self.tts_timeout,
            "asr_timeout": self.asr_timeout
        }