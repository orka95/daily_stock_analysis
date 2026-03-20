import type React from 'react';
import { useState, useEffect, useCallback } from 'react';
import type { ParsedApiError } from '../../api/error';
import { getParsedApiError } from '../../api/error';
import { Card } from '../common';
import { ApiErrorAlert } from '../common';
import { historyApi, newsApi } from '../../api/history';
import type { NewsIntelItem } from '../../types/analysis';

interface ReportNewsProps {
  recordId?: number;
  limit?: number;
  stockCode?: string;
  stockName?: string;
}

const PAGE_SIZE = 20;

const isGoogleNews = (item: NewsIntelItem) =>
  (item.provider ?? '').toLowerCase().includes('google') ||
  (item.url ?? '').includes('news.google.com');

const NewsItem: React.FC<{ item: NewsIntelItem }> = ({ item }) => (
  <div className="group p-3 rounded-lg bg-elevated/80 border border-white/5 hover:border-cyan/30 hover:bg-hover transition-colors">
    <div className="flex items-start justify-between gap-3">
      <div className="flex-1 min-w-0 text-left">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm text-white font-medium leading-snug text-left">
            {item.title}
          </p>
          {item.publishedDate && (
            <span className="px-1.5 py-0.5 rounded bg-white/5 text-[10px] text-cyan/70 whitespace-nowrap">
              {item.publishedDate}
            </span>
          )}
        </div>
        {item.snippet && (
          <p className="text-xs text-secondary mt-1 text-left">
            {item.snippet}
          </p>
        )}
      </div>
      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-cyan hover:text-white transition-colors inline-flex items-center gap-1 whitespace-nowrap"
        >
          跳转
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 3h7m0 0v7m0-7L10 14" />
          </svg>
        </a>
      )}
    </div>
  </div>
);

const Pagination: React.FC<{ page: number; total: number; onPage: (p: number) => void }> = ({ page, total, onPage }) => {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center gap-2 mt-3 justify-end">
      <button
        type="button"
        disabled={page === 1}
        onClick={() => onPage(page - 1)}
        className="text-xs px-2 py-1 rounded bg-white/5 text-secondary hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        &lt;
      </button>
      <span className="text-xs text-secondary">{page} / {totalPages}</span>
      <button
        type="button"
        disabled={page === totalPages}
        onClick={() => onPage(page + 1)}
        className="text-xs px-2 py-1 rounded bg-white/5 text-secondary hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        &gt;
      </button>
    </div>
  );
};

/**
 * 资讯区组件 - 分頁籤顯示（Tavily / Google News）
 */
