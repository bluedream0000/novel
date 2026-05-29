# -*- coding: utf-8 -*-
"""设置页面 - 美化版"""
import json
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle

from config import DEFAULT_FONT

# 配色方案 - 与书架页面一致
COLORS = {
    'primary': (0.26, 0.47, 0.85, 1),
    'primary_light': (0.4, 0.6, 0.95, 1),
    'secondary': (0.95, 0.96, 0.98, 1),
    'card_bg': (1, 1, 1, 1),
    'text_primary': (0.2, 0.2, 0.2, 1),
    'text_secondary': (0.5, 0.5, 0.5, 1),
}

FONT_SIZES = {'small': '小', 'medium': '中', 'large': '大', 'extra_large': '特大'}
THEMES = {'light': '浅色', 'dark': '深色', 'sepia': '护眼'}


class SettingsScreen(Screen):
    """设置页面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = self._load_settings()
        self.build_ui()

    def _settings_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reader_settings.json')

    def _load_settings(self):
        p = self._settings_path()
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {'theme': 'light', 'font_size': 'medium'}

    def _save_settings(self):
        try:
            with open(self._settings_path(), 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def build_ui(self):
        """构建 UI"""
        self.root_layout = BoxLayout(orientation='vertical', padding=0, spacing=0)
        with self.root_layout.canvas.before:
            Color(*COLORS['secondary'])
            self.bg_rect = Rectangle(pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)

        # 顶部标题栏
        header = BoxLayout(
            size_hint_y=None,
            height=60,
            padding=(15, 10),
            spacing=10
        )
        with header.canvas.before:
            Color(*COLORS['primary'])
            self.header_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self._update_header, size=self._update_header)

        back_btn = Button(
            text='< 返回',
            font_size=16,
            size_hint_x=None,
            width=70,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_name=DEFAULT_FONT
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'bookshelf'))

        title = Label(
            text='设置',
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            font_name=DEFAULT_FONT,
            halign='left',
            text_size=(200, None)
        )

        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(Widget())
        self.root_layout.add_widget(header)

        # 内容区域
        content = BoxLayout(
            orientation='vertical',
            padding=(15, 15),
            spacing=15
        )

        # 阅读设置卡片
        read_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=200,
            padding=(15, 15),
            spacing=15
        )
        with read_card.canvas.before:
            Color(*COLORS['card_bg'])
            self.read_rect = RoundedRectangle(pos=read_card.pos, size=read_card.size, radius=[8])
            Color(0.9, 0.9, 0.9, 1)
            self.read_border = RoundedRectangle(
                pos=(read_card.pos[0]-1, read_card.pos[1]-1),
                size=(read_card.size[0]+2, read_card.size[1]+2),
                radius=[8]
            )
        read_card.bind(pos=self._update_read_card, size=self._update_read_card)

        read_card.add_widget(Label(
            text='阅读设置',
            font_name=DEFAULT_FONT,
            font_size=16,
            bold=True,
            color=COLORS['primary'],
            size_hint_y=None,
            height=30,
            halign='left'
        ))

        # 字体大小
        font_row = BoxLayout(size_hint_y=None, height=45, spacing=8)
        font_row.add_widget(Label(
            text='字体大小:',
            font_name=DEFAULT_FONT,
            font_size=13,
            color=COLORS['text_secondary'],
            size_hint_x=None,
            width=80
        ))
        for key, label in FONT_SIZES.items():
            btn = Button(
                text=label,
                font_name=DEFAULT_FONT,
                font_size=13
            )
            if key == self.settings.get('font_size', 'medium'):
                btn.background_color = COLORS['primary']
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (0.9, 0.9, 0.9, 1)
                btn.color = COLORS['text_primary']
            btn.bind(on_press=lambda x, s=key: self._set_font(s))
            font_row.add_widget(btn)
        read_card.add_widget(font_row)

        # 主题
        theme_row = BoxLayout(size_hint_y=None, height=45, spacing=8)
        theme_row.add_widget(Label(
            text='阅读主题:',
            font_name=DEFAULT_FONT,
            font_size=13,
            color=COLORS['text_secondary'],
            size_hint_x=None,
            width=80
        ))
        for key, label in THEMES.items():
            btn = Button(
                text=label,
                font_name=DEFAULT_FONT,
                font_size=13
            )
            if key == self.settings.get('theme', 'light'):
                btn.background_color = COLORS['primary']
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (0.9, 0.9, 0.9, 1)
                btn.color = COLORS['text_primary']
            btn.bind(on_press=lambda x, t=key: self._set_theme(t))
            theme_row.add_widget(btn)
        read_card.add_widget(theme_row)

        content.add_widget(read_card)

        # 关于卡片
        about_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=140,
            padding=(15, 15),
            spacing=10
        )
        with about_card.canvas.before:
            Color(*COLORS['card_bg'])
            self.about_rect = RoundedRectangle(pos=about_card.pos, size=about_card.size, radius=[8])
            Color(0.9, 0.9, 0.9, 1)
            self.about_border = RoundedRectangle(
                pos=(about_card.pos[0]-1, about_card.pos[1]-1),
                size=(about_card.size[0]+2, about_card.size[1]+2),
                radius=[8]
            )
        about_card.bind(pos=self._update_about_card, size=self._update_about_card)

        about_card.add_widget(Label(
            text='关于',
            font_name=DEFAULT_FONT,
            font_size=16,
            bold=True,
            color=COLORS['primary'],
            size_hint_y=None,
            height=30,
            halign='left'
        ))

        about_card.add_widget(Label(
            text='小说阅读器 Kivy版',
            font_name=DEFAULT_FONT,
            font_size=14,
            bold=True,
            color=COLORS['text_primary'],
            halign='left'
        ))
        about_card.add_widget(Label(
            text='版本: 1.0.0',
            font_name=DEFAULT_FONT,
            font_size=12,
            color=COLORS['text_secondary'],
            halign='left'
        ))
        about_card.add_widget(Label(
            text='纯本地运行，无需后端服务器',
            font_name=DEFAULT_FONT,
            font_size=12,
            color=COLORS['text_secondary'],
            halign='left'
        ))

        content.add_widget(about_card)

        self.root_layout.add_widget(content)
        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_header(self, instance, value):
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size

    def _update_read_card(self, instance, value):
        self.read_rect.pos = instance.pos
        self.read_rect.size = instance.size
        self.read_border.pos = (instance.pos[0]-1, instance.pos[1]-1)
        self.read_border.size = (instance.size[0]+2, instance.size[1]+2)

    def _update_about_card(self, instance, value):
        self.about_rect.pos = instance.pos
        self.about_rect.size = instance.size
        self.about_border.pos = (instance.pos[0]-1, instance.pos[1]-1)
        self.about_border.size = (instance.size[0]+2, instance.size[1]+2)

    def _set_font(self, size_name):
        self.settings['font_size'] = size_name
        self._save_settings()
        self.build_ui()  # 重建UI以更新选中状态

    def _set_theme(self, theme_name):
        self.settings['theme'] = theme_name
        self._save_settings()
        self.build_ui()
