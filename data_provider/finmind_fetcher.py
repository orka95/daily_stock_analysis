# -*- coding: utf-8 -*-
"""
===================================
FinMindFetcher - 台股專用數據源 (Priority 1)
===================================

數據來源：FinMind (https://finmindtrade.com/)
特點：台股官方 TWSE/TPEx 數據，品質優於 Yahoo Finance
定位：台股歷史 OHLCV 首選數據源

支援數據：
1. 歷史日線 OHLCV（TaiwanStockPrice）
2. 三大法人買賣超（TaiwanStockInstitutionalInvestorsBuySell）
3. 本益比/股價淨值比（TaiwanStockPER）

設定：
- 環境變數 FINMIND_API_TOKEN：FinMind API token（增加至 600 次/小時）
- 環境變數 FINMIND_PRIORITY：優先級（預設 1）

注意事項：
- 免費版：300 次/小時，無需帳號
- 註冊版：600 次/小時，需 email 註冊取得 token
- 即時報價不支援（需贊助會員），退回 YFinanceFetcher
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS
from .tw_stock_mapping import is_tw_stock_code, convert_tw_stock_code, get_tw_stock_name

logger = logging.getLogger(__name__)


class FinMindFetcher(BaseFetcher):
    """
    FinMind 台股數據源

    優先級：1（台股歷史資料首選）
    數據來源：FinMind API（直接對接 TWSE/TPEx）

    只處理台股（TW 前綴），其他市場不支援。
    即時報價不支援，由 YFinanceFetcher 負責。
    """

    name = "FinMindFetcher"
    priority = int(os.getenv("FINMIND_PRIORITY", "1"))

    def __init__(self):
        self._token = os.getenv("FINMIND_API_TOKEN", "")
        self._api = None  # 快取 DataLoader 實例，避免重複登入
        if self._token:
            logger.info("[FinMind] 已載入 API token，限速 600 次/小時")
        else:
            logger.info("[FinMind] 未設定 API token，限速 300 次/小時")

    def _get_api(self):
        """取得 FinMind DataLoader 實例（含 token），快取避免重複登入"""
        if self._api is not None:
            return self._api
        try:
            from FinMind.data import DataLoader
        except ImportError:
            raise DataFetchError(
                "FinMind 未安裝，請執行: pip install finmind"
            )
        api = DataLoader()
        if self._token:
            api.login_by_token(api_token=self._token)
        self._api = api
        return api

    def _extract_stock_id(self, stock_code: str) -> str:
        """
        從台股代碼提取純數字部分供 FinMind 使用。

        TW2330  -> '2330'
        TW6488O -> '6488'（上櫃，僅取數字）
        """
        upper = stock_code.strip().upper()
        # 移除 TW 前綴
        if upper.startswith("TW"):
            numeric = upper[2:]
            # 移除末尾 O（上櫃標記）
            if numeric.endswith("O"):
                numeric = numeric[:-1]
            return numeric
        return upper

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        從 FinMind 取得台股日線資料。

        Args:
            stock_code: 台股代碼（帶 TW 前綴，如 TW2330）
            start_date: 開始日期（YYYY-MM-DD）
            end_date: 結束日期（YYYY-MM-DD）

        Returns:
            原始 DataFrame（FinMind 格式）
        """
        if not is_tw_stock_code(stock_code):
            raise DataFetchError(
                f"[FinMind] 只支援台股（TW 前綴），收到: {stock_code}"
            )

        stock_id = self._extract_stock_id(stock_code)
        logger.debug(f"[FinMind] 查詢 {stock_code} -> stock_id={stock_id}, {start_date}~{end_date}")

        try:
            api = self._get_api()
            df = api.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date,
            )
        except DataFetchError:
            raise
        except Exception as e:
            raise DataFetchError(f"[FinMind] 取得 {stock_code} 失敗: {e}") from e

        if df is None or df.empty:
            raise DataFetchError(f"[FinMind] {stock_code} 無資料（{start_date}~{end_date}）")

        return df

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        將 FinMind 日線資料標準化為系統通用格式。

        FinMind 欄位：
            date, stock_id, Trading_Volume, Trading_money,
            open, max, min, close, spread, Trading_turnover

        對應系統欄位：
            date, open, high, low, close, volume, amount, pct_chg
        """
        df = df.copy()

        # 欄位對應
        column_mapping = {
            "date": "date",
            "open": "open",
            "max": "high",
            "min": "low",
            "close": "close",
            "Trading_Volume": "volume",
            "Trading_money": "amount",
        }
        df = df.rename(columns=column_mapping)

        # 計算漲跌幅（FinMind 不直接提供）
        if "close" in df.columns:
            df["pct_chg"] = df["close"].pct_change() * 100
            df["pct_chg"] = df["pct_chg"].fillna(0).round(2)

        # 加入股票代碼欄位
        df["code"] = stock_code

        # 只保留需要的欄位
        keep_cols = ["code"] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]

        return df

    def get_institutional_investors(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        days: int = 30,
    ) -> Optional[pd.DataFrame]:
        """
        取得三大法人買賣超資料。

        Args:
            stock_code: 台股代碼（TW 前綴）
            start_date: 開始日期，預設為 days 天前
            days: 查詢天數（start_date 未指定時使用）

        Returns:
            DataFrame 含欄位：date, name（法人別）, buy, sell, diff
            法人別（name）：Foreign_Investor, Investment_Trust, Dealer_self
            失敗時回傳 None
        """
        if not is_tw_stock_code(stock_code):
            return None

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        stock_id = self._extract_stock_id(stock_code)

        try:
            api = self._get_api()
            df = api.taiwan_stock_institutional_investors(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date,
            )
            if df is None or df.empty:
                return None

            # 標準化欄位名稱
            df = df.rename(columns={
                "buy": "buy",
                "sell": "sell",
                "name": "name",
            })
            # 計算買賣超
            if "buy" in df.columns and "sell" in df.columns:
                df["diff"] = df["buy"] - df["sell"]

            logger.info(f"[FinMind] {stock_code} 三大法人資料 {len(df)} 筆")
            return df

        except Exception as e:
            logger.warning(f"[FinMind] {stock_code} 三大法人資料取得失敗: {e}")
            return None

    def get_per_pbr(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        days: int = 30,
    ) -> Optional[pd.DataFrame]:
        """
        取得本益比/股價淨值比資料。

        Args:
            stock_code: 台股代碼（TW 前綴）
            start_date: 開始日期
            days: 查詢天數

        Returns:
            DataFrame 含欄位：date, PER（本益比）, PBR（股價淨值比）
            失敗時回傳 None
        """
        if not is_tw_stock_code(stock_code):
            return None

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        stock_id = self._extract_stock_id(stock_code)

        try:
            api = self._get_api()
            df = api.taiwan_stock_per_pbr(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date,
            )
            if df is None or df.empty:
                return None

            logger.info(f"[FinMind] {stock_code} PER/PBR 資料 {len(df)} 筆")
            return df

        except Exception as e:
            logger.warning(f"[FinMind] {stock_code} PER/PBR 資料取得失敗: {e}")
            return None
