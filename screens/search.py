# -*- coding: utf-8 -*-
"""搜索页面（含下载逻辑）- 美化版"""
import threading
import asyncio

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window

from config import DEFAULT_FONT, FONT_SIZES
from database import DatabaseManager
from spider_manager import SpiderManager

# 配色方案 - 与书架页面一致
COLORS = {
    'primary': (0.26, 0.47, 0.85, 1),
    'primary_light': (0.4, 0.6, 0.95, 1),
    'secondary': (0.95, 0.96, 0.98, 1),
    'card_bg': (1, 1, 1, 1),
    'text_primary': (0.2, 0.2, 0.2, 1),
    'text_secondary': (0.5, 0.5, 0.5, 1),
    'success': (0.3, 0.7, 0.4, 1),
}


class SearchScreen(Screen):
    """搜索页面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.spider = SpiderManager()
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
            font_size=FONT_SIZES['md'],
            size_hint_x=None,
            width=70,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_name=DEFAULT_FONT
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'bookshelf'))

        title = Label(
            text='添加书籍',
            font_size=FONT_SIZES['xl'],
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

        # 搜索栏
        search_container = BoxLayout(
            size_hint_y=None,
            height=70,
            padding=(15, 12),
            spacing=10
        )

        search_box = BoxLayout(
            size_hint_y=None,
            height=46,
            spacing=0
        )
        with search_box.canvas.before:
            Color(*COLORS['card_bg'])
            self.search_rect = RoundedRectangle(
                pos=search_box.pos,
                size=search_box.size,
                radius=[26]
            )
            Color(0.85, 0.85, 0.85, 1)
            self.search_border = RoundedRectangle(
                pos=(search_box.pos[0]-1, search_box.pos[1]-1),
                size=(search_box.size[0]+2, search_box.size[1]+2),
                radius=[26]
            )
        search_box.bind(pos=self._update_search, size=self._update_search)

        self.search_input = TextInput(
            hint_text='输入书名或作者搜索...',
            multiline=False,
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['md'],
            background_color=(0, 0, 0, 0),
            foreground_color=COLORS['text_primary'],
            hint_text_color=(0.6, 0.6, 0.6, 1),
            padding=(15, 10),
            cursor_color=COLORS['primary']
        )

        search_btn = Button(
            text='搜索',
            font_name=DEFAULT_FONT,
            size_hint_x=None,
            width=60,
            background_color=(0, 0, 0, 0),
            color=COLORS['primary'],
            bold=True
        )
        search_btn.bind(on_press=self.do_search)

        search_box.add_widget(self.search_input)
        search_box.add_widget(search_btn)
        search_container.add_widget(search_box)
        self.root_layout.add_widget(search_container)

        # 搜索结果列表
        self.results_layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=(15, 5))
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))

        scroll = ScrollView()
        scroll.add_widget(self.results_layout)
        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_header(self, instance, value):
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size

    def _update_search(self, instance, value):
        self.search_rect.pos = instance.pos
        self.search_rect.size = instance.size
        self.search_border.pos = (instance.pos[0]-1, instance.pos[1]-1)
        self.search_border.size = (instance.size[0]+2, instance.size[1]+2)

    def set_keyword(self, keyword):
        """设置搜索关键词"""
        self.search_input.text = keyword
        self.do_search(None)

    def do_search(self, instance):
        """执行搜索"""
        keyword = self.search_input.text.strip()
        if not keyword:
            return

        self.results_layout.clear_widgets()

        # 加载中提示
        loading_box = BoxLayout(size_hint_y=None, height=60)
        loading_box.add_widget(Label(
            text='搜索中...',
            font_name=DEFAULT_FONT,
            color=COLORS['text_secondary']
        ))
        self.results_layout.add_widget(loading_box)

        threading.Thread(target=self._search_thread, args=(keyword,), daemon=True).start()

    def _search_thread(self, keyword):
        """搜索线程"""
        results = self.spider.search_book(keyword)
        Clock.schedule_once(lambda dt: self._show_results(results), 0)

    def _show_results(self, results):
        """显示搜索结果"""
        self.results_layout.clear_widgets()

        if not results:
            empty_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=120,
                padding=20
            )
            empty_box.add_widget(Label(
                text='未找到相关书籍',
                font_name=DEFAULT_FONT,
                font_size=FONT_SIZES['md'],
                color=COLORS['text_secondary']
            ))
            empty_box.add_widget(Label(
                text='试试其他关键词',
                font_name=DEFAULT_FONT,
                font_size=FONT_SIZES['sm'],
                color=COLORS['text_secondary']
            ))
            self.results_layout.add_widget(empty_box)
            return

        for book in results:
            result_item = BoxLayout(
                size_hint_y=None,
                height=80,
                padding=(15, 10),
                spacing=10
            )
            with result_item.canvas.before:
                Color(*COLORS['card_bg'])
                rect = RoundedRectangle(pos=result_item.pos, size=result_item.size, radius=[8])
                Color(0.9, 0.9, 0.9, 1)
                border = RoundedRectangle(
                    pos=(result_item.pos[0]-1, result_item.pos[1]-1),
                    size=(result_item.size[0]+2, result_item.size[1]+2),
                    radius=[8]
                )
            result_item.bind(pos=lambda inst, val, r=rect, b=border: (
                setattr(r, 'pos', inst.pos),
                setattr(b, 'pos', (inst.pos[0]-1, inst.pos[1]-1))
            ))
            result_item.bind(size=lambda inst, val, r=rect, b=border: (
                setattr(r, 'size', inst.size),
                setattr(b, 'size', (inst.size[0]+2, inst.size[1]+2))
            ))

            book_name = book.get('bookName') or book.get('name', '未知')
            book_author = book.get('bookAuthor') or book.get('author', '未知')

            info_layout = BoxLayout(orientation='vertical', spacing=3)
            info_layout.add_widget(Label(
                text=book_name,
                font_size=FONT_SIZES['md'],
                bold=True,
                halign='left',
                color=COLORS['text_primary'],
                font_name=DEFAULT_FONT,
                text_size=(Window.width - 140, None)
            ))
            info_layout.add_widget(Label(
                text=f'作者: {book_author}',
                font_size=FONT_SIZES['sm'],
                halign='left',
                color=COLORS['text_secondary'],
                font_name=DEFAULT_FONT
            ))

            download_btn = Button(
                text='添加',
                font_name=DEFAULT_FONT,
                size_hint_x=None,
                width=60,
                background_color=COLORS['primary'],
                color=(1, 1, 1, 1)
            )
            download_btn.bind(on_press=lambda x, b=book: self.on_download(b))

            result_item.add_widget(info_layout)
            result_item.add_widget(download_btn)
            self.results_layout.add_widget(result_item)

    def on_download(self, book):
        """下载书籍"""
        book_name = book.get('bookName') or book.get('name', '未知')
        book_author = book.get('bookAuthor') or book.get('author', '')
        catalogue_url = book.get('catalogueUrl') or book.get('catalogue_url', '')
        book_origin = book.get('bookOrigin') or book.get('origin', 'biquuge')

        # 美化的下载弹窗
        popup_content = BoxLayout(orientation='vertical', padding=20, spacing=15)

        popup_content.add_widget(Label(
            text=f'正在添加: {book_name}',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['md'],
            bold=True,
            color=COLORS['text_primary']
        ))

        self.download_progress = ProgressBar(max=100, value=10)
        popup_content.add_widget(self.download_progress)

        self.download_status = Label(
            text='正在添加到书架...',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            color=COLORS['text_secondary']
        )
        popup_content.add_widget(self.download_status)

        self.download_popup = Popup(
            title='添加书籍',
            title_font=DEFAULT_FONT,
            content=popup_content,
            size_hint=(0.85, None),
            height=200,
            auto_dismiss=False,
            separator_height=1
        )
        self.download_popup.open()

        self.current_download = {
            'book_name': book_name,
            'book_author': book_author,
            'catalogue_url': catalogue_url,
            'book_origin': book_origin
        }

        threading.Thread(target=self._add_book_thread, daemon=True).start()

    def _add_book_thread(self):
        """添加书籍到书架"""
        try:
            from spider.base_spider import get_spider
            from urllib.parse import urlparse

            book_name = self.current_download['book_name']
            book_author = self.current_download['book_author']
            catalogue_url = self.current_download['catalogue_url']
            book_origin = self.current_download['book_origin']

            Clock.schedule_once(lambda dt: self._update_download_status('正在添加到书架...', 20), 0)
            book_id = self.db.add_book(book_name, book_author, catalogue=catalogue_url,
                                        book_origin=book_origin, catalogue_url=catalogue_url)

            if book_id < 0:
                Clock.schedule_once(lambda dt: self._download_error('添加到书架失败'), 0)
                return

            Clock.schedule_once(lambda dt: self._update_download_status('正在获取目录...', 40), 0)

            spider = get_spider(book_origin)
            if not spider:
                Clock.schedule_once(lambda dt: self._download_error('未找到爬虫配置'), 0)
                return

            parsed = urlparse(catalogue_url)
            catalogue_path = parsed.path + ('?' + parsed.query if parsed.query else '')

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                chapters = loop.run_until_complete(spider.fetch_catalogue(catalogue_path))
            finally:
                loop.close()

            if not chapters:
                Clock.schedule_once(lambda dt: self._download_error('获取目录失败'), 0)
                return

            total = len(chapters)
            Clock.schedule_once(lambda dt: self._update_download_status(
                f'获取目录成功，共 {total} 章', 50), 0)

            catalogue_data = []
            for i, ch in enumerate(chapters, 1):
                catalogue_data.append({
                    'chapterIndex': str(i),
                    'chapterName': ch.get('chapterName', f'第{i}章'),
                    'chapterUrl': ch.get('chapterUrl', ''),
                })

            self.db.update_book(book_id, catalogue=catalogue_data, catalogue_len=total)

            Clock.schedule_once(lambda dt: self._update_download_status(
                f'目录获取完成，开始下载章节...', 60), 0)

            self.current_catalogue = catalogue_data
            self.current_book_id = book_id

            threading.Thread(target=self._download_chapters_thread, daemon=True).start()

        except Exception as e:
            error_msg = str(e)
            Clock.schedule_once(lambda dt, msg=error_msg: self._download_error(f'添加失败: {msg}'), 0)

    def _download_chapters_thread(self):
        """后台下载章节内容"""
        try:
            import aiohttp

            book_id = self.current_book_id
            catalogue = self.current_catalogue
            book_name = self.current_download['book_name']
            book_origin = self.current_download['book_origin']

            from spider.base_spider import get_spider
            spider = get_spider(book_origin)
            if not spider:
                Clock.schedule_once(lambda dt: self._download_error('未找到爬虫'), 0)
                return

            total = len(catalogue)
            batch_size = 20
            max_concurrent = 5

            async def download():
                async with aiohttp.ClientSession() as session:
                    semaphore = asyncio.Semaphore(max_concurrent)

                    async def fetch_chapter(ch):
                        async with semaphore:
                            result = await spider.fetch_chapter(session, ch)
                            await asyncio.sleep(0.2)
                            return ch, result

                    for batch_start in range(0, total, batch_size):
                        batch = catalogue[batch_start:batch_start + batch_size]
                        tasks = [fetch_chapter(ch) for ch in batch]
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        saved = 0
                        for result in results:
                            if isinstance(result, Exception):
                                continue
                            ch, chapter_data = result
                            if chapter_data:
                                idx = int(ch.get('chapterIndex', 0)) or int(chapter_data.get('chapterIndex', 0))
                                if idx <= 0:
                                    continue
                                self.db.add_chapter(
                                    book_id, idx,
                                    chapter_data.get('chapterName', ''),
                                    chapter_data.get('chapterContent', '')
                                )
                                saved += 1

                        progress = int((batch_start + batch_size) / total * 100)
                        Clock.schedule_once(
                            lambda dt, p=progress: self._update_download_progress(p), 0)

                        if batch_start + batch_size < total:
                            await asyncio.sleep(0.5)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(download())
            finally:
                loop.close()

            Clock.schedule_once(lambda dt: self._download_complete(book_id, book_name), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self._download_error(f'下载失败: {str(e)}'), 0)

    def _update_download_status(self, text, progress):
        """更新下载状态"""
        if hasattr(self, 'download_status'):
            self.download_status.text = text
        if hasattr(self, 'download_progress'):
            self.download_progress.value = progress

    def _update_download_progress(self, progress):
        """更新下载进度"""
        if hasattr(self, 'download_status'):
            self.download_status.text = f'下载进度: {progress}%'
        if hasattr(self, 'download_progress'):
            self.download_progress.value = progress

    def _download_complete(self, book_id, book_name):
        """下载完成"""
        if hasattr(self, 'download_popup'):
            self.download_popup.dismiss()

        self.manager.current = 'bookshelf'
        bookshelf = self.manager.get_screen('bookshelf')
        bookshelf.load_books()

        popup = Popup(
            title='添加成功',
            title_font=DEFAULT_FONT,
            content=Label(
                text=f'《{book_name}》\n已添加到书架！',
                font_name=DEFAULT_FONT,
                font_size=FONT_SIZES['md']
            ),
            size_hint=(0.8, None),
            height=150,
            separator_height=1
        )
        popup.open()

    def _download_error(self, error_msg):
        """下载出错"""
        if hasattr(self, 'download_popup'):
            self.download_popup.dismiss()
        popup = Popup(
            title='添加失败',
            title_font=DEFAULT_FONT,
            content=Label(
                text=f'添加失败: {error_msg}',
                font_name=DEFAULT_FONT,
                font_size=FONT_SIZES['sm']
            ),
            size_hint=(0.8, None),
            height=150,
            separator_height=1
        )
        popup.open()
