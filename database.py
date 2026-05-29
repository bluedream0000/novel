# -*- coding: utf-8 -*-
"""
数据库管理器 - Kivy App 版本
适配手机存储路径
"""
import os
import sqlite3
from kivy.utils import platform


class DatabaseManager:
    """数据库管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.db_path = self._get_db_path()
        self._init_db()
    
    def _get_db_path(self):
        """获取数据库路径（适配 Android）"""
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                storage_path = app_storage_path()
            except ImportError:
                # 开发环境或非 Android
                storage_path = os.path.dirname(os.path.abspath(__file__))
        else:
            # 开发环境
            storage_path = os.path.dirname(os.path.abspath(__file__))
        
        # 确保目录存在
        os.makedirs(storage_path, exist_ok=True)
        return os.path.join(storage_path, 'novel.db')
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建书籍表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_name TEXT NOT NULL,
                author TEXT,
                book_origin TEXT,
                catalogue_url TEXT,
                catalogue TEXT,
                catalogue_len INTEGER DEFAULT 0,
                last_read_chapter INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 检查并添加新字段（兼容旧表）
        cursor.execute("PRAGMA table_info(books)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'catalogue_len' not in columns:
            cursor.execute("ALTER TABLE books ADD COLUMN catalogue_len INTEGER DEFAULT 0")
        if 'book_origin' not in columns:
            cursor.execute("ALTER TABLE books ADD COLUMN book_origin TEXT")
        if 'catalogue_url' not in columns:
            cursor.execute("ALTER TABLE books ADD COLUMN catalogue_url TEXT")

        # 创建章节表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                chapter_index INTEGER,
                title TEXT,
                content TEXT,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        ''')

        conn.commit()
        conn.close()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def get_all_books(self):
        """获取所有书籍"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, book_name, author, book_origin, catalogue_url, catalogue, '
                       'catalogue_len, last_read_chapter, status, created_at FROM books ORDER BY created_at DESC')
        books = cursor.fetchall()
        conn.close()
        return books
    
    def get_book(self, book_id):
        """获取单本书籍"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        book = cursor.fetchone()
        conn.close()
        return book

    def get_book_by_name_author(self, book_name, author=''):
        """按书名和作者查找书籍（用于云同步去重）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM books WHERE book_name = ? AND author = ?', (book_name, author))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def add_book(self, book_name, author='', catalogue='', book_origin='', catalogue_url=''):
        """添加书籍"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO books (book_name, author, catalogue, book_origin, catalogue_url) VALUES (?, ?, ?, ?, ?)',
            (book_name, author, catalogue, book_origin, catalogue_url)
        )
        book_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return book_id
    
    def update_book(self, book_id, **kwargs):
        """更新书籍信息"""
        allowed_fields = ['book_name', 'author', 'book_origin', 'catalogue_url', 'catalogue', 'catalogue_len', 'last_read_chapter', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return

        # 处理 catalogue（转换为 JSON 字符串存储）
        if 'catalogue' in updates:
            import json
            updates['catalogue'] = json.dumps(updates['catalogue'], ensure_ascii=False)

        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [book_id]
        cursor.execute(f'UPDATE books SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
    
    def delete_book(self, book_id):
        """删除书籍"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chapters WHERE book_id = ?', (book_id,))
        cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()
        conn.close()
    
    def get_chapters(self, book_id):
        """获取书籍所有章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, book_id, chapter_index, title, content FROM chapters WHERE book_id = ? ORDER BY chapter_index',
            (book_id,)
        )
        chapters = cursor.fetchall()
        conn.close()
        return chapters
    
    def get_chapter(self, book_id, chapter_index):
        """获取单个章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM chapters WHERE book_id = ? AND chapter_index = ?',
            (book_id, chapter_index)
        )
        chapter = cursor.fetchone()
        conn.close()
        return chapter
    
    def add_chapter(self, book_id, chapter_index, title, content):
        """添加或更新章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO chapters 
               (book_id, chapter_index, title, content) 
               VALUES (?, ?, ?, ?)''',
            (book_id, chapter_index, title, content)
        )
        conn.commit()
        conn.close()
    
    def delete_chapters(self, book_id):
        """删除书籍所有章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chapters WHERE book_id = ?', (book_id,))
        conn.commit()
        conn.close()
    
    def update_read_progress(self, book_id, chapter_index):
        """更新阅读进度"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE books SET last_read_chapter = ? WHERE id = ?',
            (chapter_index, book_id)
        )
        conn.commit()
        conn.close()
    
    def search_books(self, keyword):
        """搜索书籍"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT * FROM books 
               WHERE book_name LIKE ? OR author LIKE ?
               ORDER BY created_at DESC''',
            (f'%{keyword}%', f'%{keyword}%')
        )
        books = cursor.fetchall()
        conn.close()
        return books
    
    def get_book_count(self):
        """获取书籍数量"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM books')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_chapter_count(self, book_id):
        """获取章节数量"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM chapters WHERE book_id = ?', (book_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
