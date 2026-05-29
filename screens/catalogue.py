# -*- coding: utf-8 -*-
"""目录页面 - 独立页面"""
import json
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window

from config import DEFAULT_FONT
from database import DatabaseManager

# 配色方案 - 与书架页面一致
COLORS = {
    'primary': (0.26, 0.47, 0.85, 1),
    'primary_light': (0.4, 0.6, 0.95, 1),
    'secondary': (0.95, 0.96, 0.98, 1),
    'card_bg': (1, 1, 1, 1),
    'text_primary': (0.2, 0.2, 0.2, 1),
    'text_secondary': (0.5, 0.5, 0.5, 1),
}


class CatalogueScreen(Screen):
    """独立目录页面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.current_book_id = None
        self.book_name = ''
        self.catalogue = []
        self.catalogue_len = 0
        self.current_chapter = 0
        self.build_ui()

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
        back_btn.bind(on_press=self.on_back)

        self.title_label = Label(
            text='目录',
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            font_name=DEFAULT_FONT,
            halign='left',
            text_size=(200, None)
        )

        header.add_widget(back_btn)
        header.add_widget(self.title_label)
        header.add_widget(Widget())
        self.root_layout.add_widget(header)

        # 书籍信息条
        self.book_info_bar = BoxLayout(
            size_hint_y=None,
            height=45,
            padding=(15, 8),
            spacing=10
        )
        with self.book_info_bar.canvas.before:
            Color(*COLORS['card_bg'])
            self.info_rect = Rectangle(pos=self.book_info_bar.pos, size=self.book_info_bar.size)
            Color(0.9, 0.9, 0.9, 1)
            self.info_line = Rectangle(
                pos=(self.book_info_bar.pos[0], self.book_info_bar.pos[1]),
                size=(self.book_info_bar.size[0], 1)
            )
        self.book_info_bar.bind(pos=self._update_info, size=self._update_info)

        self.book_info_label = Label(
            text='选择一本书查看目录',
            font_size=13,
            color=COLORS['text_secondary'],
            font_name=DEFAULT_FONT,
            halign='left'
        )
        self.chapter_count_label = Label(
            text='',
            font_size=13,
            color=COLORS['primary'],
            font_name=DEFAULT_FONT,
            halign='right'
        )
        self.book_info_bar.add_widget(self.book_info_label)
        self.book_info_bar.add_widget(self.chapter_count_label)
        self.root_layout.add_widget(self.book_info_bar)

        # 章节列表
        self.chapters_layout = GridLayout(
            cols=1,
            spacing=2,
            size_hint_y=None,
            padding=(10, 5)
        )
        self.chapters_layout.bind(minimum_height=self.chapters_layout.setter('height'))

        scroll = ScrollView()
        scroll.add_widget(self.chapters_layout)
        self.root_layout.add_widget(scroll)

        # 底部导航
        bottom_bar = BoxLayout(
            size_hint_y=None,
            height=55,
            padding=(15, 8),
            spacing=10
        )
        with bottom_bar.canvas.before:
            Color(*COLORS['card_bg'])
            self.bottom_rect = Rectangle(pos=bottom_bar.pos, size=bottom_bar.size)
            Color(0.9, 0.9, 0.9, 1)
            self.bottom_line = Rectangle(
                pos=(bottom_bar.pos[0], bottom_bar.pos[1] + bottom_bar.size[1] - 1),
                size=(bottom_bar.size[0], 1)
            )
        bottom_bar.bind(pos=self._update_bottom, size=self._update_bottom)

        self.chapter_info_label = Label(
            text='',
            font_size=13,
            color=COLORS['text_secondary'],
            font_name=DEFAULT_FONT
        )

        prev_btn = Button(
            text='< 上一章',
            font_name=DEFAULT_FONT,
            size_hint_x=None,
            width=90,
            background_color=COLORS['primary_light'],
            color=(1, 1, 1, 1)
        )
        prev_btn.bind(on_press=self.prev_chapter)

        next_btn = Button(
            text='下一章 >',
            font_name=DEFAULT_FONT,
            size_hint_x=None,
            width=90,
            background_color=COLORS['primary'],
            color=(1, 1, 1, 1)
        )
        next_btn.bind(on_press=self.next_chapter)

        bottom_bar.add_widget(prev_btn)
        bottom_bar.add_widget(self.chapter_info_label)
        bottom_bar.add_widget(next_btn)
        self.root_layout.add_widget(bottom_bar)

        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_header(self, instance, value):
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size

    def _update_info(self, instance, value):
        self.info_rect.pos = instance.pos
        self.info_rect.size = instance.size
        self.info_line.pos = (instance.pos[0], instance.pos[1])
        self.info_line.size = (instance.size[0], 1)

    def _update_bottom(self, instance, value):
        self.bottom_rect.pos = instance.pos
        self.bottom_rect.size = instance.size
        self.bottom_line.pos = (instance.pos[0], instance.pos[1] + instance.size[1] - 1)
        self.bottom_line.size = (instance.size[0], 1)

    def load_book(self, book_id):
        """加载书籍目录"""
        self.current_book_id = book_id
        self.chapters_layout.clear_widgets()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT book_name, catalogue, catalogue_len, last_read_chapter FROM books WHERE id = ?', (book_id,))
        result = cursor.fetchone()

        if not result:
            self.book_info_label.text = '未找到书籍信息'
            conn.close()
            return

        self.book_name = result[0]
        catalogue_data = result[1]
        self.catalogue_len = result[2] or 0
        self.current_chapter = result[3] or 0

        self.title_label.text = f'{self.book_name} - 目录'
        self.book_info_label.text = self.book_name
        self.chapter_count_label.text = f'共 {self.catalogue_len} 章'
        self.chapter_info_label.text = f'{self.current_chapter + 1}/{self.catalogue_len}'

        if catalogue_data:
            try:
                self.catalogue = json.loads(catalogue_data)
            except Exception:
                self.catalogue = []
        else:
            self.catalogue = []

        # 获取已下载章节
        cursor.execute('SELECT chapter_index FROM chapters WHERE book_id = ?', (book_id,))
        downloaded_set = set(row[0] for row in cursor.fetchall())
        conn.close()

        if not self.catalogue:
            self.chapters_layout.add_widget(Label(
                text='暂无目录信息',
                font_name=DEFAULT_FONT,
                size_hint_y=None,
                height=60,
                color=COLORS['text_secondary']
            ))
            return

        for i, ch in enumerate(self.catalogue):
            name = ch.get('chapterName', f'第 {i + 1} 章')
            is_downloaded = (i + 1) in downloaded_set
            is_current = (i == self.current_chapter)

            row = BoxLayout(
                size_hint_y=None,
                height=48,
                padding=(15, 5),
                spacing=10
            )

            # 章节号
            num_label = Label(
                text=str(i + 1),
                font_size=12,
                color=COLORS['primary'] if is_current else COLORS['text_secondary'],
                font_name=DEFAULT_FONT,
                size_hint_x=None,
                width=35,
                halign='center'
            )

            # 章节名
            name_label = Label(
                text=name,
                font_size=14,
                color=COLORS['primary'] if is_current else COLORS['text_primary'],
                font_name=DEFAULT_FONT,
                bold=is_current,
                halign='left',
                text_size=(Window.width - 140, None)
            )

            # 下载状态
            status_text = '已下载' if is_downloaded else '未下载'
            status_label = Label(
                text=status_text,
                font_size=11,
                color=(0.3, 0.7, 0.4, 1) if is_downloaded else (0.8, 0.6, 0.4, 1),
                font_name=DEFAULT_FONT,
                size_hint_x=None,
                width=55,
                halign='center'
            )

            # 当前章节背景高亮
            if is_current:
                with row.canvas.before:
                    Color(0.26, 0.47, 0.85, 0.08)
                    highlight = Rectangle(pos=row.pos, size=row.size)
                row.bind(pos=lambda inst, val, h=highlight: setattr(h, 'pos', inst.pos))
                row.bind(size=lambda inst, val, h=highlight: setattr(h, 'size', inst.size))

            row.add_widget(num_label)
            row.add_widget(name_label)
            row.add_widget(status_label)

            row.bind(on_press=lambda inst, idx=i: self.on_chapter_select(idx))
            self.chapters_layout.add_widget(row)

        # 滚动到当前章节
        if self.current_chapter > 5:
            Clock.schedule_once(lambda dt: self._scroll_to_current(), 0.1)

    def _scroll_to_current(self):
        """滚动到当前章节"""
        scroll = self.chapters_layout.parent
        if scroll and self.catalogue_len > 0:
            item_height = 48 + 2  # height + spacing
            total_height = self.chapters_layout.minimum_height
            visible_height = scroll.height
            target_y = (self.current_chapter * item_height) / total_height
            scroll.scroll_y = max(0, min(1, target_y))

    def on_chapter_select(self, chapter_index):
        """选择章节 - 进入阅读"""
        if not self.current_book_id:
            return
        read_screen = self.manager.get_screen('read')
        read_screen.load_book(self.current_book_id)
        # 直接跳到选中章节
        Clock.schedule_once(lambda dt: read_screen.load_chapter(chapter_index), 0.2)
        self.manager.current = 'read'

    def prev_chapter(self, instance):
        if self.current_chapter > 0:
            self.on_chapter_select(self.current_chapter - 1)

    def next_chapter(self, instance):
        if self.current_chapter < self.catalogue_len - 1:
            self.on_chapter_select(self.current_chapter + 1)

    def on_back(self, instance):
        self.manager.current = 'bookshelf'
