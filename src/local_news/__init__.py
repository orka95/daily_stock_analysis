# -*- coding: utf-8 -*-
"""
本地新聞源管理器

自動載入 src/local_news/ 目錄下的所有 parser，
掃描 LOCAL_NEWS_DIRS 中的檔案，自動匹配對應 parser。

新增來源只需在此目錄新增一個 *_parser.py，無需改其他程式碼。
"""

import glob
import importlib
import inspect
import os
import pkgutil
from datetime import datetime
from typing import Dict, List, Optional

from src.local_news.base import BaseNewsParser, NewsItem


class LocalNewsManager:
    """統一本地新聞入口"""

    def __init__(self, news_dirs: List[str]):
        self._news_dirs = news_dirs
        self._parsers: List[BaseNewsParser] = []
        self._load_parsers()

    def _load_parsers(self):
        """自動掃描並載入所有 parser"""
        package_dir = os.path.dirname(__file__)
        for _, module_name, _ in pkgutil.iter_modules([package_dir]):
            if module_name in ("base", "__init__"):
                continue
            module = importlib.import_module(f"src.local_news.{module_name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, BaseNewsParser) and cls is not BaseNewsParser:
                    self._parsers.append(cls())

    @property
    def parsers(self) -> List[BaseNewsParser]:
        return self._parsers

    def search(
        self,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        date: Optional[str] = None,
    ) -> List[Dict]:
        """
        搜尋本地新聞

        Args:
            stock_code: 股票代碼
            stock_name: 股票名稱
            date: 日期字串 YYYY-MM-DD（預設今天）

        Returns:
            新聞列表（dict 格式，相容現有 API 回傳）
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        all_items: List[NewsItem] = []

        for news_dir in self._news_dirs:
            if not os.path.isdir(news_dir):
                continue
            # 掃描目錄下所有 JSON 檔案（今日的）
            for filepath in glob.glob(os.path.join(news_dir, f"*{date}*.json")):
                for parser in self._parsers:
                    if parser.can_parse(filepath):
                        items = parser.parse(filepath, stock_code, stock_name)
                        all_items.extend(items)
                        break  # 一個檔案只由一個 parser 處理

        # 轉為 dict 格式（相容現有 API）
        return [
            {
                "title": item.title,
                "snippet": item.snippet,
                "url": item.url,
                "source": item.source,
                "published_date": item.published_date,
                "tags": item.tags,
                "provider": item.provider,
            }
            for item in all_items
        ]
