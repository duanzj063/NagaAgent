#!/usr/bin/env python3
"""
Live2D基本功能测试脚本
无需额外依赖，测试基本功能
"""

import os
import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_model_files():
    """测试模型文件是否存在"""
    logger.info("测试Live2D模型文件...")
    
    model_paths = [
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.model3.json",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.moc3",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.physics3.json",
        "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.pose3.json",
    ]
    
    existing_files = []
    missing_files = []
    
    for model_path in model_paths:
        full_path = project_root / model_path
        if full_path.exists():
            size = full_path.stat().st_size
            existing_files.append(f"✅ {model_path} ({size} bytes)")
            logger.info(f"找到模型文件: {model_path} ({size} bytes)")
        else:
            missing_files.append(f"❌ {model_path}")
            logger.warning(f"缺失模型文件: {model_path}")
    
    return existing_files, missing_files

def test_motion_files():
    """测试动作文件"""
    logger.info("测试Live2D动作文件...")
    
    motion_dir = project_root / "live2d_module/models/fake_neuro_live_2d/motions"
    if not motion_dir.exists():
        logger.warning("动作目录不存在")
        return [], ["动作目录不存在"]
    
    motion_files = list(motion_dir.glob("*.motion3.json"))
    existing_motions = []
    
    for motion_file in motion_files:
        size = motion_file.stat().st_size
        relative_path = motion_file.relative_to(project_root)
        existing_motions.append(f"✅ {relative_path} ({size} bytes)")
        logger.info(f"找到动作文件: {relative_path} ({size} bytes)")
    
    return existing_motions, []

def test_texture_files():
    """测试纹理文件"""
    logger.info("测试Live2D纹理文件...")
    
    texture_dir = project_root / "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.2048"
    if not texture_dir.exists():
        logger.warning("纹理目录不存在")
        return [], ["纹理目录不存在"]
    
    texture_files = list(texture_dir.glob("*.png"))
    existing_textures = []
    
    for texture_file in texture_files:
        size = texture_file.stat().st_size
        relative_path = texture_file.relative_to(project_root)
        existing_textures.append(f"✅ {relative_path} ({size} bytes)")
        logger.info(f"找到纹理文件: {relative_path} ({size} bytes)")
    
    return existing_textures, []

def test_module_imports():
    """测试模块导入（基本模块）"""
    logger.info("测试模块导入...")
    
    basic_modules = [
        "os", "sys", "json", "logging", "pathlib", 
        "asyncio", "typing", "datetime", "enum"
    ]
    
    successful_imports = []
    failed_imports = []
    
    for module in basic_modules:
        try:
            __import__(module)
            successful_imports.append(f"✅ {module}")
            logger.info(f"成功导入: {module}")
        except ImportError as e:
            failed_imports.append(f"❌ {module}: {e}")
            logger.error(f"导入失败: {module}: {e}")
    
    return successful_imports, failed_imports

def test_live2d_module_imports():
    """测试Live2D模块导入"""
    logger.info("测试Live2D模块导入...")
    
    live2d_modules = [
        "live2d_module",
        "live2d_module.event_adapter", 
        "live2d_module.emotion_handler",
        "live2d_module.audio_integration"
    ]
    
    successful_imports = []
    failed_imports = []
    
    for module in live2d_modules:
        try:
            __import__(module)
            successful_imports.append(f"✅ {module}")
            logger.info(f"成功导入: {module}")
        except ImportError as e:
            failed_imports.append(f"❌ {module}: {e}")
            logger.error(f"导入失败: {module}: {e}")
    
    return successful_imports, failed_imports

def test_configuration():
    """测试配置文件"""
    logger.info("测试配置...")
    
    config_files = [
        "config.py",
        "config.json.example",
        "requirements.txt",
        "pyproject.toml"
    ]
    
    existing_configs = []
    missing_configs = []
    
    for config_file in config_files:
        full_path = project_root / config_file
        if full_path.exists():
            size = full_path.stat().st_size
            existing_configs.append(f"✅ {config_file} ({size} bytes)")
            logger.info(f"找到配置文件: {config_file} ({size} bytes)")
        else:
            missing_configs.append(f"❌ {config_file}")
            logger.warning(f"缺失配置文件: {config_file}")
    
    return existing_configs, missing_configs

def generate_report():
    """生成测试报告"""
    logger.info("生成测试报告...")
    
    report = {
        "timestamp": str(datetime.datetime.now()),
        "test_results": {}
    }
    
    # 运行所有测试
    report["test_results"]["model_files"] = {
        "existing": test_model_files()[0],
        "missing": test_model_files()[1]
    }
    
    report["test_results"]["motion_files"] = {
        "existing": test_motion_files()[0],
        "missing": test_motion_files()[1]
    }
    
    report["test_results"]["texture_files"] = {
        "existing": test_texture_files()[0],
        "missing": test_texture_files()[1]
    }
    
    report["test_results"]["basic_imports"] = {
        "successful": test_module_imports()[0],
        "failed": test_module_imports()[1]
    }
    
    report["test_results"]["live2d_imports"] = {
        "successful": test_live2d_module_imports()[0],
        "failed": test_live2d_module_imports()[1]
    }
    
    report["test_results"]["configuration"] = {
        "existing": test_configuration()[0],
        "missing": test_configuration()[1]
    }
    
    # 计算统计信息
    total_tests = 0
    passed_tests = 0
    
    for category, results in report["test_results"].items():
        if "existing" in results:
            total_tests += len(results["existing"]) + len(results.get("missing", []))
            passed_tests += len(results["existing"])
        if "successful" in results:
            total_tests += len(results["successful"]) + len(results.get("failed", []))
            passed_tests += len(results["successful"])
    
    report["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
    }
    
    # 保存报告
    report_path = project_root / "live2d_basic_test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"测试报告已保存到: {report_path}")
    
    return report

def print_summary(report):
    """打印测试摘要"""
    print("\n" + "="*60)
    print("Live2D基本功能测试报告")
    print("="*60)
    
    summary = report["summary"]
    print(f"总测试数: {summary['total_tests']}")
    print(f"通过测试: {summary['passed_tests']}")
    print(f"通过率: {summary['pass_rate']:.1f}%")
    
    print("\n测试详情:")
    for category, results in report["test_results"].items():
        print(f"\n{category}:")
        
        if "existing" in results:
            print(f"  现有文件: {len(results['existing'])}")
            for item in results["existing"][:3]:  # 只显示前3个
                print(f"    {item}")
            if len(results["existing"]) > 3:
                print(f"    ... 还有 {len(results['existing']) - 3} 个文件")
        
        if "missing" in results and results["missing"]:
            print(f"  缺失文件: {len(results['missing'])}")
            for item in results["missing"]:
                print(f"    {item}")
        
        if "successful" in results:
            print(f"  成功导入: {len(results['successful'])}")
            for item in results["successful"][:3]:  # 只显示前3个
                print(f"    {item}")
            if len(results["successful"]) > 3:
                print(f"    ... 还有 {len(results['successful']) - 3} 个模块")
        
        if "failed" in results and results["failed"]:
            print(f"  导入失败: {len(results['failed'])}")
            for item in results["failed"]:
                print(f"    {item}")

if __name__ == "__main__":
    try:
        import datetime
        report = generate_report()
        print_summary(report)
        
        if report["summary"]["pass_rate"] >= 70:
            print("\n✅ 基本功能测试通过！")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败，请检查上述问题")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"\n❌ 测试运行失败: {e}")
        sys.exit(1)