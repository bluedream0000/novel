# -*- coding: utf-8 -*-
"""爬虫管理器"""
import os
import sys


class SpiderManager:
    """爬虫管理器"""
    def __init__(self):
        self.spiders = {}
        self._add_spider_path()
        self._load_spiders()

    def _add_spider_path(self):
        """添加爬虫模块路径"""
        from config import PROJECT_ROOT
        # 将项目根目录添加到 Python 路径
        spider_dir = os.path.join(PROJECT_ROOT, 'spider')
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

    def _load_spiders(self):
        """加载爬虫模块"""
        try:
            from spider.spider_factory import SpiderFactory
            self.factory = SpiderFactory()
            print("爬虫模块加载成功")
        except Exception as e:
            print(f"加载爬虫失败: {e}")
            self.factory = None

    def search_book(self, keyword, callback=None):
        """搜索书籍（异步）"""
        if not self.factory:
            return []

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                self.factory.search_books(keyword, origin='biquuge')
            )
            loop.close()
            return results if results else []
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def download_book(self, book_url, book_name, progress_callback=None):
        """下载书籍"""
        # 实现下载逻辑
        pass
