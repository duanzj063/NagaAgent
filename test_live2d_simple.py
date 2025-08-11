#!/usr/bin/env python3
"""
简化的Live2D显示测试
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from live2d_module.naga_live2d_model import start_naga_live2d

def test_live2d_display():
    """测试Live2D显示功能"""
    print("=== Live2D显示测试 ===")
    
    # 创建QApplication
    app = QApplication(sys.argv)
    
    # 准备Live2D配置
    live2d_config = {
        "model_path": "live2d_module/models/fake_neuro_live_2d/hiyori_pro_mic.model3.json",
        "scale": 1.0,
        "offset_x": 1050,
        "offset_y": 600,
        "enabled": True
    }
    
    try:
        print("正在启动Live2D人物...")
        live2d_app, live2d_model = start_naga_live2d(live2d_config, blocking=False)
        
        if live2d_app and live2d_model:
            print("Live2D人物启动成功！")
            print("功能提示：")
            print("- 使用Ctrl+1~9播放动作")
            print("- 使用Ctrl+U切换动作")
            print("- 鼠标拖拽移动人物")
            print("- 滚轮缩放大小")
            print("- 点击关闭按钮退出")
            
            # 运行应用
            exit_code = app.exec_()
            print(f"应用退出，代码: {exit_code}")
            return exit_code
        else:
            print("Live2D人物启动失败")
            return 1
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_live2d_display())