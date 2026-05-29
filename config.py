# -*- coding: utf-8 -*-
"""应用配置常量"""
import os

# 项目根目录（kivy_app 的上级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 字体配置
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
DEFAULT_FONT = os.path.join(FONT_DIR, 'AaBianYaKai.ttf')

# 字体大小配置（参考手机常用尺寸）
FONT_SIZES = {
    'xs': 12,      # 超小字（辅助信息）
    'sm': 14,      # 小字（标签、提示）
    'md': 16,      # 中等（正文、按钮）
    'lg': 18,      # 大字（标题、重要信息）
    'xl': 20,      # 超大字（页面标题）
    'xxl': 24,     # 特大字（大标题）
}

# 窗口配置（开发时）
WINDOW_SIZE = (400, 700)
