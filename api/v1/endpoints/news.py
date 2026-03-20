# -*- coding: utf-8 -*-
"""
本地新聞 API
透過 LocalNewsManager 讀取本地新聞源（支援玩股網及未來新增的來源）。
"""

from typing import Optional

from fastapi import APIRouter, Query

from src.config import get_config
from src.local_news import LocalNewsManager

router = APIRouter()


@router.get("")
def get_local_news(
    stock_code: Optional[str] = Query(None),
    stock_name: Optional[str] = Query(None),
):
    config = get_config()
    manager = LocalNewsManager(config.local_news_dirs)
    items = manager.search(stock_code=stock_code, stock_name=stock_name)
    return {"total": len(items), "items": items}
