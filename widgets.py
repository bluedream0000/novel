# -*- coding: utf-8 -*-
"""通用中文组件"""
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from config import DEFAULT_FONT

DEFAULT_FONT_NAME = DEFAULT_FONT


class ChineseLabel(Label):
    """支持中文的 Label 组件"""
    def __init__(self, **kwargs):
        # 设置默认字体
        if 'font_name' not in kwargs:
            kwargs['font_name'] = DEFAULT_FONT_NAME
        if 'font_size' not in kwargs:
            kwargs['font_size'] = 16
        super().__init__(**kwargs)


class ChineseButton(Button):
    """支持中文的 Button 组件"""
    def __init__(self, **kwargs):
        if 'font_name' not in kwargs:
            kwargs['font_name'] = DEFAULT_FONT_NAME
        if 'font_size' not in kwargs:
            kwargs['font_size'] = 14
        super().__init__(**kwargs)


class ChineseTextInput(TextInput):
    """支持中文的 TextInput 组件"""
    def __init__(self, **kwargs):
        if 'font_name' not in kwargs:
            kwargs['font_name'] = DEFAULT_FONT_NAME
        if 'font_size' not in kwargs:
            kwargs['font_size'] = 16
        super().__init__(**kwargs)
