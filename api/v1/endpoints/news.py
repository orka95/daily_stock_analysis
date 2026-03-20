# -*- coding: utf-8 -*-
"""
玩股網本地新聞 API
直接讀取今日的 wantgoo_news_YYYY-MM-DD.json，不經過 DB。
"""

import glob
import json
import os
from datetime import datetime

import re
from typing import Optional

from fastapi import APIRouter, Query

from src.config import get_config

router = APIRouter()

# 排除的 category 關鍵字（商品期貨相關）
EXCLUDED_CATEGORIES = {'商品期貨'}


@router.get("")
def get_wantgoo_news(
    stock_code: Optional[str] = Query(None),
    stock_name: Optional[str] = Query(None),
):
    config = get_config()
    today = datetime.now().strftime("%Y-%m-%d")
    items = []

    # 建立過濾關鍵詞
    keywords = set()
    if stock_name:
        keywords.add(stock_name.lower())
    if stock_code:
        bare_code = re.sub(r'^(tw|hk)', '', stock_code, flags=re.IGNORECASE)
        keywords.add(bare_code.lower())
        keywords.add(stock_code.lower())
    keywords.discard('')

    for news_dir in config.local_news_dirs:
        pattern = os.path.join(news_dir, f"wantgoo_news_{today}.json")
        files = glob.glob(pattern)
        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
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

                    items.append({
                        "title": article.get("headline", ""),
                        "snippet": (article.get("content_text", "") or article.get("summary", ""))[:500],
                        "url": article.get("url", ""),
                        "source": f"玩股網 ({category})",
                        "published_date": article.get("time", ""),
                        "tags": article.get("tags", []),
                        "provider": "Wantgoo本地",
                    })
            except Exception:
                pass

    return {"total": len(items), "items": items}
