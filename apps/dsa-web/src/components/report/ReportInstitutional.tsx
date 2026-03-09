import type React from 'react';
import type { InstitutionalData, InstitutionalRow } from '../../types/analysis';
import { Card } from '../common';

interface ReportInstitutionalProps {
  institutional?: InstitutionalData;
}

/** 格式化股數（萬股） */
function formatShares(val: number): string {
  const abs = Math.abs(val);
  if (abs >= 10000) return `${(val / 10000).toFixed(1)}萬`;
  return val.toLocaleString();
}

/** 買賣超顏色（台股：紅漲綠跌） */
function getDiffColor(diff: number): string {
  if (diff > 0) return 'text-[#ff4d4d]';
  if (diff < 0) return 'text-[#00d46a]';
  return 'text-muted';
}

const ROW_LABELS: Record<string, string> = {
  '外資': '外資',
  '投信': '投信',
  '自營商': '自營商',
  '自營商(避險)': '自營(避險)',
  '外資自營商': '外資自營',
};

/**
 * 三大法人買賣超卡片
 * 資料來源：context_snapshot.enhanced_context.institutional（FinMind）
 */
export const ReportInstitutional: React.FC<ReportInstitutionalProps> = ({ institutional }) => {
  if (!institutional) return null;

  const { date, rows, totalDiff, summary } = institutional;
  const isBuy = totalDiff > 0;
  const isSell = totalDiff < 0;

  // 只顯示主要三大法人（外資、投信、自營商合計）
  const mainRows = rows.filter(r =>
    ['外資', '投信', '自營商'].includes(r.name)
  );
  // 若 mainRows 為空，顯示全部
  const displayRows: InstitutionalRow[] = mainRows.length > 0 ? mainRows : rows;

  return (
    <Card variant="bordered" padding="md">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-baseline gap-2">
          <span className="label-uppercase">INSTITUTIONAL</span>
          <h3 className="text-base font-semibold text-white">三大法人</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted">
          <span>{date}</span>
          <span
            className={`font-semibold px-2 py-0.5 rounded text-xs ${
              isBuy
                ? 'bg-[#ff4d4d]/15 text-[#ff4d4d]'
                : isSell
                ? 'bg-[#00d46a]/15 text-[#00d46a]'
                : 'bg-white/5 text-muted'
            }`}
          >
            {summary} {formatShares(totalDiff)} 股
          </span>
        </div>
      </div>

      {/* 法人明細表 */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left py-2 text-muted font-medium">法人別</th>
              <th className="text-right py-2 text-muted font-medium">買進</th>
              <th className="text-right py-2 text-muted font-medium">賣出</th>
              <th className="text-right py-2 text-muted font-medium">買賣超</th>
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row) => (
              <tr key={row.name} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                <td className="py-2 text-white">
                  {ROW_LABELS[row.name] ?? row.name}
                </td>
                <td className="py-2 text-right font-mono text-secondary">
                  {formatShares(row.buy)}
                </td>
                <td className="py-2 text-right font-mono text-secondary">
                  {formatShares(row.sell)}
                </td>
                <td className={`py-2 text-right font-mono font-semibold ${getDiffColor(row.diff)}`}>
                  {row.diff > 0 ? '+' : ''}{formatShares(row.diff)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td className="pt-2 text-muted font-medium">合計</td>
              <td />
              <td />
              <td className={`pt-2 text-right font-mono font-bold ${getDiffColor(totalDiff)}`}>
                {totalDiff > 0 ? '+' : ''}{formatShares(totalDiff)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* 底部說明 */}
      <p className="text-xs text-muted mt-2">
        資料來源：FinMind（TWSE 官方）
      </p>
    </Card>
  );
};
