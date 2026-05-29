# -*- coding: utf-8 -*-
"""
小说阅读器 - Kivy Android App
纯本地运行，无需后端服务器
"""
import os
import sys

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.text import LabelBase

# 加载 Kivy 配置
from kivy.config import Config
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kivy.ini')
if os.path.exists(config_path):
    Config.read(config_path)

# 导入配置
from config import DEFAULT_FONT, WINDOW_SIZE

# 设置窗口大小（开发时）
from kivy.core.window import Window
Window.size = WINDOW_SIZE

# 注册中文字体并设置为默认
if os.path.exists(DEFAULT_FONT):
    LabelBase.register(name='ChineseFont', fn_regular=DEFAULT_FONT)
    # 设置默认字体
    from kivy.uix.label import Label
    Label.font_name = DEFAULT_FONT
    from kivy.uix.button import Button
    Button.font_name = DEFAULT_FONT
    print(f"字体已加载: {DEFAULT_FONT}")
else:
    print(f"警告: 未找到字体文件 {DEFAULT_FONT}")
    print("请将 TTF 字体文件放入 fonts/ 目录")

# 导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入所有 Screen
from screens import (
    BookshelfScreen,
    SearchScreen,
    ReadScreen,
    CloudScreen,
    SettingsScreen,
    CatalogueScreen,
)


class NovelReaderApp(App):
    """小说阅读器 App"""
    def build(self):
        """构建应用"""
        # 设置主题颜色
        self.theme_cls = None

        # 创建屏幕管理器
        sm = ScreenManager()
        sm.add_widget(BookshelfScreen(name='bookshelf'))
        sm.add_widget(SearchScreen(name='search'))
        sm.add_widget(ReadScreen(name='read'))
        sm.add_widget(CloudScreen(name='cloud'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(CatalogueScreen(name='catalogue'))

        return sm


if __name__ == '__main__':
    NovelReaderApp().run()
