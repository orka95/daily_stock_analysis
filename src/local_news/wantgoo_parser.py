# -*- coding: utf-8 -*-
"""
玩股網 (Wantgoo) 本地新聞解析器

檔案格式：wantgoo_news_YYYY-MM-DD.json
"""

import json
import os
from typing import List, Optional

from src.local_news.base import BaseNewsParser, NewsItem

# 排除的 category 關鍵字
EXCLUDED_CATEGORIES = {'商品期貨'}


class WantgooParser(BaseNewsParser):

    @property
    def source_name(self) -> str:
        return "Wantgoo"

    def can_parse(self, filepath: str) -> bool:
        basename = os.path.basename(filepath)
        return basename.startswith("wantgoo_news_") and basename.endswith(".json")

    def parse(
        self,
        filepath: str,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
    ) -> List[NewsItem]:
        keywords = self._build_keywords(stock_code, stock_name)
        items = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return items

        for article in data:
            category = article.get("category", "")
            if any(exc in category for exc in EXCLUDED_CATEGORIES):
                continue

            # 關鍵詞過濾
            if keywords:
                searchable = (
                    f"{article.get('headline', '')} "
                    f"{article.get('summary', '')} "
                    f"{' '.join(article.get('tags', []))}"
                ).lower()
                if not any(kw in searchable for kw in keywords):
                    continue

            items.append(NewsItem(
                title=article.get("headline", ""),
                snippet=(article.get("content_text", "") or article.get("summary", ""))[:500],
                url=article.get("url", ""),
                source=f"玩股網 ({category})",
                published_date=article.get("time", ""),
                tags=article.get("tags", []),
                provider="Wantgoo本地",
            ))

        return items
