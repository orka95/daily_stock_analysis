import type React from 'react';
import { useEffect, useState } from 'react';
import { useAuth, useSystemConfig } from '../hooks';
import { ApiErrorAlert } from '../components/common';
import {
  ChangePasswordCard,
  ImageStockExtractor,
  LLMChannelEditor,
  SettingsAlert,
  SettingsField,
  SettingsLoading,
} from '../components/settings';
import { getCategoryDescriptionZh, getCategoryTitleZh } from '../utils/systemConfigI18n';
import { systemConfigApi, type UsageStatsResponse } from '../api/systemConfig';

const SettingsPage: React.FC = () => {
  const { passwordChangeable } = useAuth();
  const {
    categories,
    itemsByCategory,
    issueByKey,
    activeCategory,
    setActiveCategory,
    hasDirty,
    dirtyCount,
    toast,
    clearToast,
    isLoading,
    isSaving,
    loadError,
    saveError,
    retryAction,
    load,
    retry,
    save,
    setDraftValue,
    configVersion,
    maskToken,
  } = useSystemConfig();

  const [stats, setStats] = useState<UsageStatsResponse | null>(null);

  useEffect(() => {
    void load();
    systemConfigApi.getStats().then(setStats).catch(() => null);
  }, [load]);

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timer = window.setTimeout(() => {
      clearToast();
    }, 3200);

    return () => {
      window.clearTimeout(timer);
    };
  }, [clearToast, toast]);

  const rawActiveItems = itemsByCategory[activeCategory] || [];

  // Hide per-channel LLM_*_ env vars from the normal field list;
  // they are managed by the LLMChannelEditor component instead.
  const LLM_CHANNEL_KEY_RE = /^LLM_[A-Z0-9]+_(BASE_URL|API_KEY|API_KEYS|MODELS|EXTRA_HEADERS)$/;
  const activeItems =
    activeCategory === 'ai_model'
      ? rawActiveItems.filter((item) => !LLM_CHANNEL_KEY_RE.test(item.key))
      : rawActiveItems;

  return (
    <div className="min-h-screen px-4 pb-6 pt-4 md:px-6">
      <header className="mb-4 rounded-2xl border border-white/8 bg-card/80 p-4 backdrop-blur-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">系統設定</h1>
            <p className="text-sm text-secondary">
              預設使用 .env 中的設定
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button type="button" className="btn-secondary" onClick={() => void load()} disabled={isLoading || isSaving}>
              重置
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => void save()}
              disabled={!hasDirty || isSaving || isLoading}
            >
              {isSaving ? '儲存中...' : `儲存設定${dirtyCount ? ` (${dirtyCount})` : ''}`}
            </button>
          </div>
        </div>

        {saveError ? (
          <ApiErrorAlert
            className="mt-3"
            error={saveError}
            actionLabel={retryAction === 'save' ? '重試儲存' : undefined}
            onAction={retryAction === 'save' ? () => void retry() : undefined}
          />
        ) : null}
      </header>

      {loadError ? (
        <ApiErrorAlert
          error={loadError}
          actionLabel={retryAction === 'load' ? '重試載入' : '重新載入'}
          onAction={() => void retry()}
          className="mb-4"
        />
      ) : null}

      {isLoading ? (
        <SettingsLoading />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-2xl border border-white/8 bg-card/60 p-3 backdrop-blur-sm">
            <p className="mb-2 text-xs uppercase tracking-wide text-muted">設定分類</p>
            <div className="space-y-2">
              {categories.map((category) => {
                const isActive = category.category === activeCategory;
                const count = (itemsByCategory[category.category] || []).length;
                const title = getCategoryTitleZh(category.category, category.title);
                const description = getCategoryDescriptionZh(category.category, category.description);

                return (
                  <button
                    key={category.category}
                    type="button"
                    className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                      isActive
                        ? 'border-accent bg-cyan/10 text-white'
                        : 'border-white/8 bg-elevated/40 text-secondary hover:border-white/16 hover:text-white'
                    }`}
                    onClick={() => setActiveCategory(category.category)}
                  >
                    <span className="flex items-center justify-between text-sm font-medium">
                      {title}
                      <span className="text-xs text-muted">{count}</span>
                    </span>
                    {description ? <span className="mt-1 block text-xs text-muted">{description}</span> : null}
                  </button>
                );
              })}

              {/* Token 使用統計 */}
              <button
                type="button"
                className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                  activeCategory === '__stats__'
                    ? 'border-accent bg-cyan/10 text-white'
                    : 'border-white/8 bg-elevated/40 text-secondary hover:border-white/16 hover:text-white'
                }`}
                onClick={() => setActiveCategory('__stats__' as never)}
              >
                <span className="flex items-center justify-between text-sm font-medium">
                  使用量統計
                  <span className="text-xs text-muted">token</span>
                </span>
                <span className="mt-1 block text-xs text-muted">AI 呼叫次數與 Token 用量。</span>
              </button>
            </div>
          </aside>

          <section className="space-y-3 rounded-2xl border border-white/8 bg-card/60 p-4 backdrop-blur-sm">
            {activeCategory === ('__stats__' as never) ? (
              <div className="space-y-4">
                <h2 className="text-base font-semibold text-white">使用量統計</h2>
                {stats ? (
                  <>
                    <div className="rounded-xl border border-white/8 bg-elevated/40 p-4 text-sm text-secondary">
                      <p className="mb-1 text-xs text-muted">使用模型</p>
                      <p className="font-mono text-white">{stats.modelName}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                      <StatCard label="總分析次數" value={stats.totalAnalyses.toLocaleString()} unit="次" />
                      <StatCard label="今日分析次數" value={stats.todayAnalyses.toLocaleString()} unit="次" />
                      <StatCard label="追蹤股票數" value={stats.totalStocks.toLocaleString()} unit="檔" />
                      <StatCard
                        label="今日估算 Token"
                        value={stats.estimatedTokensToday >= 1000
                          ? `${(stats.estimatedTokensToday / 1000).toFixed(1)}K`
                          : stats.estimatedTokensToday.toLocaleString()}
                        unit="tokens"
                      />
                      <StatCard
                        label="累計估算 Token"
                        value={stats.estimatedTokensTotal >= 1000
                          ? `${(stats.estimatedTokensTotal / 1000).toFixed(1)}K`
                          : stats.estimatedTokensTotal.toLocaleString()}
                        unit="tokens"
                      />
                    </div>
                    <p className="text-xs text-muted">
                      ＊Token 為估算值（每次分析約 3,000 tokens）。實際用量請至 AI 供應商後台確認。
                    </p>
                  </>
                ) : (
                  <div className="text-sm text-secondary">載入中...</div>
                )}
              </div>
            ) : null}
            {activeCategory === 'base' ? (
              <div className="space-y-3">
                <ImageStockExtractor
                  stockListValue={
                    (activeItems.find((i) => i.key === 'STOCK_LIST')?.value as string) ?? ''
                  }
                  configVersion={configVersion}
                  maskToken={maskToken}
                  onMerged={() => void load()}
                  disabled={isSaving || isLoading}
                />
              </div>
            ) : null}
            {activeCategory === 'ai_model' ? (
              <LLMChannelEditor
                items={rawActiveItems}
                configVersion={configVersion}
                maskToken={maskToken}
                onSaved={() => void load()}
                disabled={isSaving || isLoading}
              />
            ) : null}
            {activeCategory === 'system' && passwordChangeable ? (
              <div className="space-y-3">
                <ChangePasswordCard />
              </div>
            ) : null}
            {activeItems.length && activeCategory !== ('__stats__' as never) ? (
              activeItems.map((item) => (
                <SettingsField
                  key={item.key}
                  item={item}
                  value={item.value}
                  disabled={isSaving}
                  onChange={setDraftValue}
                  issues={issueByKey[item.key] || []}
                />
              ))
            ) : activeCategory !== ('__stats__' as never) && !activeItems.length ? (
              <div className="rounded-xl border border-white/8 bg-elevated/40 p-5 text-sm text-secondary">
                目前分類下暫無設定項目。
              </div>
            ) : null}
          </section>
        </div>
      )}

      {toast ? (
        <div className="fixed bottom-5 right-5 z-50 w-[320px] max-w-[calc(100vw-24px)]">
          {toast.type === 'success'
            ? <SettingsAlert title="操作成功" message={toast.message} variant="success" />
            : <ApiErrorAlert error={toast.error} />}
        </div>
      ) : null}
    </div>
  );
};

const StatCard: React.FC<{ label: string; value: string; unit: string }> = ({ label, value, unit }) => (
  <div className="rounded-xl border border-white/8 bg-elevated/40 p-4">
    <p className="mb-1 text-xs text-muted">{label}</p>
    <p className="text-2xl font-semibold text-white">{value}</p>
    <p className="text-xs text-secondary">{unit}</p>
  </div>
);

export default SettingsPage;
