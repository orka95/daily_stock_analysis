# -*- coding: utf-8 -*-
"""
===================================
历史查询服务层
===================================

职责：
1. 封装历史记录查询逻辑
2. 提供分页和筛选功能
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from src.storage import DatabaseManager
from src.utils.data_processing import normalize_model_used, parse_json_field

logger = logging.getLogger(__name__)


class HistoryService:
    """
    历史查询服务
    
    封装历史分析记录的查询逻辑
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化历史查询服务
        
        Args:
            db_manager: 数据库管理器（可选，默认使用单例）
        """
        self.db = db_manager or DatabaseManager.get_instance()
    
    def get_history_list(
        self,
        stock_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取历史分析列表
        
        Args:
            stock_code: 股票代码筛选
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            page: 页码
            limit: 每页数量
            
        Returns:
            包含 total, items 的字典
        """
        try:
            # 解析日期参数
            start_dt = None
            end_dt = None
            
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"无效的 start_date 格式: {start_date}")
            
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"无效的 end_date 格式: {end_date}")
            
            # 计算 offset
            offset = (page - 1) * limit
            
            # 使用新的分页查询方法
            records, total = self.db.get_analysis_history_paginated(
                code=stock_code,
                start_date=start_dt,
                end_date=end_dt,
                offset=offset,
                limit=limit
            )
            
            # 转换为响应格式
            items = []
            for record in records:
                items.append({
                    "id": record.id,
                    "query_id": record.query_id,
                    "stock_code": record.code,
                    "stock_name": record.name,
                    "report_type": record.report_type,
                    "sentiment_score": record.sentiment_score,
                    "operation_advice": record.operation_advice,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                })
            
            return {
                "total": total,
                "items": items,
            }
            
        except Exception as e:
            logger.error(f"查询历史列表失败: {e}", exc_info=True)
            return {"total": 0, "items": []}

    def _resolve_record(self, record_id: str):
        """
        Resolve a record_id parameter to an AnalysisHistory object.

        Tries integer primary key first; falls back to query_id string lookup
        when the value is not a valid integer.

        Args:
            record_id: integer PK (as string) or query_id string

        Returns:
            AnalysisHistory object or None
        """
        try:
            int_id = int(record_id)
            record = self.db.get_analysis_history_by_id(int_id)
            if record:
                return record
        except (ValueError, TypeError):
            pass
        # Fall back to query_id lookup
        return self.db.get_latest_analysis_by_query_id(record_id)

    def resolve_and_get_detail(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve record_id (int PK or query_id string) and return history detail.

        Args:
            record_id: integer PK (as string) or query_id string

        Returns:
            Complete analysis report dict, or None
        """
        try:
            record = self._resolve_record(record_id)
            if not record:
                return None
            return self._record_to_detail_dict(record)
        except Exception as e:
            logger.error(f"resolve_and_get_detail failed for {record_id}: {e}", exc_info=True)
            return None

    def resolve_and_get_news(self, record_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        Resolve record_id (int PK or query_id string) and return associated news.

        Args:
            record_id: integer PK (as string) or query_id string
            limit: max items to return

        Returns:
            List of news intel dicts
        """
        try:
            record = self._resolve_record(record_id)
            if not record:
                logger.warning(f"resolve_and_get_news: record not found for {record_id}")
                return []
            return self.get_news_intel(query_id=record.query_id, limit=limit)
        except Exception as e:
            logger.error(f"resolve_and_get_news failed for {record_id}: {e}", exc_info=True)
            return []

    def get_history_detail_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取历史报告详情

        使用数据库主键精确查询，避免 query_id 在批量分析时重复导致返回错误记录。

        Args:
            record_id: 分析历史记录主键 ID

        Returns:
            完整的分析报告字典，不存在返回 None
        """
        try:
            record = self.db.get_analysis_history_by_id(record_id)
            if not record:
                return None
            return self._record_to_detail_dict(record)
        except Exception as e:
            logger.error(f"根据 ID 查询历史详情失败: {e}", exc_info=True)
            return None

    def _record_to_detail_dict(self, record) -> Dict[str, Any]:
        """
        Convert an AnalysisHistory ORM record to a detail response dict.
        """
        raw_result = parse_json_field(record.raw_result)

        model_used = (raw_result or {}).get("model_used") if isinstance(raw_result, dict) else None
        model_used = normalize_model_used(model_used)

        context_snapshot = None
        if record.context_snapshot:
            try:
                context_snapshot = json.loads(record.context_snapshot)
            except json.JSONDecodeError:
                context_snapshot = record.context_snapshot

        return {
            "id": record.id,
            "query_id": record.query_id,
            "stock_code": record.code,
            "stock_name": record.name,
            "report_type": record.report_type,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "model_used": model_used,
            "analysis_summary": record.analysis_summary,
            "operation_advice": record.operation_advice,
            "trend_prediction": record.trend_prediction,
            "sentiment_score": record.sentiment_score,
            "sentiment_label": self._get_sentiment_label(record.sentiment_score or 50),
            "ideal_buy": str(record.ideal_buy) if record.ideal_buy else None,
            "secondary_buy": str(record.secondary_buy) if record.secondary_buy else None,
            "stop_loss": str(record.stop_loss) if record.stop_loss else None,
            "take_profit": str(record.take_profit) if record.take_profit else None,
            "news_content": record.news_content,
            "raw_result": raw_result,
            "context_snapshot": context_snapshot,
        }

    def get_news_intel(self, query_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        获取指定 query_id 关联的新闻情报

        Args:
            query_id: 分析记录唯一标识
            limit: 返回数量限制

        Returns:
            新闻情报列表（包含 title、snippet、url）
        """
        try:
            records = self.db.get_news_intel_by_query_id(query_id=query_id)

            if not records:
                records = self._fallback_news_by_analysis_context(query_id=query_id, limit=limit)

            items: List[Dict[str, str]] = []
            for record in records:
                snippet = (record.snippet or "").strip()
                if len(snippet) > 200:
                    snippet = f"{snippet[:197]}..."
                # 只顯示新聞來源提供的真正發布時間（轉換為台灣時間 UTC+8）
                pub_date = getattr(record, 'published_date', None)
                pub_date_str = None
                if pub_date:
                    from datetime import timezone, timedelta
                    utc = timezone.utc
                    tw_tz = timezone(timedelta(hours=8))
                    # SQLite 不保存時區，讀出來是 naive datetime，一律視為 UTC
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=utc)
                    pub_date_str = pub_date.astimezone(tw_tz).strftime('%Y-%m-%d %H:%M')
                
                items.append({
                    "title": record.title,
                    "snippet": snippet,
                    "url": record.url,
                    "published_date": pub_date_str,
                    "provider": getattr(record, 'provider', None),
                })

            return items

        except Exception as e:
            logger.error(f"查询新闻情报失败: {e}", exc_info=True)
            return []

    def get_news_intel_by_record_id(self, record_id: int, limit: int = 20) -> List[Dict[str, str]]:
        """
        根据分析历史记录 ID 获取关联的新闻情报

        将 record_id 解析为 query_id，再调用 get_news_intel。

        Args:
            record_id: 分析历史记录主键 ID
            limit: 返回数量限制

        Returns:
            新闻情报列表（包含 title、snippet、url）
        """
        try:
            # 根据 record_id 查出对应的 AnalysisHistory 记录
            record = self.db.get_analysis_history_by_id(record_id)
            if not record:
                logger.warning(f"未找到 record_id={record_id} 的分析记录")
                return []

            # 从记录中获取 query_id，然后调用原方法
            return self.get_news_intel(query_id=record.query_id, limit=limit)

        except Exception as e:
            logger.error(f"根据 record_id 查询新闻情报失败: {e}", exc_info=True)
            return []

    def refresh_news(self, record_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        重新获取指定分析记录的新闻情报并更新数据库。

        Args:
            record_id: 分析历史记录主键 ID（整数）或 query_id（字符串）
            limit: 返回数量限制

        Returns:
            更新后的新闻情报列表
        """
        try:
            from src.search_service import SearchService
            from src.config import get_config
            import time

            # 1. 查找分析记录以获取 stock_code 和 stock_name
            record = self._resolve_record(record_id)
            if not record:
                logger.warning(f"refresh_news: record not found for {record_id}")
                return []

            stock_code = record.code
            stock_name = record.name
            query_id = record.query_id

            # 2. 初始化 SearchService
            config = get_config()
            search_service = SearchService(
                bocha_keys=config.bocha_api_keys,
                tavily_keys=config.tavily_api_keys,
                brave_keys=config.brave_api_keys,
                serpapi_keys=config.serpapi_keys,
                news_max_age_days=config.news_max_age_days,
                local_news_dirs=config.local_news_dirs,
            )

            if not search_service.is_available:
                logger.warning(f"[{stock_code}] 刷新新闻失败: 搜索服务不可用")
                return self.get_news_intel(query_id=query_id, limit=limit)

            # 3. 执行新闻搜索
            logger.info(f"[{stock_code}] 开始刷新新闻情报...")
            news_response = search_service.search_stock_news(
                stock_code=stock_code,
                stock_name=stock_name,
                max_results=limit
            )

            # 4. 如果搜索成功，保存到数据库
            if news_response and news_response.success and news_response.results:
                # 重新构建一个查询上下文
                query_context = {
                    "query_id": query_id,
                    "target": stock_code,
                    "target_name": stock_name,
                    "api_version": "v1",
                    "timestamp": time.time(),
                }
                
                # 先清除該 query_id 的舊資料，避免累積
                self.db.delete_news_intel_by_query_id(query_id=query_id)

                self.db.save_news_intel(
                    code=stock_code,
                    name=stock_name,
                    dimension="latest_news",
                    query=news_response.query,
                    response=news_response,
                    query_context=query_context
                )
                
                logger.info(f"[{stock_code}] 新闻情报刷新并保存成功，新增/更新 {len(news_response.results)} 条")
            else:
                logger.warning(f"[{stock_code}] 刷新新闻搜索未返回有效结果")

            # 5. 返回最新的新闻列表
            return self.get_news_intel(query_id=query_id, limit=limit)

        except Exception as e:
            logger.error(f"refresh_news failed for {record_id}: {e}", exc_info=True)
            return self.get_news_intel(query_id=record_id, limit=limit)  # 失败时回退到返回现有结果

    def _fallback_news_by_analysis_context(self, query_id: str, limit: int) -> List[Any]:
        """
        Fallback by analysis context when direct query_id lookup returns no news.

        Typical scenarios:
        - URL-level dedup keeps one canonical news row across repeated analyses.
        - Legacy records may have different historical query_id strategies.
        """
        records = self.db.get_analysis_history(query_id=query_id, limit=1)
        if not records:
            return []

        analysis = records[0]
        if not analysis.code or not analysis.created_at:
            return []

        # Narrow down to same-stock recent news, then filter by analysis time window.
        days = max(1, (datetime.now() - analysis.created_at).days + 1)
        candidates = self.db.get_recent_news(code=analysis.code, days=days, limit=max(limit * 5, 50))

        start_time = analysis.created_at - timedelta(hours=6)
        end_time = analysis.created_at + timedelta(hours=6)
        matched = [
            item for item in candidates
            if item.fetched_at and start_time <= item.fetched_at <= end_time
        ]

        return matched[:limit]
    
    def _get_sentiment_label(self, score: int) -> str:
        """
        根据评分获取情绪标签
        
        Args:
            score: 情绪评分 (0-100)
            
        Returns:
            情绪标签
        """
        if score >= 80:
            return "极度乐观"
        elif score >= 60:
            return "乐观"
        elif score >= 40:
            return "中性"
        elif score >= 20:
            return "悲观"
        else:
            return "极度悲观"
