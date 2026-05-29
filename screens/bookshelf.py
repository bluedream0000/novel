# -*- coding: utf-8 -*-
"""书架页面 - 美化版"""
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window

from config import DEFAULT_FONT, FONT_SIZES
from database import DatabaseManager

# 配色方案
COLORS = {
    'primary': (0.26, 0.47, 0.85, 1),      # 主色调 - 蓝色
    'primary_light': (0.4, 0.6, 0.95, 1),   # 浅蓝
    'secondary': (0.95, 0.96, 0.98, 1),     # 背景色
    'card_bg': (1, 1, 1, 1),                # 卡片白色
    'text_primary': (0.2, 0.2, 0.2, 1),     # 主文字
    'text_secondary': (0.5, 0.5, 0.5, 1),   # 次要文字
    'accent': (0.9, 0.3, 0.3, 1),           # 强调色 - 红色(删除)
    'success': (0.3, 0.7, 0.4, 1),          # 成功绿
}


class Card(BoxLayout):
    """卡片组件"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*COLORS['card_bg'])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            Color(0.9, 0.9, 0.9, 1)
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
        self.bind(pos=self._update_rect, size=self._update_rect)
        
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.border.pos = (instance.pos[0] - 1, instance.pos[1] - 1)
        self.border.size = (instance.size[0] + 2, instance.size[1] + 2)


class StyledButton(Button):
    """样式按钮"""
    def __init__(self, btn_type='primary', **kwargs):
        super().__init__(**kwargs)
        self.font_name = DEFAULT_FONT
        self.border = (0, 0, 0, 0)
        
        if btn_type == 'primary':
            self.background_color = COLORS['primary']
            self.color = (1, 1, 1, 1)
        elif btn_type == 'secondary':
            self.background_color = COLORS['primary_light']
            self.color = (1, 1, 1, 1)
        elif btn_type == 'danger':
            self.background_color = COLORS['accent']
            self.color = (1, 1, 1, 1)
        elif btn_type == 'ghost':
            self.background_color = (0, 0, 0, 0)
            self.color = COLORS['primary']


class BookshelfScreen(Screen):
    """书架页面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.build_ui()
        Clock.schedule_once(self.load_books, 0)

    def build_ui(self):
        """构建 UI"""
        # 根布局带背景色
        self.root_layout = BoxLayout(orientation='vertical', padding=0, spacing=0)
        with self.root_layout.canvas.before:
            Color(*COLORS['secondary'])
            self.bg_rect = Rectangle(pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # 顶部标题栏 - 渐变效果
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
        
        # 标题
        title = Label(
            text='我的书架',
            font_size=FONT_SIZES['xl'],
            bold=True,
            color=(1, 1, 1, 1),
            font_name=DEFAULT_FONT,
            halign='left',
            text_size=(200, None)
        )

        # 右上角添加按钮
        add_btn = Button(
            text='+',
            font_size=FONT_SIZES['xxl'],
            size_hint_x=None,
            width=45,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1)
        )
        add_btn.bind(on_press=self.on_add_book)
        
        header.add_widget(title)
        header.add_widget(Widget())  # 占位
        header.add_widget(add_btn)
        self.root_layout.add_widget(header)
        
        # 搜索栏 - 圆角设计
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
            hint_text='搜索书名或作者...',
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
        search_btn.bind(on_press=self.on_search)
        
        search_box.add_widget(self.search_input)
        search_box.add_widget(search_btn)
        search_container.add_widget(search_box)
        self.root_layout.add_widget(search_container)
        
        # 统计信息
        self.stats_label = Label(
            text='共 0 本书',
            font_size=FONT_SIZES['sm'],
            color=COLORS['text_secondary'],
            font_name=DEFAULT_FONT,
            size_hint_y=None,
            height=25,
            halign='left',
            text_size=(Window.width - 30, None),
            padding=(15, 0)
        )
        self.root_layout.add_widget(self.stats_label)

        # 书籍列表
        self.books_layout = GridLayout(
            cols=1,
            spacing=10,
            size_hint_y=None,
            padding=(15, 10)
        )
        self.books_layout.bind(minimum_height=self.books_layout.setter('height'))

        scroll = ScrollView()
        scroll.add_widget(self.books_layout)
        self.root_layout.add_widget(scroll)

        # 底部导航栏
        bottom_bar = BoxLayout(
            size_hint_y=None, 
            height=60,
            padding=(15, 10),
            spacing=15
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
        
        # 底部按钮
        sync_btn = StyledButton(
            text='云端同步',
            btn_type='secondary',
            size_hint_x=1
        )
        sync_btn.bind(on_press=self.on_cloud_sync)
        
        settings_btn = StyledButton(
            text='设置',
            btn_type='primary',
            size_hint_x=1
        )
        settings_btn.bind(on_press=self.on_settings)

        bottom_bar.add_widget(sync_btn)
        bottom_bar.add_widget(settings_btn)
        self.root_layout.add_widget(bottom_bar)

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
        
    def _update_bottom(self, instance, value):
        self.bottom_rect.pos = instance.pos
        self.bottom_rect.size = instance.size
        self.bottom_line.pos = (instance.pos[0], instance.pos[1] + instance.size[1] - 1)
        self.bottom_line.size = (instance.size[0], 1)

    def load_books(self, dt=None):
        """加载书籍列表"""
        self.books_layout.clear_widgets()
        books = self.db.get_all_books()
        
        # 更新统计
        self.stats_label.text = f'共 {len(books)} 本书'

        if not books:
            # 空状态提示
            empty_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=200,
                padding=20
            )
            empty_icon = Label(
                text='📚',
                font_size=60,
                size_hint_y=None,
                height=80
            )
            empty_text = Label(
                text='书架空空如也\n点击右上角 + 号添加书籍',
                font_size=FONT_SIZES['md'],
                color=COLORS['text_secondary'],
                font_name=DEFAULT_FONT,
                halign='center'
            )
            empty_box.add_widget(empty_icon)
            empty_box.add_widget(empty_text)
            self.books_layout.add_widget(empty_box)
            return

        for book in books:
            book_id = book[0]
            book_name = book[1]
            author = book[2]
            catalogue = book[5]
            last_read = book[7]
            status = book[8]

            # 书籍卡片
            book_card = Card(
                orientation='horizontal',
                size_hint_y=None,
                height=90,
                padding=(15, 12),
                spacing=10
            )

            # 书籍信息区域
            info_layout = BoxLayout(
                orientation='vertical',
                padding=(0, 0),
                spacing=5
            )
            
            # 书名
            name_label = Label(
                text=book_name,
                font_size=FONT_SIZES['md'],
                bold=True,
                halign='left',
                valign='center',
                text_size=(None, None),
                color=COLORS['text_primary'],
                font_name=DEFAULT_FONT,
                size_hint_y=0.55
            )
            
            # 作者和阅读进度
            meta_text = f'作者: {author or "未知"}'
            if last_read:
                meta_text += f'  |  已读到第 {last_read} 章'
                
            author_label = Label(
                text=meta_text,
                font_size=FONT_SIZES['xs'],
                halign='left',
                valign='center',
                text_size=(None, None),
                color=COLORS['text_secondary'],
                font_name=DEFAULT_FONT,
                size_hint_y=0.45
            )
            
            info_layout.add_widget(name_label)
            info_layout.add_widget(author_label)

            # 操作按钮区域
            btn_layout = BoxLayout(
                size_hint_x=None, 
                width=160, 
                spacing=8,
                padding=(0, 15, 0, 15)
            )
            
            # 阅读按钮 - 主按钮
            read_btn = StyledButton(
                text='阅读',
                btn_type='primary',
                size_hint_x=0.5
            )
            read_btn.bind(on_press=lambda x, bid=book_id: self.on_read(bid))
            
            # 更多按钮
            more_btn = StyledButton(
                text='⋮',
                btn_type='ghost',
                size_hint_x=0.25,
                font_size=FONT_SIZES['lg']
            )
            more_btn.bind(on_press=lambda x, bid=book_id: self.show_book_menu(bid))

            btn_layout.add_widget(read_btn)
            btn_layout.add_widget(more_btn)

            book_card.add_widget(info_layout)
            book_card.add_widget(btn_layout)

            self.books_layout.add_widget(book_card)

    def show_book_menu(self, book_id):
        """显示书籍操作菜单"""
        content = BoxLayout(orientation='vertical', padding=15, spacing=10, size_hint_y=None)
        content.height = 180
        
        cat_btn = StyledButton(
            text='查看目录',
            btn_type='secondary',
            size_hint_y=None,
            height=45
        )
        cat_btn.bind(on_press=lambda x: (popup.dismiss(), self.on_catalogue(book_id)))
        
        delete_btn = StyledButton(
            text='删除书籍',
            btn_type='danger',
            size_hint_y=None,
            height=45
        )
        delete_btn.bind(on_press=lambda x: (popup.dismiss(), self.on_delete(book_id)))
        
        cancel_btn = StyledButton(
            text='取消',
            btn_type='ghost',
            size_hint_y=None,
            height=45
        )
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        
        content.add_widget(cat_btn)
        content.add_widget(delete_btn)
        content.add_widget(cancel_btn)
        
        popup = Popup(
            title='',
            title_size=0,
            content=content,
            size_hint=(0.85, None),
            height=200,
            auto_dismiss=True,
            separator_height=0
        )
        popup.open()

    def on_search(self, instance):
        """搜索书籍"""
        keyword = self.search_input.text.strip()
        if keyword:
            self.manager.current = 'search'
            self.manager.get_screen('search').set_keyword(keyword)

    def on_add_book(self, instance):
        """添加书籍"""
        self.manager.current = 'search'

    def on_cloud_sync(self, instance):
        """云端同步"""
        self.manager.current = 'cloud'

    def on_settings(self, instance):
        """设置"""
        self.manager.current = 'settings'

    def on_read(self, book_id):
        """阅读书籍"""
        read_screen = self.manager.get_screen('read')
        read_screen.load_book(book_id)
        self.manager.current = 'read'

    def on_catalogue(self, book_id):
        """查看书籍目录 - 跳转到独立目录页"""
        catalogue_screen = self.manager.get_screen('catalogue')
        catalogue_screen.load_book(book_id)
        self.manager.current = 'catalogue'

    def on_delete(self, book_id):
        """删除书籍"""
        def confirm_delete(instance):
            self.db.delete_book(book_id)
            self.load_books()
            popup.dismiss()

        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        content.add_widget(Label(
            text='确定要删除这本书吗？',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['md'],
            color=COLORS['text_primary']
        ))
        
        btn_box = BoxLayout(size_hint_y=None, height=45, spacing=15)
        
        cancel_btn = StyledButton(
            text='取消',
            btn_type='ghost'
        )
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        
        confirm_btn = StyledButton(
            text='删除',
            btn_type='danger'
        )
        confirm_btn.bind(on_press=confirm_delete)
        
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(confirm_btn)
        content.add_widget(btn_box)

        popup = Popup(
            title='确认删除',
            title_font=DEFAULT_FONT,
            content=content,
            size_hint=(0.85, None),
            height=180,
            separator_height=1
        )
        popup.open()
