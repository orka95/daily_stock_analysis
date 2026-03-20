# -*- coding: utf-8 -*-
"""
本地新聞源解析器抽象基類

未來新增來源只需：
1. 繼承 BaseNewsParser
2. 實作 can_parse() / parse() / source_name
3. 放入 src/local_news/ 目錄即可自動載入
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NewsItem:
    """統一新聞項目格式"""
    title: str
    snippet: str
    url: str
    source: str
    published_date: str = ""
    tags: List[str] = field(default_factory=list)
    provider: str = ""


class BaseNewsParser(ABC):
    """本地新聞源解析器抽象基類"""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """來源名稱，例如 'Wantgoo'、'CNYES'"""
        pass

    @abstractmethod
    def can_parse(self, filepath: str) -> bool:
        """判斷此檔案是否為該來源的格式"""
        pass

    @abstractmethod
    def parse(
        self,
        filepath: str,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
    ) -> List[NewsItem]:
        """
        解析新聞檔案，回傳符合條件的新聞列表

        Args:
            filepath: 新聞檔案路徑
            stock_code: 股票代碼（用於過濾）
            stock_name: 股票名稱（用於過濾）
        """
        pass

    def _build_keywords(self, stock_code: Optional[str], stock_name: Optional[str]) -> set:
        """建立過濾關鍵詞（通用輔助方法）"""
        import re
        keywords = set()
        if stock_name:
            keywords.add(stock_name.lower())
        if stock_code:
            bare_code = re.sub(r'^(tw|hk)', '', stock_code, flags=re.IGNORECASE)
            keywords.add(bare_code.lower())
            keywords.add(stock_code.lower())
        keywords.discard('')
        return keywords