export const ReportNews: React.FC<ReportNewsProps> = ({ recordId, limit = 200, stockCode, stockName }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [items, setItems] = useState<NewsIntelItem[]>([]);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [activeTab, setActiveTab] = useState<'tavily' | 'google' | 'wantgoo'>('tavily');
  const [tavilyPage, setTavilyPage] = useState(1);
  const [googlePage, setGooglePage] = useState(1);
  const [wantgooPage, setWantgooPage] = useState(1);
  const [wantgooItems, setWantgooItems] = useState<NewsIntelItem[]>([]);

  const fetchNews = useCallback(async () => {
    if (!recordId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await historyApi.getNews(recordId, limit);
      setItems(response.items || []);
    } catch (err) {
      setError(getParsedApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [recordId, limit]);

  const handleRefreshNews = useCallback(async () => {
    if (!recordId) return;
    setIsRefreshing(true);
    setError(null);
    try {
      const response = await historyApi.refreshNews(recordId, limit);
      setItems(response.items || []);
    } catch (err) {
      setError(getParsedApiError(err));
    } finally {
      setIsRefreshing(false);
    }
  }, [recordId, limit]);

  useEffect(() => {
    setItems([]);
    setError(null);
    setTavilyPage(1);
    setGooglePage(1);
    setWantgooPage(1);
    if (recordId) fetchNews();
  }, [recordId, fetchNews]);

  useEffect(() => {
    newsApi.getWantgooNews(stockCode, stockName).then(r => setWantgooItems(r.items || [])).catch(() => {});
  }, [stockCode, stockName]);

  if (!recordId) return null;

  const googleItems = items.filter(i => isGoogleNews(i));
  const tavilyItems = items.filter(i => !isGoogleNews(i));

  const currentItems = activeTab === 'tavily' ? tavilyItems : activeTab === 'google' ? googleItems : wantgooItems;
  const currentPage = activeTab === 'tavily' ? tavilyPage : activeTab === 'google' ? googlePage : wantgooPage;
  const setCurrentPage = activeTab === 'tavily' ? setTavilyPage : activeTab === 'google' ? setGooglePage : setWantgooPage;
  const pagedItems = currentItems.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  return (
    <Card variant="bordered" padding="md">
      <div className="flex items-center justify-between mb-3">
        <div className="mb-3 flex items-baseline gap-2">
          <span className="label-uppercase">NEWS FEED</span>
          <h3 className="text-base font-semibold text-white">相关资讯</h3>
        </div>
        <div className="flex items-center gap-2">
          {(isLoading || isRefreshing) && (
            <div className="w-3.5 h-3.5 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
          )}
          <button
            type="button"
            onClick={fetchNews}
            disabled={isLoading || isRefreshing}
            className="text-xs text-cyan hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="從資料庫重新載入"
          >
            本機刷新
          </button>
          <span className="text-white/20">|</span>
          <button
            type="button"
            onClick={handleRefreshNews}
            disabled={isLoading || isRefreshing}
            className="text-xs text-yellow-400 hover:text-yellow-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            title="重新搜尋網路最新新聞並更新"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            抓取最新
          </button>
        </div>
      </div>

      {error && !isLoading && !isRefreshing && (
        <ApiErrorAlert error={error} actionLabel="重试" onAction={() => void fetchNews()} />
      )}

      {(isLoading || isRefreshing) && !error && (
        <div className="flex items-center gap-4 text-xs text-secondary">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
            {isRefreshing ? '正在重新抓取網路新聞...' : '加载资讯中...'}
          </div>
        </div>
      )}

      {!isLoading && !isRefreshing && !error && items.length === 0 && (
        <div className="text-xs text-muted">暂无相关资讯</div>
      )}

      {!isLoading && !isRefreshing && !error && items.length > 0 && (
        <>
          {/* 頁籤 */}
          <div className="flex gap-1 mb-3 border-b border-white/10">
            <button
              type="button"
              onClick={() => { setActiveTab('tavily'); setTavilyPage(1); }}
              className={`px-3 py-1.5 text-xs font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'tavily'
                  ? 'border-cyan text-cyan'
                  : 'border-transparent text-secondary hover:text-white'
              }`}
            >
              Tavily
              <span className="ml-1.5 px-1 py-0.5 rounded bg-white/10 text-[10px]">{tavilyItems.length}</span>
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('google'); setGooglePage(1); }}
              className={`px-3 py-1.5 text-xs font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'google'
                  ? 'border-cyan text-cyan'
                  : 'border-transparent text-secondary hover:text-white'
              }`}
            >
              Google News
              <span className="ml-1.5 px-1 py-0.5 rounded bg-white/10 text-[10px]">{googleItems.length}</span>
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('wantgoo'); setWantgooPage(1); }}
              className={`px-3 py-1.5 text-xs font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'wantgoo'
                  ? 'border-cyan text-cyan'
                  : 'border-transparent text-secondary hover:text-white'
              }`}
            >
              玩股網
              <span className="ml-1.5 px-1 py-0.5 rounded bg-white/10 text-[10px]">{wantgooItems.length}</span>
            </button>
          </div>

          {/* 新聞列表 */}
          {pagedItems.length === 0 ? (
            <div className="text-xs text-muted">此來源暫無資訊</div>
          ) : (
            <div className="space-y-2 text-left">
              {pagedItems.map((item, index) => (
                <NewsItem key={`${item.title}-${index}`} item={item} />
              ))}
            </div>
          )}

          {/* 分頁 */}
          <Pagination page={currentPage} total={currentItems.length} onPage={setCurrentPage} />
        </>
      )}
    </Card>
  );
};
