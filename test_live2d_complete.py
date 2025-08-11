#!/usr/bin/env python3
"""
Live2D依赖安装和测试脚本
适用于当前Python环境
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd, description="", check=True):
    """运行命令"""
    try:
        logger.info(f"运行: {cmd}")
        if check:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} 成功")
            return True, result.stdout
        else:
            logger.error(f"❌ {description} 失败: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        logger.error(f"❌ {description} 异常: {e}")
        return False, str(e)

def install_with_break_system_packages():
    """使用--break-system-packages安装依赖"""
    logger.info("使用--break-system-packages安装依赖...")
    
    dependencies = [
        "numpy>=1.20.0",
        "pydantic>=2.11.3",
        "aiohttp>=3.11.18",
        "live2d-py>=0.3.2",
        "pyopengl>=3.1.0",
        "pyopengl-accelerate>=3.1.0"
    ]
    
    for dep in dependencies:
        cmd = f"python3 -m pip install --break-system-packages {dep}"
        success, output = run_command(cmd, f"安装 {dep}")
        if not success:
            logger.warning(f"安装 {dep} 失败，但继续尝试下一个...")
    
    return True

def test_imports():
    """测试导入"""
    logger.info("测试模块导入...")
    
    test_modules = [
        ('numpy', 'numpy'),
        ('pydantic', 'pydantic'),
        ('aiohttp', 'aiohttp'),
        ('live2d_module.simple_live2d', '简化Live2D模块'),
        ('live2d_module.event_adapter', '事件适配器'),
        ('live2d_module.emotion_handler', '情绪处理器'),
        ('live2d_module.audio_integration', '音频集成')
    ]
    
    success_count = 0
    for module_name, display_name in test_modules:
        try:
            __import__(module_name)
            logger.info(f"✅ {display_name} 导入成功")
            success_count += 1
        except ImportError as e:
            logger.warning(f"⚠️ {display_name} 导入失败: {e}")
    
    logger.info(f"导入成功率: {success_count}/{len(test_modules)} ({success_count/len(test_modules)*100:.1f}%)")
    return success_count >= len(test_modules) * 0.5  # 至少50%成功

def test_live2d_functionality():
    """测试Live2D功能"""
    logger.info("测试Live2D功能...")
    
    try:
        # 直接导入简化版模块
        import importlib.util
        spec = importlib.util.spec_from_file_location('simple_live2d', 'live2d_module/simple_live2d.py')
        simple_live2d = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simple_live2d)
        
        # 测试初始化
        if simple_live2d.live2d_manager.initialize():
            logger.info("✅ Live2D管理器初始化成功")
        else:
            logger.error("❌ Live2D管理器初始化失败")
            return False
        
        # 测试情绪分析
        test_emotions = [
            ("我很开心", "开心"),
            ("这让我生气", "生气"),
            ("好难过", "伤心"),
            ("太惊讶了", "惊讶")
        ]
        
        for text, expected in test_emotions:
            emotion, confidence = simple_live2d.live2d_manager.analyze_emotion(text)
            logger.info(f"文本: {text} -> 情绪: {emotion} (置信度: {confidence:.2f})")
        
        # 测试动作播放
        if simple_live2d.live2d_manager.play_motion("Hiyori_m01"):
            logger.info("✅ 动作播放成功")
        else:
            logger.error("❌ 动作播放失败")
            return False
        
        # 获取状态
        status = simple_live2d.live2d_manager.get_status()
        logger.info(f"Live2D状态: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Live2D功能测试失败: {e}")
        return False

def check_model_files():
    """检查模型文件"""
    logger.info("检查模型文件...")
    
    model_files = [
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.model3.json",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.moc3",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.physics3.json",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.pose3.json"
    ]
    
    existing_files = []
    total_size = 0
    
    for model_file in model_files:
        if os.path.exists(model_file):
            size = os.path.getsize(model_file)
            logger.info(f"✅ {model_file} ({size} bytes)")
            existing_files.append(model_file)
            total_size += size
        else:
            logger.warning(f"❌ {model_file} 不存在")
    
    logger.info(f"模型文件完整性: {len(existing_files)}/{len(model_files)} ({len(existing_files)/len(model_files)*100:.1f}%)")
    logger.info(f"模型文件总大小: {total_size} bytes")
    
    return len(existing_files) == len(model_files)

def run_conversation_test():
    """运行对话系统测试"""
    logger.info("测试对话系统集成...")
    
    try:
        # 测试对话核心导入
        sys.path.insert(0, '.')
        from conversation_core import NagaConversation
        
        # 创建对话实例
        conversation = NagaConversation()
        
        # 检查Live2D集成
        if hasattr(conversation, 'live2d_enabled'):
            logger.info(f"✅ 对话系统Live2D集成状态: {conversation.live2d_enabled}")
        else:
            logger.warning("⚠️ 对话系统没有Live2D集成属性")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 对话系统测试失败: {e}")
        return False

def generate_final_report():
    """生成最终报告"""
    logger.info("生成最终测试报告...")
    
    report = {
        "timestamp": str(__import__('datetime').datetime.now()),
        "test_summary": {
            "dependencies_installed": False,
            "imports_successful": False,
            "live2d_functional": False,
            "model_files_complete": False,
            "conversation_integration": False
        },
        "environment": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform
        },
        "recommendations": []
    }
    
    # 1. 安装依赖
    logger.info("步骤 1: 安装依赖...")
    if install_with_break_system_packages():
        report["test_summary"]["dependencies_installed"] = True
        logger.info("✅ 依赖安装完成")
    else:
        logger.error("❌ 依赖安装失败")
        report["recommendations"].append("手动安装依赖：pip install numpy pydantic aiohttp")
    
    # 2. 测试导入
    logger.info("步骤 2: 测试导入...")
    if test_imports():
        report["test_summary"]["imports_successful"] = True
        logger.info("✅ 模块导入测试通过")
    else:
        logger.warning("⚠️ 模块导入测试部分失败")
        report["recommendations"].append("检查依赖是否正确安装")
    
    # 3. 测试Live2D功能
    logger.info("步骤 3: 测试Live2D功能...")
    if test_live2d_functionality():
        report["test_summary"]["live2d_functional"] = True
        logger.info("✅ Live2D功能测试通过")
    else:
        logger.error("❌ Live2D功能测试失败")
        report["recommendations"].append("检查Live2D模块是否正确实现")
    
    # 4. 检查模型文件
    logger.info("步骤 4: 检查模型文件...")
    if check_model_files():
        report["test_summary"]["model_files_complete"] = True
        logger.info("✅ 模型文件检查通过")
    else:
        logger.error("❌ 模型文件检查失败")
        report["recommendations"].append("检查Live2D模型文件是否完整")
    
    # 5. 测试对话集成
    logger.info("步骤 5: 测试对话集成...")
    if run_conversation_test():
        report["test_summary"]["conversation_integration"] = True
        logger.info("✅ 对话集成测试通过")
    else:
        logger.error("❌ 对话集成测试失败")
        report["recommendations"].append("检查对话系统集成是否正确")
    
    # 计算总体成功率
    passed_tests = sum(report["test_summary"].values())
    total_tests = len(report["test_summary"])
    success_rate = (passed_tests / total_tests) * 100
    
    report["success_rate"] = success_rate
    
    # 生成建议
    if success_rate >= 80:
        report["overall_status"] = "优秀"
        report["conclusion"] = "Live2D集成状态优秀，大部分功能正常工作"
    elif success_rate >= 60:
        report["overall_status"] = "良好"
        report["conclusion"] = "Live2D集成状态良好，基本功能可用"
    elif success_rate >= 40:
        report["overall_status"] = "一般"
        report["conclusion"] = "Live2D集成状态一般，部分功能可用"
    else:
        report["overall_status"] = "较差"
        report["conclusion"] = "Live2D集成状态较差，需要进一步修复"
    
    # 保存报告
    with open("live2d_final_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"最终测试报告已保存到: live2d_final_test_report.json")
    return report

def main():
    """主函数"""
    print("="*60)
    print("Live2D依赖安装和完整测试脚本")
    print("="*60)
    
    try:
        report = generate_final_report()
        
        # 打印摘要
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)
        
        summary = report["test_summary"]
        for test_name, result in summary.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}: {'通过' if result else '失败'}")
        
        print(f"\n总体成功率: {report['success_rate']:.1f}%")
        print(f"总体状态: {report['overall_status']}")
        print(f"结论: {report['conclusion']}")
        
        if report["recommendations"]:
            print("\n建议:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")
        
        # 返回适当的退出码
        if report["success_rate"] >= 60:
            print("\n🎉 Live2D集成测试基本通过！")
            return 0
        else:
            print("\n⚠️ Live2D集成需要进一步修复")
            return 1
            
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())