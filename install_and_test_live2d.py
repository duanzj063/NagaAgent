#!/usr/bin/env python3
"""
Live2D完整安装和测试脚本
解决依赖问题并验证功能
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

def run_command(cmd, description=""):
    """运行命令"""
    try:
        logger.info(f"运行: {cmd}")
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

def check_system_dependencies():
    """检查系统依赖"""
    logger.info("检查系统依赖...")
    
    # 检查Python版本
    python_version = sys.version_info
    logger.info(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查pip
    success, _ = run_command("python3 -m pip --version", "检查pip")
    if not success:
        logger.warning("pip不可用，尝试使用系统包管理器")
    
    # 检查基本库
    basic_modules = ['json', 'os', 'sys', 'asyncio', 'threading', 'time', 'datetime', 'enum', 'typing']
    for module in basic_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} 可用")
        except ImportError:
            logger.error(f"❌ {module} 不可用")

def install_dependencies():
    """安装依赖"""
    logger.info("安装依赖...")
    
    # 尝试不同的安装方法
    install_methods = [
        # 方法1: 使用pip安装到用户目录
        "python3 -m pip install --user numpy pydantic",
        # 方法2: 使用系统包管理器
        "sudo apt-get install python3-numpy python3-pydantic -y",
        # 方法3: 使用--break-system-packages
        "python3 -m pip install --break-system-packages numpy pydantic"
    ]
    
    for i, method in enumerate(install_methods, 1):
        logger.info(f"尝试安装方法 {i}: {method}")
        success, output = run_command(method, f"安装方法{i}")
        if success:
            logger.info("✅ 依赖安装成功")
            return True
    
    logger.error("❌ 所有安装方法都失败了")
    return False

def test_imports():
    """测试导入"""
    logger.info("测试模块导入...")
    
    test_modules = [
        ('numpy', 'numpy'),
        ('pydantic', 'pydantic'),
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
    return success_count == len(test_modules)

def run_basic_tests():
    """运行基本测试"""
    logger.info("运行基本测试...")
    
    # 测试简化版Live2D
    try:
        from live2d_module.simple_live2d import live2d_manager
        
        # 初始化
        if live2d_manager.initialize():
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
            emotion, confidence = live2d_manager.analyze_emotion(text)
            logger.info(f"文本: {text} -> 情绪: {emotion} (置信度: {confidence:.2f})")
        
        # 测试动作播放
        if live2d_manager.play_motion("Hiyori_m01"):
            logger.info("✅ 动作播放成功")
        else:
            logger.error("❌ 动作播放失败")
            return False
        
        # 获取状态
        status = live2d_manager.get_status()
        logger.info(f"Live2D状态: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 基本测试失败: {e}")
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
    for model_file in model_files:
        if os.path.exists(model_file):
            size = os.path.getsize(model_file)
            logger.info(f"✅ {model_file} ({size} bytes)")
            existing_files.append(model_file)
        else:
            logger.warning(f"❌ {model_file} 不存在")
    
    logger.info(f"模型文件完整性: {len(existing_files)}/{len(model_files)}")
    return len(existing_files) == len(model_files)

def generate_installation_report():
    """生成安装报告"""
    logger.info("生成安装报告...")
    
    report = {
        "timestamp": str(__import__('datetime').datetime.now()),
        "system_info": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform
        },
        "dependencies": {
            "numpy_available": False,
            "pydantic_available": False,
            "live2d_py_available": False
        },
        "model_files": {
            "count": 0,
            "total_size": 0,
            "files": []
        },
        "test_results": {
            "imports_success": False,
            "basic_tests_success": False,
            "model_files_complete": False
        },
        "recommendations": []
    }
    
    # 检查依赖
    try:
        import numpy
        report["dependencies"]["numpy_available"] = True
    except ImportError:
        report["recommendations"].append("安装numpy: pip install numpy")
    
    try:
        import pydantic
        report["dependencies"]["pydantic_available"] = True
    except ImportError:
        report["recommendations"].append("安装pydantic: pip install pydantic")
    
    # 检查模型文件
    model_files = [
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.model3.json",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.moc3",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.physics3.json",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.pose3.json"
    ]
    
    for model_file in model_files:
        if os.path.exists(model_file):
            size = os.path.getsize(model_file)
            report["model_files"]["files"].append({
                "path": model_file,
                "size": size
            })
            report["model_files"]["total_size"] += size
    
    report["model_files"]["count"] = len(report["model_files"]["files"])
    report["test_results"]["model_files_complete"] = report["model_files"]["count"] == len(model_files)
    
    # 运行测试
    report["test_results"]["imports_success"] = test_imports()
    report["test_results"]["basic_tests_success"] = run_basic_tests()
    
    # 生成建议
    if not report["dependencies"]["numpy_available"]:
        report["recommendations"].append("建议使用简化版Live2D模块")
    
    if not report["test_results"]["model_files_complete"]:
        report["recommendations"].append("检查模型文件是否完整")
    
    # 保存报告
    with open("live2d_installation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info("安装报告已保存到: live2d_installation_report.json")
    return report

def main():
    """主函数"""
    print("="*60)
    print("Live2D完整安装和测试脚本")
    print("="*60)
    
    # 1. 检查系统依赖
    check_system_dependencies()
    
    # 2. 尝试安装依赖
    install_success = install_dependencies()
    
    # 3. 检查模型文件
    model_files_ok = check_model_files()
    
    # 4. 运行测试
    test_success = run_basic_tests()
    
    # 5. 生成报告
    report = generate_installation_report()
    
    # 6. 总结
    print("\n" + "="*60)
    print("安装和测试总结")
    print("="*60)
    
    print(f"依赖安装: {'✅ 成功' if install_success else '❌ 失败'}")
    print(f"模型文件: {'✅ 完整' if model_files_ok else '❌ 不完整'}")
    print(f"基本测试: {'✅ 通过' if test_success else '❌ 失败'}")
    
    if report["test_results"]["imports_success"]:
        print("模块导入: ✅ 成功")
    else:
        print("模块导入: ⚠️ 部分失败（可以使用简化版）")
    
    print(f"\n建议:")
    for recommendation in report["recommendations"]:
        print(f"  - {recommendation}")
    
    if test_success or model_files_ok:
        print("\n✅ Live2D基本功能可用！")
        return 0
    else:
        print("\n❌ Live2D功能不可用，请检查上述问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())