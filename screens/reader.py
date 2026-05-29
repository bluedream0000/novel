# -*- coding: utf-8 -*-
"""阅读页面 - 高性能优化版本"""
import json
import os
import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

from config import DEFAULT_FONT, FONT_SIZES
from database import DatabaseManager

THEMES = {
    'light': {'bg': (0.96, 0.96, 0.94, 1), 'text': (0.2, 0.2, 0.2, 1)},
    'dark':  {'bg': (0.1, 0.1, 0.1, 1),  'text': (0.75, 0.75, 0.75, 1)},
    'sepia': {'bg': (0.96, 0.93, 0.85, 1), 'text': (0.37, 0.29, 0.2, 1)},
}
READER_FONT_SIZES = {'small': FONT_SIZES['sm'], 'medium': FONT_SIZES['md'], 'large': FONT_SIZES['lg'], 'extra_large': FONT_SIZES['xl']}


class ReadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.current_book_id = None
        self.current_chapter = 0
        self.catalogue = []
        self.catalogue_len = 0
        self.book_name = ''
        self._catalogue_popup = None
        self._loading = False
        self.settings = self._load_settings()
        self.font_size = READER_FONT_SIZES.get(self.settings.get('font_size', 'medium'), FONT_SIZES['md'])
        self.theme = self.settings.get('theme', 'light')
        # 缓存计算好的宽度
        self._content_width = 370
        self._pending_content = None
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
        # 主容器
        self.root_layout = BoxLayout(orientation='vertical')
        self.add_widget(self.root_layout)

        # 背景色
        self._bg_color = Color(*THEMES[self.theme]['bg'])
        self._bg_rect = Rectangle(pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.canvas.before.add(self._bg_color)
        self.root_layout.canvas.before.add(self._bg_rect)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)

        # 顶部工具栏
        self.toolbar = BoxLayout(size_hint_y=None, height=50, padding=(10, 5))
        back_btn = Button(text='< 返回', size_hint_x=None, width=80, font_name=DEFAULT_FONT)
        back_btn.bind(on_press=self.on_back)
        self.title_label = Label(
            text='阅读器',
            font_size=FONT_SIZES['md'],
            font_name=DEFAULT_FONT,
            color=THEMES[self.theme]['text'],
        )
        menu_btn = Button(text='菜单', size_hint_x=None, width=60, font_name=DEFAULT_FONT)
        menu_btn.bind(on_press=self.show_menu)
        self.toolbar.add_widget(back_btn)
        self.toolbar.add_widget(self.title_label)
        self.toolbar.add_widget(menu_btn)
        self.root_layout.add_widget(self.toolbar)

        # ScrollView
        self.scroll_view = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=0,
        )

        # 内容容器
        self.content_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=(15, 15),
            spacing=15,
        )

        # 章节标题
        self.chapter_title_label = Label(
            text='',
            font_size=FONT_SIZES['xl'],
            font_name=DEFAULT_FONT,
            size_hint_y=None,
            height=50,
            halign='center',
            color=THEMES[self.theme]['text'],
        )
        self.content_card.add_widget(self.chapter_title_label)

        # 分隔线
        self.separator = BoxLayout(size_hint_y=None, height=2)
        with self.separator.canvas.before:
            Color(0.8, 0.8, 0.8, 0.5)
            Rectangle(pos=self.separator.pos, size=self.separator.size)
        self.content_card.add_widget(self.separator)

        # 正文 - 关键优化：使用固定宽度，避免动态计算
        self.content_label = Label(
            text='',
            font_size=self.font_size,
            font_name=DEFAULT_FONT,
            halign='left',
            valign='top',
            size_hint=(None, None),
            color=THEMES[self.theme]['text'],
            text_size=(self._content_width, None),
        )
        self.content_label.bind(texture_size=self._on_texture_size)
        self.content_card.add_widget(self.content_label)

        self.scroll_view.add_widget(self.content_card)
        self.root_layout.add_widget(self.scroll_view)

        # 底部导航
        self.bottom_nav = BoxLayout(size_hint_y=None, height=50, padding=(5, 5), spacing=5)
        prev_btn = Button(text='< 上一章', font_name=DEFAULT_FONT)
        prev_btn.bind(on_press=self.prev_chapter)
        cat_btn = Button(text='目录', font_name=DEFAULT_FONT)
        cat_btn.bind(on_press=self.show_catalogue)
        self.chapter_info = Label(
            text='1/1',
            font_name=DEFAULT_FONT,
            color=THEMES[self.theme]['text'],
        )
        next_btn = Button(text='下一章 >', font_name=DEFAULT_FONT)
        next_btn.bind(on_press=self.next_chapter)
        self.bottom_nav.add_widget(prev_btn)
        self.bottom_nav.add_widget(cat_btn)
        self.bottom_nav.add_widget(self.chapter_info)
        self.bottom_nav.add_widget(next_btn)
        self.root_layout.add_widget(self.bottom_nav)

    def _update_bg(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _on_texture_size(self, instance, value):
        """纹理大小变化时更新容器高度"""
        if value[1] > 0:
            instance.size = value
            # 更新容器高度
            self.content_card.height = 50 + 2 + 15 + value[1] + 30

    def on_enter(self):
        """屏幕进入时更新宽度"""
        # 计算内容宽度，只执行一次
        self._content_width = max(Window.width - 30, 200)
        self.content_label.text_size = (self._content_width, None)

    def apply_theme(self):
        theme = THEMES.get(self.theme, THEMES['light'])
        self._bg_color.rgba = theme['bg']
        self.content_label.color = theme['text']
        self.chapter_title_label.color = theme['text']
        self.chapter_info.color = theme['text']
        self.title_label.color = theme['text']
        self.content_label.font_size = self.font_size

    def load_book(self, book_id):
        """加载书籍 - 优化：立即显示，后台加载内容"""
        if self._loading:
            return
        self._loading = True
        self.current_book_id = book_id
        
        # 立即显示加载状态
        self.title_label.text = '加载中...'
        self.chapter_title_label.text = '加载中...'
        self.content_label.text = '正在加载...'
        
        # 在后台线程加载书籍信息
        thread = threading.Thread(target=self._load_book_thread, args=(book_id,))
        thread.daemon = True
        thread.start()

    def _load_book_thread(self, book_id):
        """后台线程加载书籍信息"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT book_name, catalogue_len, last_read_chapter FROM books WHERE id = ?',
                (book_id,)
            )
            result = cursor.fetchone()
            
            if result:
                self.book_name = result[0]
                self.catalogue_len = result[1] or 0
                last_chapter = result[2] or 0
                self.current_chapter = min(last_chapter, self.catalogue_len - 1) if self.catalogue_len > 0 else 0
                
                # 加载目录
                cursor.execute('SELECT catalogue FROM books WHERE id = ?', (book_id,))
                cat_result = cursor.fetchone()
                if cat_result and cat_result[0]:
                    try:
                        self.catalogue = json.loads(cat_result[0])
                        self.catalogue_len = len(self.catalogue)
                    except Exception:
                        self.catalogue = []
            
            conn.close()
            
            # 回到主线程更新UI
            Clock.schedule_once(self._on_book_loaded, 0)
        except Exception as e:
            print(f"Load book error: {e}")
            Clock.schedule_once(lambda dt: setattr(self, '_loading', False), 0)

    def _on_book_loaded(self, dt):
        """书籍加载完成，更新UI"""
        self.title_label.text = self.book_name
        self.chapter_info.text = f'{self.current_chapter + 1}/{self.catalogue_len}'
        self._loading = False
        # 加载当前章节
        self.load_chapter(self.current_chapter)

    def load_chapter(self, chapter_index):
        """加载章节 - 优化：后台加载内容"""
        if not self.current_book_id:
            return
        
        chapter_index = max(0, min(chapter_index, self.catalogue_len - 1))
        self.current_chapter = chapter_index
        
        # 显示加载中
        self.chapter_title_label.text = '加载中...'
        self.content_label.text = '正在加载...'
        
        # 后台加载章节内容
        thread = threading.Thread(target=self._load_chapter_thread, args=(chapter_index,))
        thread.daemon = True
        thread.start()

    def _load_chapter_thread(self, chapter_index):
        """后台线程加载章节内容"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT title, content FROM chapters WHERE book_id = ? AND chapter_index = ?',
                (self.current_book_id, chapter_index + 1)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                title, content = result
                self._pending_content = {
                    'title': title or f'第 {chapter_index + 1} 章',
                    'content': content or '章节内容为空'
                }
            else:
                self._pending_content = {
                    'title': f'第 {chapter_index + 1} 章',
                    'content': '章节内容未下载，请先下载该章节'
                }
            
            # 回到主线程更新UI
            Clock.schedule_once(self._on_chapter_loaded, 0)
        except Exception as e:
            print(f"Load chapter error: {e}")
            self._pending_content = {
                'title': f'第 {chapter_index + 1} 章',
                'content': '加载失败，请重试'
            }
            Clock.schedule_once(self._on_chapter_loaded, 0)

    def _on_chapter_loaded(self, dt):
        """章节加载完成，更新UI"""
        if self._pending_content:
            self.chapter_title_label.text = self._pending_content['title']
            self.content_label.text = self._pending_content['content']
            self._pending_content = None
        
        self.chapter_info.text = f'{self.current_chapter + 1}/{self.catalogue_len}'
        
        # 更新阅读进度
        try:
            self.db.update_read_progress(self.current_book_id, self.current_chapter)
        except Exception:
            pass
        
        # 滚动到顶部
        Clock.schedule_once(lambda dt: setattr(self.scroll_view, 'scroll_y', 1.0), 0.05)

    def prev_chapter(self, instance):
        if self.current_chapter > 0:
            self.load_chapter(self.current_chapter - 1)

    def next_chapter(self, instance):
        if self.current_chapter < self.catalogue_len - 1:
            self.load_chapter(self.current_chapter + 1)

    def show_catalogue(self, instance):
        """显示目录"""
        if not self.catalogue:
            Popup(title='目录', content=Label(text='暂无目录', font_name=DEFAULT_FONT), size_hint=(0.9, 0.4)).open()
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT chapter_index FROM chapters WHERE book_id = ?', (self.current_book_id,))
        downloaded_set = set(row[0] for row in cursor.fetchall())
        conn.close()

        popup_content = BoxLayout(orientation='vertical', spacing=5)
        header = BoxLayout(size_hint_y=None, height=40, padding=(10, 5))
        header.add_widget(Label(text=f'目录（共 {self.catalogue_len} 章）', font_size=FONT_SIZES['md'], font_name=DEFAULT_FONT))
        close_btn = Button(text='关闭', size_hint_x=None, width=60, font_name=DEFAULT_FONT)
        close_btn.bind(on_press=lambda x: self._close_catalogue())
        header.add_widget(close_btn)
        popup_content.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        chapters_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        chapters_layout.bind(minimum_height=chapters_layout.setter('height'))

        for i, ch in enumerate(self.catalogue):
            name = ch.get('chapterName', f'第 {i + 1} 章')
            status = ' [当前]' if i == self.current_chapter else (' [未下载]' if (i + 1) not in downloaded_set else '')
            btn = Button(
                text=f'{name}{status}', size_hint_y=None, height=42,
                font_name=DEFAULT_FONT, font_size=FONT_SIZES['sm'], halign='left',
            )
            if i == self.current_chapter:
                btn.background_color = (0.3, 0.5, 0.9, 0.4)
            btn.bind(on_press=lambda x, idx=i: self._on_catalogue_select(idx))
            chapters_layout.add_widget(btn)

        chapters_layout.height = chapters_layout.minimum_height
        scroll.add_widget(chapters_layout)
        popup_content.add_widget(scroll)

        self._catalogue_popup = Popup(title='', title_size=0, content=popup_content, size_hint=(0.9, 0.8), auto_dismiss=True)
        self._catalogue_popup.open()

    def _on_catalogue_select(self, idx):
        self.load_chapter(idx)
        self._close_catalogue()

    def _close_catalogue(self):
        if self._catalogue_popup:
            self._catalogue_popup.dismiss()
            self._catalogue_popup = None

    def show_menu(self, instance):
        content = BoxLayout(orientation='vertical', padding=15, spacing=15, size_hint_y=None)
        content.height = 320
        content.add_widget(Label(text='字体大小', font_name=DEFAULT_FONT, size_hint_y=None, height=30, halign='left'))
        font_row = BoxLayout(size_hint_y=None, height=45, spacing=8)
        for key, label in {'small': '小', 'medium': '中', 'large': '大', 'extra_large': '特大'}.items():
            btn = Button(text=label, font_name=DEFAULT_FONT)
            if key == self.settings.get('font_size', 'medium'):
                btn.background_color = (0.3, 0.5, 0.9, 0.5)
            btn.bind(on_press=lambda x, s=key: self._set_font(s))
            font_row.add_widget(btn)
        content.add_widget(font_row)

        content.add_widget(Label(text='阅读主题', font_name=DEFAULT_FONT, size_hint_y=None, height=30, halign='left'))
        theme_row = BoxLayout(size_hint_y=None, height=45, spacing=8)
        for key, label in {'light': '浅色', 'dark': '深色', 'sepia': '护眼'}.items():
            btn = Button(text=label, font_name=DEFAULT_FONT)
            if key == self.settings.get('theme', 'light'):
                btn.background_color = (0.3, 0.5, 0.9, 0.5)
            btn.bind(on_press=lambda x, t=key: self._set_theme(t))
            theme_row.add_widget(btn)
        content.add_widget(theme_row)

        back_btn = Button(text='返回书架', size_hint_y=None, height=45, font_name=DEFAULT_FONT)
        back_btn.bind(on_press=lambda x: self.on_back(None))
        content.add_widget(back_btn)

        Popup(title='阅读设置', content=content, size_hint=(0.85, None), height=320).open()

    def _set_font(self, size_name):
        self.font_size = READER_FONT_SIZES.get(size_name, FONT_SIZES['md'])
        self.settings['font_size'] = size_name
        self._save_settings()
        self.content_label.font_size = self.font_size

    def _set_theme(self, theme_name):
        self.theme = theme_name
        self.settings['theme'] = theme_name
        self._save_settings()
        self.apply_theme()

    def on_back(self, instance):
        self.manager.current = 'bookshelf'
