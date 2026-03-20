import React from 'react';
import type { AnalysisResult, AnalysisReport, InstitutionalData } from '../../types/analysis';
import { ReportOverview } from './ReportOverview';
import { ReportStrategy } from './ReportStrategy';
import { ReportNews } from './ReportNews';
import { ReportDetails } from './ReportDetails';
import { ReportInstitutional } from './ReportInstitutional';

interface ReportSummaryProps {
  data: AnalysisResult | AnalysisReport;
  isHistory?: boolean;
}

/**
 * 從 contextSnapshot 中提取三大法人資料
 * 路徑：contextSnapshot.enhanced_context.institutional
 */
function extractInstitutional(details?: AnalysisReport['details']): InstitutionalData | undefined {
  try {
    const snap = details?.contextSnapshot as Record<string, unknown> | undefined;
    // API 回傳經 toCamelCase 轉換，key 已是 camelCase
    const enhanced = (snap?.enhancedContext ?? snap?.enhanced_context) as Record<string, unknown> | undefined;
    const inst = enhanced?.institutional as Record<string, unknown> | undefined;
    if (!inst || !inst.rows) return undefined;
    return {
      date: String(inst.date ?? ''),
      rows: (inst.rows as Array<Record<string, unknown>>).map(r => ({
        name: String(r.name ?? ''),
        buy: Number(r.buy ?? 0),
        sell: Number(r.sell ?? 0),
        diff: Number(r.diff ?? 0),
      })),
      totalDiff: Number(inst.totalDiff ?? inst.total_diff ?? 0),
      summary: String(inst.summary ?? ''),
    };
  } catch {
    return undefined;
  }
}

/**
 * 完整报告展示组件
 * 整合概览、策略、三大法人、资讯、详情五个区域
 */
export const ReportSummary: React.FC<ReportSummaryProps> = ({
  data,
  isHistory = false,
}) => {
  // 兼容 AnalysisResult 和 AnalysisReport 两种数据格式
  const report: AnalysisReport = 'report' in data ? data.report : data;
  // 使用 report id，因为 queryId 在批量分析时可能重复，且历史报告详情接口需要 recordId 来获取关联资讯和详情数据
  const recordId = report.meta.id;

  const { meta, summary, strategy, details } = report;
  const modelUsed = (meta.modelUsed || '').trim();
  const shouldShowModel = Boolean(
    modelUsed && !['unknown', 'error', 'none', 'null', 'n/a'].includes(modelUsed.toLowerCase()),
  );

  const institutional = extractInstitutional(details);

  return (
    <div className="space-y-3 animate-fade-in">
      {/* 概览区（首屏） */}
      <ReportOverview
        meta={meta}
        summary={summary}
        isHistory={isHistory}
      />

      {/* 策略点位区 */}
      <ReportStrategy strategy={strategy} />

      {/* 三大法人買賣超（台股限定，有資料才顯示） */}
      <ReportInstitutional institutional={institutional} />

      {/* 资讯区 */}
      <ReportNews recordId={recordId} stockCode={meta.stockCode} stockName={meta.stockName} />

      {/* 透明度与追溯区 */}
      <ReportDetails details={details} recordId={recordId} />

      {/* 分析模型标记（Issue #528）— 报告末尾 */}
      {shouldShowModel && (
        <p className="text-xs text-gray-500 mt-3">
          分析模型: {modelUsed}
        </p>
      )}
    </div>
  );
};
