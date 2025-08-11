#!/usr/bin/env python3
"""
Live2D集成测试脚本
用于验证Live2D模块在NagaAgent中的集成情况
"""

import asyncio
import logging
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class Live2DIntegrationTest:
    """Live2D集成测试类"""
    
    def __init__(self):
        self.test_results = []
        self.logger = logging.getLogger("Live2DTest")
        
    def add_test_result(self, test_name: str, success: bool, message: str = ""):
        """添加测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        self.logger.info(f"{status} {test_name}: {message}")
        
    def test_module_imports(self):
        """测试模块导入"""
        try:
            # 测试配置系统
            from config import config
            self.add_test_result("配置系统导入", True, "配置系统导入成功")
            
            # 测试Live2D模块
            from live2d_module import (
                init_live2d_module, get_live2d_status, check_dependencies,
                event_bus, create_emotion_event, create_ai_response_event
            )
            self.add_test_result("Live2D模块导入", True, "Live2D模块导入成功")
            
            # 测试配置访问
            live2d_config = config.ui.live2d
            self.add_test_result("Live2D配置访问", True, f"Live2D配置访问成功: {live2d_config.enabled}")
            
            return True
            
        except ImportError as e:
            self.add_test_result("模块导入", False, f"导入失败: {e}")
            return False
        except Exception as e:
            self.add_test_result("模块导入", False, f"未知错误: {e}")
            return False
    
    def test_dependencies(self):
        """测试依赖项"""
        try:
            from live2d_module import check_dependencies, get_missing_dependencies
            
            deps = check_dependencies()
            missing = get_missing_dependencies()
            
            self.logger.info(f"依赖项状态: {deps}")
            self.logger.info(f"缺失依赖项: {missing}")
            
            if missing:
                self.add_test_result("依赖项检查", False, f"缺失依赖项: {missing}")
                return False
            else:
                self.add_test_result("依赖项检查", True, "所有依赖项都可用")
                return True
                
        except Exception as e:
            self.add_test_result("依赖项检查", False, f"检查失败: {e}")
            return False
    
    def test_configuration(self):
        """测试配置"""
        try:
            from config import config
            
            # 测试Live2D配置
            live2d_config = config.ui.live2d
            
            # 检查必要配置项
            required_fields = [
                'enabled', 'model_path', 'scale', 'offset_x', 'offset_y',
                'emotion_analysis', 'lip_sync', 'tts_enabled', 'asr_enabled'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not hasattr(live2d_config, field):
                    missing_fields.append(field)
            
            if missing_fields:
                self.add_test_result("配置检查", False, f"缺失配置项: {missing_fields}")
                return False
            
            self.add_test_result("配置检查", True, f"Live2D配置完整，启用状态: {live2d_config.enabled}")
            return True
            
        except Exception as e:
            self.add_test_result("配置检查", False, f"配置检查失败: {e}")
            return False
    
    async def test_event_system(self):
        """测试事件系统"""
        try:
            from live2d_module import event_bus, create_emotion_event, create_ai_response_event
            
            # 创建测试事件
            emotion_event = create_emotion_event("开心", 1.0, "测试情绪事件")
            ai_event = create_ai_response_event("test_session", "测试AI响应")
            
            # 测试事件发布
            await event_bus.publish("test_emotion", emotion_event)
            await event_bus.publish("test_ai", ai_event)
            
            # 测试事件历史
            history = event_bus.get_event_history()
            
            self.add_test_result("事件系统", True, f"事件系统正常，历史记录数: {len(history)}")
            return True
            
        except Exception as e:
            self.add_test_result("事件系统", False, f"事件系统测试失败: {e}")
            return False
    
    async def test_emotion_handler(self):
        """测试情绪处理器"""
        try:
            from live2d_module.emotion_handler import Live2DEmotionHandler
            
            # 创建情绪处理器
            emotion_config = {
                "enabled": True,
                "emotion_weights": {
                    "开心": 1.0,
                    "生气": 1.2,
                    "伤心": 1.1,
                    "惊讶": 1.3,
                    "害羞": 0.9,
                    "害怕": 1.0
                },
                "emotion_duration": {
                    "开心": 2.0,
                    "生气": 1.5,
                    "伤心": 3.0,
                    "惊讶": 1.0,
                    "害羞": 2.5,
                    "害怕": 2.0,
                    "neutral": 1.0
                }
            }
            
            handler = Live2DEmotionHandler(emotion_config)
            
            # 测试情绪分析
            test_texts = [
                "今天真开心！",
                "我感到很伤心。",
                "哇，太惊讶了！",
                "这让我很生气。",
                "有点害羞。"
            ]
            
            for text in test_texts:
                emotion, intensity = handler.analyze_emotion(text)
                self.logger.info(f"文本: '{text}' -> 情绪: {emotion}, 强度: {intensity}")
            
            self.add_test_result("情绪处理器", True, "情绪分析功能正常")
            return True
            
        except Exception as e:
            self.add_test_result("情绪处理器", False, f"情绪处理器测试失败: {e}")
            return False
    
    async def test_audio_adapter(self):
        """测试音频适配器"""
        try:
            from live2d_module.audio_integration import Live2DAudioAdapter
            
            # 创建音频适配器
            audio_config = {
                "tts_enabled": True,
                "asr_enabled": True,
                "tts_api_url": "http://127.0.0.1:8000/voice/speak",
                "asr_api_url": "http://127.0.0.1:8000/voice/transcribe",
                "enable_cache": True,
                "cache_dir": "test_audio_cache",
                "max_retries": 2,
                "retry_delay": 1.0
            }
            
            adapter = Live2DAudioAdapter(audio_config)
            
            # 测试配置获取
            config = adapter.get_config()
            self.logger.info(f"音频适配器配置: {config}")
            
            self.add_test_result("音频适配器", True, "音频适配器初始化成功")
            return True
            
        except Exception as e:
            self.add_test_result("音频适配器", False, f"音频适配器测试失败: {e}")
            return False
    
    def test_conversation_integration(self):
        """测试对话系统集成"""
        try:
            from conversation_core import NagaConversation
            
            # 创建对话实例
            conversation = NagaConversation()
            
            # 检查Live2D集成
            if hasattr(conversation, 'live2d_enabled'):
                self.add_test_result("对话集成", True, f"Live2D集成状态: {conversation.live2d_enabled}")
                return True
            else:
                self.add_test_result("对话集成", False, "Live2D集成属性不存在")
                return False
                
        except Exception as e:
            self.add_test_result("对话集成", False, f"对话集成测试失败: {e}")
            return False
    
    def test_main_integration(self):
        """测试主程序集成"""
        try:
            # 检查主程序是否能正常导入
            import main
            
            # 检查Live2D可用性标志
            if hasattr(main, 'LIVE2D_AVAILABLE'):
                self.add_test_result("主程序集成", True, f"Live2D可用性: {main.LIVE2D_AVAILABLE}")
                return True
            else:
                self.add_test_result("主程序集成", False, "Live2D可用性标志不存在")
                return False
                
        except Exception as e:
            self.add_test_result("主程序集成", False, f"主程序集成测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("=" * 50)
        self.logger.info("开始Live2D集成测试")
        self.logger.info("=" * 50)
        
        # 模块导入测试
        self.test_module_imports()
        
        # 配置测试
        self.test_configuration()
        
        # 依赖项测试
        self.test_dependencies()
        
        # 事件系统测试
        await self.test_event_system()
        
        # 情绪处理器测试
        await self.test_emotion_handler()
        
        # 音频适配器测试
        await self.test_audio_adapter()
        
        # 对话集成测试
        self.test_conversation_integration()
        
        # 主程序集成测试
        self.test_main_integration()
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        self.logger.info("=" * 50)
        self.logger.info("测试报告")
        self.logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        self.logger.info(f"总测试数: {total_tests}")
        self.logger.info(f"通过测试: {passed_tests}")
        self.logger.info(f"失败测试: {failed_tests}")
        self.logger.info(f"通过率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            self.logger.info("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    self.logger.info(f"  - {result['test_name']}: {result['message']}")
        
        # 保存测试报告
        report_path = Path("live2d_test_report.json")
        report_data = {
            "timestamp": asyncio.get_event_loop().time(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": (passed_tests/total_tests)*100,
            "test_results": self.test_results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n详细测试报告已保存到: {report_path}")
        
        return failed_tests == 0

async def main():
    """主函数"""
    setup_logging()
    
    test = Live2DIntegrationTest()
    success = await test.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！Live2D集成成功！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)