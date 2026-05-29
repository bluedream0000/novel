# -*- coding: utf-8 -*-
"""云端同步页面 - 带配置保存和进度显示"""
import os
import time
import threading
import json

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window

from config import DEFAULT_FONT, FONT_SIZES

# 配色方案
COLORS = {
    'primary': (0.26, 0.47, 0.85, 1),
    'primary_light': (0.4, 0.6, 0.95, 1),
    'secondary': (0.95, 0.96, 0.98, 1),
    'card_bg': (1, 1, 1, 1),
    'text_primary': (0.2, 0.2, 0.2, 1),
    'text_secondary': (0.5, 0.5, 0.5, 1),
    'success': (0.3, 0.7, 0.4, 1),
    'danger': (0.9, 0.3, 0.3, 1),
}

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'qiniu_config.json')


class CloudScreen(Screen):
    """云端同步页面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.qn = None
        self.is_public = True
        self.sync_cancelled = False
        self.build_ui()
        Clock.schedule_once(self.load_config, 0)

    def _config_path(self):
        """获取配置文件路径"""
        return CONFIG_FILE

    def load_config(self, dt=None):
        """加载保存的配置"""
        try:
            if os.path.exists(self._config_path()):
                with open(self._config_path(), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.ak_input.text = config.get('ak', '')
                self.bucket_input.text = config.get('bucket', '')
                self.domain_input.text = config.get('domain', '')
                # SecretKey 不保存，需要重新输入（安全考虑）
                
                # 恢复公开空间设置
                self.is_public = config.get('is_public', True)
                if not self.is_public:
                    self.public_btn.text = '[未选] 公开空间（推荐）'
                    self.public_btn.background_color = (0.85, 0.85, 0.85, 1)
                    self.public_btn.color = COLORS['text_secondary']
                
                self.log_label.text = '配置已加载，请输入 SecretKey'
        except Exception as e:
            print(f'加载配置失败: {e}')

    def save_config(self):
        """保存配置（不包含 SecretKey）"""
        try:
            config = {
                'ak': self.ak_input.text.strip(),
                'bucket': self.bucket_input.text.strip(),
                'domain': self.domain_input.text.strip(),
                'is_public': self.is_public,
                'saved_at': int(time.time())
            }
            with open(self._config_path(), 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f'保存配置失败: {e}')
            return False

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
            font_size=FONT_SIZES['lg'],
            size_hint_x=None,
            width=70,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_name=DEFAULT_FONT
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'bookshelf'))

        title = Label(
            text='云端同步',
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

        # 内容滚动区域
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=10, padding=(15, 10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # 配置卡片
        config_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=320,
            padding=(15, 15),
            spacing=12
        )
        with config_card.canvas.before:
            Color(*COLORS['card_bg'])
            self.config_rect = RoundedRectangle(pos=config_card.pos, size=config_card.size, radius=[8])
            Color(0.9, 0.9, 0.9, 1)
            self.config_border = RoundedRectangle(
                pos=(config_card.pos[0]-1, config_card.pos[1]-1),
                size=(config_card.size[0]+2, config_card.size[1]+2),
                radius=[8]
            )
        config_card.bind(pos=self._update_config, size=self._update_config)

        config_card.add_widget(Label(
            text='七牛云配置',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['lg'],
            bold=True,
            color=COLORS['primary'],
            size_hint_y=None,
            height=30,
            halign='left'
        ))

        # AccessKey
        ak_row = BoxLayout(size_hint_y=None, height=38, spacing=8)
        ak_row.add_widget(Label(
            text='AccessKey:',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            color=COLORS['text_secondary'],
            size_hint_x=None,
            width=90
        ))
        self.ak_input = TextInput(
            password=True,
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=COLORS['text_primary'],
            padding=(10, 8)
        )
        ak_row.add_widget(self.ak_input)
        config_card.add_widget(ak_row)

        # SecretKey
        sk_row = BoxLayout(size_hint_y=None, height=38, spacing=8)
        sk_row.add_widget(Label(
            text='SecretKey:',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            color=COLORS['text_secondary'],
            size_hint_x=None,
            width=90
        ))
        self.sk_input = TextInput(
            password=True,
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=COLORS['text_primary'],
            padding=(10, 8),
            hint_text='首次使用需输入'
        )
        sk_row.add_widget(self.sk_input)
        config_card.add_widget(sk_row)

        # Bucket
        bucket_row = BoxLayout(size_hint_y=None, height=38, spacing=8)
        bucket_row.add_widget(Label(
            text='Bucket:',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            color=COLORS['text_secondary'],
            size_hint_x=None,
            width=90
        ))
        self.bucket_input = TextInput(
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=COLORS['text_primary'],
            padding=(10, 8)
        )
        bucket_row.add_widget(self.bucket_input)
        config_card.add_widget(bucket_row)

        # Domain
        domain_row = BoxLayout(size_hint_y=None, height=38, spacing=8)
        domain_row.add_widget(Label(
            text='Domain:',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            color=COLORS['text_secondary'],
            size_hint_x=None,
            width=90
        ))
        self.domain_input = TextInput(
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=COLORS['text_primary'],
            padding=(10, 8),
            hint_text='如: xxx.qiniudn.com'
        )
        domain_row.add_widget(self.domain_input)
        config_card.add_widget(domain_row)

        # 公开空间选项
        self.public_btn = Button(
            text='[已选] 公开空间（推荐）',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            size_hint_y=None,
            height=38,
            background_color=COLORS['primary'],
            color=(1, 1, 1, 1)
        )
        self.public_btn.bind(on_press=self.toggle_public)
        config_card.add_widget(self.public_btn)

        # 保存配置按钮
        save_btn = Button(
            text='保存配置',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['sm'],
            size_hint_y=None,
            height=38,
            background_color=COLORS['success'],
            color=(1, 1, 1, 1)
        )
        save_btn.bind(on_press=self.on_save_config)
        config_card.add_widget(save_btn)

        content.add_widget(config_card)

        # 进度条（默认隐藏）
        self.progress_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=60,
            padding=(15, 10),
            spacing=5,
            opacity=0
        )
        with self.progress_card.canvas.before:
            Color(*COLORS['card_bg'])
            self.progress_rect = RoundedRectangle(pos=self.progress_card.pos, size=self.progress_card.size, radius=[8])
        self.progress_card.bind(pos=self._update_progress_rect, size=self._update_progress_rect)

        self.progress_label = Label(
            text='准备同步...',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['xs'],
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=20,
            halign='left'
        )
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=10)
        self.progress_card.add_widget(self.progress_label)
        self.progress_card.add_widget(self.progress_bar)
        content.add_widget(self.progress_card)

        # 测试连接按钮
        test_btn = Button(
            text='测试连接',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['md'],
            size_hint_y=None,
            height=40,
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1)
        )
        test_btn.bind(on_press=self.test_connection)
        content.add_widget(test_btn)

        # 操作按钮
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        upload_btn = Button(
            text='上传到云端',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['md'],
            bold=True,
            background_color=COLORS['primary'],
            color=(1, 1, 1, 1)
        )
        upload_btn.bind(on_press=self.upload_to_cloud)

        download_btn = Button(
            text='从云端下载',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['md'],
            bold=True,
            background_color=COLORS['primary_light'],
            color=(1, 1, 1, 1)
        )
        download_btn.bind(on_press=self.download_from_cloud)

        btn_box.add_widget(upload_btn)
        btn_box.add_widget(download_btn)
        content.add_widget(btn_box)

        # 日志区域
        log_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=200,
            padding=(15, 12),
            spacing=8
        )
        with log_card.canvas.before:
            Color(*COLORS['card_bg'])
            self.log_rect = RoundedRectangle(pos=log_card.pos, size=log_card.size, radius=[8])
            Color(0.9, 0.9, 0.9, 1)
            self.log_border = RoundedRectangle(
                pos=(log_card.pos[0]-1, log_card.pos[1]-1),
                size=(log_card.size[0]+2, log_card.size[1]+2),
                radius=[8]
            )
        log_card.bind(pos=self._update_log, size=self._update_log)

        log_card.add_widget(Label(
            text='同步日志',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['md'],
            bold=True,
            color=COLORS['primary'],
            size_hint_y=None,
            height=25,
            halign='left'
        ))

        self.log_label = Label(
            text='准备就绪',
            font_name=DEFAULT_FONT,
            font_size=FONT_SIZES['xs'],
            halign='left',
            valign='top',
            color=COLORS['text_secondary'],
            text_size=(Window.width - 60, None)
        )
        log_card.add_widget(self.log_label)
        content.add_widget(log_card)

        content.height = content.minimum_height
        scroll.add_widget(content)
        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_header(self, instance, value):
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size

    def _update_config(self, instance, value):
        self.config_rect.pos = instance.pos
        self.config_rect.size = instance.size
        self.config_border.pos = (instance.pos[0]-1, instance.pos[1]-1)
        self.config_border.size = (instance.size[0]+2, instance.size[1]+2)

    def _update_log(self, instance, value):
        self.log_rect.pos = instance.pos
        self.log_rect.size = instance.size
        self.log_border.pos = (instance.pos[0]-1, instance.pos[1]-1)
        self.log_border.size = (instance.size[0]+2, instance.size[1]+2)

    def _update_progress_rect(self, instance, value):
        self.progress_rect.pos = instance.pos
        self.progress_rect.size = instance.size

    def toggle_public(self, instance):
        """切换公开空间选项"""
        self.is_public = not self.is_public
        if self.is_public:
            instance.text = '[已选] 公开空间（推荐）'
            instance.background_color = COLORS['primary']
            instance.color = (1, 1, 1, 1)
        else:
            instance.text = '[未选] 公开空间（推荐）'
            instance.background_color = (0.85, 0.85, 0.85, 1)
            instance.color = COLORS['text_secondary']

    def on_save_config(self, instance):
        """保存配置按钮"""
        if self.save_config():
            self.log_label.text = '配置已保存！\n（SecretKey 未保存，需每次输入）'
        else:
            self.log_label.text = '配置保存失败'

    def _init_qiniu(self):
        """初始化七牛云管理器"""
        ak = self.ak_input.text.strip()
        sk = self.sk_input.text.strip()
        bucket = self.bucket_input.text.strip()
        domain = self.domain_input.text.strip()

        if not all([ak, sk, bucket, domain]):
            return None

        from qiniu_manager import QiniuManager
        return QiniuManager(ak, sk, bucket, domain)

    def test_connection(self, instance):
        """测试七牛云连接"""
        ak = self.ak_input.text.strip()
        sk = self.sk_input.text.strip()
        bucket = self.bucket_input.text.strip()
        domain = self.domain_input.text.strip()

        # 校验必填项
        missing = []
        if not ak: missing.append('AccessKey')
        if not sk: missing.append('SecretKey')
        if not bucket: missing.append('Bucket')
        if not domain: missing.append('Domain')
        if missing:
            self.log_label.text = '配置不完整，缺少: ' + '、'.join(missing)
            return

        self.log_label.text = '正在测试连接...'
        self.show_progress('正在测试连接...')
        threading.Thread(target=self._test_connection_thread, daemon=True).start()

    def _test_connection_thread(self):
        """测试连接线程 - 通过尝试上传一个小文件来验证"""
        try:
            qn = self._init_qiniu()
            test_key = 'novel-reader/default/_test_connection.json'
            test_data = json.dumps({'test': True, 'time': int(time.time())}).encode('utf-8')

            self.update_progress('正在生成 Token...', 60)
            # 尝试生成 Token（验证 AK/SK 是否正确）
            token = qn.generate_upload_token(test_key, expires=60)
            if not token:
                Clock.schedule_once(lambda dt: (
                    setattr(self.log_label, 'text', 'Token 生成失败，请检查 AK/SK'),
                    self.hide_progress()
                ), 0)
                return

            self.update_progress('正在上传测试文件...', 70)
            # 尝试上传一个小文件（验证 Bucket 和权限）
            result = qn.upload_file(test_key, test_data, is_public=self.is_public)

            if result['success']:
                self.update_progress('正在验证下载...', 85)
                # 尝试下载（验证 Domain 和读取权限）
                dl = qn.download_json(test_key)
                if dl['success']:
                    self.update_progress('连接测试成功！', 100)
                    Clock.schedule_once(lambda dt: (
                        setattr(self.log_label, 'text',
                            '连接测试成功！\nAK/SK: 有效\nBucket: ' + self.bucket_input.text.strip() + '\nDomain: ' + self.domain_input.text.strip() + '\n上传/下载: 正常'),
                        self.hide_progress()
                    ), 0)
                else:
                    Clock.schedule_once(lambda dt: (
                        setattr(self.log_label, 'text', '上传成功但下载失败: ' + dl.get('error', '')),
                        self.hide_progress()
                    ), 0)
            else:
                err = result.get('error', '未知错误')
                Clock.schedule_once(lambda dt: (
                    setattr(self.log_label, 'text', '连接测试失败: ' + err),
                    self.hide_progress()
                ), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: (
                setattr(self.log_label, 'text', '连接测试出错: ' + str(e)),
                self.hide_progress()
            ), 0)

    def show_progress(self, message='准备同步...'):
        """显示进度条"""
        Clock.schedule_once(lambda dt: (
            setattr(self.progress_card, 'opacity', 1),
            setattr(self.progress_label, 'text', message),
            setattr(self.progress_bar, 'value', 0)
        ), 0)

    def hide_progress(self):
        """隐藏进度条"""
        Clock.schedule_once(lambda dt: setattr(self.progress_card, 'opacity', 0), 0)

    def update_progress(self, message, percent):
        """更新进度"""
        Clock.schedule_once(lambda dt: (
            setattr(self.progress_label, 'text', message),
            setattr(self.progress_bar, 'value', percent)
        ), 0)

    def upload_to_cloud(self, instance):
        """上传到云端"""
        self.qn = self._init_qiniu()
        if not self.qn:
            self.log_label.text = '请先填写完整的七牛云配置'
            return

        self.sync_cancelled = False
        self.show_progress('正在准备上传...')
        self.log_label.text = '开始上传...'
        threading.Thread(target=self._upload_thread, daemon=True).start()

    def _upload_thread(self):
        """上传线程 - 数据结构与 Flask /api/sync/export 完全对齐"""
        try:
            from database import DatabaseManager
            db = DatabaseManager()

            self.update_progress('正在读取书架数据...', 10)
            books = db.get_all_books()
            total_books = len(books)
            
            if total_books == 0:
                Clock.schedule_once(lambda dt: (
                    setattr(self.log_label, 'text', '书架为空，无需上传'),
                    self.hide_progress()
                ), 0)
                return

            books_data = []
            for i, book in enumerate(books):
                if self.sync_cancelled:
                    return
                    
                # 解包：id, book_name, author, book_origin, catalogue_url, catalogue,
                #        catalogue_len, last_read_chapter, status, created_at
                book_id = book[0]
                book_name = book[1]
                author = book[2]
                book_origin = book[3] or ''
                catalogue_url = book[4] or ''
                catalogue = book[5]
                catalogue_len = book[6] or 0
                last_read_chapter = book[7] or 0
                status = book[8] or 'pending'

                # 解析 catalogue JSON 字符串
                if isinstance(catalogue, str):
                    try:
                        catalogue = json.loads(catalogue)
                    except (json.JSONDecodeError, TypeError):
                        catalogue = []
                if not isinstance(catalogue, list):
                    catalogue = []

                # 获取该书籍的所有已下载章节
                chapters = db.get_chapters(book_id)
                chapters_data = []
                for ch in chapters:
                    chapters_data.append({
                        'index': ch[2],   # chapter_index
                        'name': ch[3],    # title
                        'content': ch[4]  # content
                    })

                books_data.append({
                    'id': book_id,
                    'bookName': book_name,
                    'author': author,
                    'bookOrigin': book_origin,
                    'catalogueUrl': catalogue_url,
                    'lastReadChapter': last_read_chapter,
                    'catalogueLen': catalogue_len,
                    'catalogue': catalogue,
                    'status': status,
                    'chapters': chapters_data,
                })
                
                # 更新进度，显示章节信息和数据大小
                progress = 10 + int((i + 1) / total_books * 30)
                book_size_kb = len(json.dumps(books_data[-1], ensure_ascii=False).encode('utf-8')) / 1024
                self.update_progress(
                    '正在打包 (' + str(i+1) + '/' + str(total_books) + ') ' +
                    book_name + ' - ' + str(len(chapters_data)) + '章 ' +
                    '{:.1f}'.format(book_size_kb) + 'KB...',
                    progress
                )

            # 与 Flask 移动端 syncBookshelfToCloud 完全一致的结构
            export_data = {
                'version': 1,
                'updatedAt': int(time.time() * 1000),  # 毫秒时间戳，与JS Date.now()一致
                'books': books_data
            }

            # 路径与 Flask 移动端一致: novel-reader/default/bookshelf.json
            bookshelf_key = 'novel-reader/default/bookshelf.json'
            json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            content_size = len(json_content.encode('utf-8'))

            self.update_progress('正在上传 (' + '{:.1f}'.format(content_size/1024) + ' KB)...', 50)

            # 上传书架数据
            result = self.qn.upload_file(bookshelf_key, json_content.encode('utf-8'), is_public=self.is_public)

            if result['success']:
                self.update_progress('上传完成！', 100)
                msg = '上传成功！\n文件: novel-reader/default/bookshelf.json\n书籍数: ' + str(total_books) + ' 本\n大小: ' + '{:.1f}'.format(content_size/1024) + ' KB'
                Clock.schedule_once(lambda dt: (
                    setattr(self.log_label, 'text', msg),
                    self.hide_progress()
                ), 0)
                # 保存配置
                self.save_config()
            else:
                err_msg = result.get('error', '未知错误')
                Clock.schedule_once(lambda dt: (
                    setattr(self.log_label, 'text', '上传失败: ' + err_msg),
                    self.hide_progress()
                ), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: (
                setattr(self.log_label, 'text', '上传出错: ' + str(e)),
                self.hide_progress()
            ), 0)

    def download_from_cloud(self, instance):
        """从云端下载"""
        self.qn = self._init_qiniu()
        if not self.qn:
            self.log_label.text = '请先填写完整的七牛云配置'
            return

        self.sync_cancelled = False
        self.show_progress('正在连接云端...')
        self.log_label.text = '开始下载...'
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        """下载线程 - 兼容 Flask /api/sync/export 格式"""
        try:
            # 路径与 Flask 移动端一致: novel-reader/default/bookshelf.json
            bookshelf_key = 'novel-reader/default/bookshelf.json'

            # 打印下载URL用于调试
            download_url = self.qn.generate_download_url(bookshelf_key, is_public=self.is_public)
            print('[Cloud] 下载URL:', download_url)
            print('[Cloud] is_public:', self.is_public)

            self.update_progress('正在下载备份文件...', 30)
            result = self.qn.download_json(bookshelf_key)

            print('[Cloud] 下载结果:', result.get('success'), result.get('error', ''))

            if not result['success']:
                error_msg = result.get('error', '未知错误')
                if '404' in error_msg or '不存在' in error_msg:
                    error_msg = '未找到备份文件，请先上传'
                Clock.schedule_once(lambda dt: (
                    setattr(self.log_label, 'text', '下载失败: ' + error_msg + '\nURL: ' + download_url),
                    self.hide_progress()
                ), 0)
                return

            self.update_progress('正在解析数据...', 60)
            from database import DatabaseManager
            db = DatabaseManager()
            raw_data = result['data']

            # 调试：打印云端数据结构
            print('[Cloud] raw_data 类型:', type(raw_data))
            if isinstance(raw_data, dict):
                print('[Cloud] raw_data keys:', list(raw_data.keys()))
            else:
                print('[Cloud] raw_data 不是dict，内容前200字符:', str(raw_data)[:200])

            # 兼容三种格式：
            # 1. Flask 移动端格式: { version, updatedAt, books: [...] }
            # 2. Flask /api/sync/export 格式: { success, data: { books: [...] } }
            # 3. 旧 Kivy 格式: { version, bookshelf: [...] }
            if 'books' in raw_data:
                book_list = raw_data['books']
            elif 'data' in raw_data and isinstance(raw_data['data'], dict) and 'books' in raw_data['data']:
                book_list = raw_data['data']['books']
            elif 'bookshelf' in raw_data:
                book_list = raw_data['bookshelf']
            else:
                book_list = []

            print('[Cloud] book_list 数量:', len(book_list))
            if len(book_list) > 0:
                print('[Cloud] 第一本书 keys:', list(book_list[0].keys()) if isinstance(book_list[0], dict) else type(book_list[0]))

            imported_count = 0
            skipped_books = 0
            new_chapters = 0
            total = len(book_list)
            
            for i, book_data in enumerate(book_list):
                if self.sync_cancelled:
                    return

                # 兼容 camelCase 和 snake_case 字段名
                book_name = book_data.get('bookName') or book_data.get('book_name', '未知')
                author = book_data.get('author', '')
                book_origin = book_data.get('bookOrigin') or book_data.get('book_origin', '')
                catalogue_url = book_data.get('catalogueUrl') or book_data.get('catalogue_url', '')
                last_read = book_data.get('lastReadChapter') or book_data.get('last_read_chapter', 0)
                catalogue = book_data.get('catalogue', [])
                catalogue_len = book_data.get('catalogueLen') or book_data.get('catalogue_len', 0)
                status = book_data.get('status', 'pending')

                # catalogue 可能是 JSON 字符串
                if isinstance(catalogue, str):
                    try:
                        catalogue = json.loads(catalogue)
                    except (json.JSONDecodeError, TypeError):
                        catalogue = []

                # 检查本地是否已存在该书（按书名+作者匹配）
                local_book_id = db.get_book_by_name_author(book_name, author)

                if local_book_id:
                    # 书籍已存在，只同步缺失的章节和更新阅读进度
                    skipped_books += 1

                    # 更新阅读进度（取云端和本地的较大值）
                    local_book = db.get_book(local_book_id)
                    local_last_read = local_book[7] if len(local_book) > 7 else 0
                    if last_read and last_read > local_last_read:
                        db.update_read_progress(local_book_id, last_read)

                    # 只下载本地没有的章节
                    cloud_chapters = book_data.get('chapters', [])
                    if cloud_chapters:
                        local_chapters = db.get_chapters(local_book_id)
                        local_chapter_indices = set(ch[2] for ch in local_chapters)

                        for ch in cloud_chapters:
                            ch_index = ch.get('index', 0)
                            ch_name = ch.get('name') or ch.get('title', '')
                            ch_content = ch.get('content', '')
                            if ch_index and ch_content and ch_index not in local_chapter_indices:
                                db.add_chapter(local_book_id, ch_index, ch_name, ch_content)
                                new_chapters += 1
                else:
                    # 本地不存在，新增书籍
                    book_id = db.add_book(
                        book_name, author,
                        catalogue=json.dumps(catalogue, ensure_ascii=False),
                        book_origin=book_origin,
                        catalogue_url=catalogue_url
                    )

                    if book_id > 0:
                        db.update_book(book_id, catalogue_len=catalogue_len, status=status)

                        if last_read:
                            db.update_read_progress(book_id, last_read)

                        # 恢复章节内容
                        chapters = book_data.get('chapters', [])
                        for ch in chapters:
                            ch_index = ch.get('index', 0)
                            ch_name = ch.get('name') or ch.get('title', '')
                            ch_content = ch.get('content', '')
                            if ch_index and ch_content:
                                db.add_chapter(book_id, ch_index, ch_name, ch_content)
                                new_chapters += 1

                    imported_count += 1

                progress = 60 + int((i + 1) / total * 35)
                self.update_progress('正在导入 (' + str(i+1) + '/' + str(total) + ')...', progress)

            self.update_progress('下载完成！', 100)
            msg = '同步完成！\n新增书籍: ' + str(imported_count) + ' 本'
            if skipped_books > 0:
                msg += '\n已存在跳过: ' + str(skipped_books) + ' 本'
            if new_chapters > 0:
                msg += '\n新增章节: ' + str(new_chapters) + ' 章'
            if imported_count == 0 and skipped_books == 0:
                msg += '\n（云端无书籍数据）'
            elif imported_count == 0 and new_chapters == 0:
                msg += '\n（本地已是最新）'
            Clock.schedule_once(lambda dt: (
                setattr(self.log_label, 'text', msg),
                self.hide_progress()
            ), 0)
            # 保存配置
            self.save_config()

        except Exception as e:
            Clock.schedule_once(lambda dt: (
                setattr(self.log_label, 'text', '下载出错: ' + str(e)),
                self.hide_progress()
            ), 0)
