#!/usr/bin/env python3
"""
Live2D集成修复脚本
用于检测和修复Live2D集成问题
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装Live2D依赖"""
    print("🔧 安装Live2D依赖...")
    
    dependencies = [
        "live2d-v3",
        "pyopengl", 
        "pyopengl-accelerate",
        "pygame",
        "numpy",
        "aiohttp"
    ]
    
    for dep in dependencies:
        try:
            print(f"   安装 {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"   ✅ {dep} 安装成功")
        except subprocess.CalledProcessError:
            print(f"   ❌ {dep} 安装失败")
            return False
    
    return True

def check_model_files():
    """检查模型文件"""
    print("📁 检查模型文件...")
    
    model_paths = [
        "live2d_module/models/hiyori_pro_mic.model3.json",
        "live2d_module/models/hiyori_pro_mic.moc3",
        "models/hiyori_pro_mic.model3.json"
    ]
    
    found_models = []
    for path in model_paths:
        if os.path.exists(path):
            found_models.append(path)
            print(f"   ✅ 找到模型: {path}")
    
    if not found_models:
        print("   ❌ 未找到任何模型文件")
        print("   请确保将Live2D模型文件放在正确位置")
        return False
    
    return True

def update_config():
    """更新配置文件"""
    print("⚙️ 更新配置文件...")
    
    config_path = "config.json"
    if not os.path.exists(config_path):
        print("   ❌ config.json 不存在")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 确保Live2D配置存在并启用
        if "ui" not in config:
            config["ui"] = {}
        
        if "live2d" not in config["ui"]:
            config["ui"]["live2d"] = {
                "enabled": True,
                "model_path": "live2d_module/models/hiyori_pro_mic.model3.json",
                "emotion_analysis": True,
                "lip_sync": True,
                "tts_enabled": True,
                "asr_enabled": True,
                "scale": 1.0,
                "offset_x": 1050,
                "offset_y": 600
            }
        else:
            config["ui"]["live2d"]["enabled"] = True
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("   ✅ 配置已更新，Live2D已启用")
        return True
        
    except Exception as e:
        print(f"   ❌ 配置更新失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    print("📁 创建目录...")
    
    directories = [
        "live2d_module/models",
        "live2d_cache",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ 创建目录: {directory}")
    
    return True

def check_my_neuro_source():
    """检查My-Neuro源文件"""
    print("🔍 检查My-Neuro源文件...")
    
    # 这里需要用户手动检查My-Neuro项目
    print("   请手动检查以下路径是否存在My-Neuro的Live2D文件：")
    print("   D:\\code\\pythonWork\\my-neuro\\UI\\2D\\")
    print("   D:\\code\\pythonWork\\my-neuro\\live-2d\\")
    
    # 检查是否可以复制
    my_neuro_paths = [
        "D:/code/pythonWork/my-neuro/UI/2D",
        "D:/code/pythonWork/my-neuro/live-2d"
    ]
    
    for path in my_neuro_paths:
        if os.path.exists(path):
            print(f"   ✅ 找到My-Neuro路径: {path}")
            print(f"   请手动复制该目录下的文件到 NagaAgent/live2d_module/models/")
    
    return True

def run_test():
    """运行测试"""
    print("🧪 运行Live2D集成测试...")
    
    try:
        subprocess.check_call([sys.executable, "test_live2d_integration.py"])
        return True
    except subprocess.CalledProcessError:
        print("   ❌ 测试失败")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Live2D集成修复工具")
    print("=" * 60)
    
    steps = [
        ("检查Python版本", check_python_version),
        ("创建必要目录", create_directories),
        ("安装依赖", install_dependencies),
        ("检查模型文件", check_model_files),
        ("更新配置", update_config),
        ("检查My-Neuro源", check_my_neuro_source),
        ("运行测试", run_test)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n🔍 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 60)
    if failed_steps:
        print("❌ 以下步骤失败:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n请手动解决上述问题后重新运行此脚本")
        return 1
    else:
        print("🎉 所有步骤完成！Live2D集成应该可以正常工作了")
        return 0

if __name__ == "__main__":
    sys.exit(main())