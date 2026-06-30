"use client";

import { useMemo } from "react";
import type { TrendHistoryPoint } from "@/lib/types";

interface TrendChartProps {
  history: TrendHistoryPoint[];
  width?: number;
  height?: number;
}

/** Lightweight SVG sparkline chart for 7-day hot trend */
export function TrendChart({ history, width = 580, height = 240 }: TrendChartProps) {
  const sorted = useMemo(
    () => [...history].sort((a, b) => new Date(a.snapshot_at).getTime() - new Date(b.snapshot_at).getTime()),
    [history],
  );

  const padding = { top: 24, bottom: 36, left: 48, right: 24 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const values = sorted.map((h) => h.hot_value_norm);
  const maxVal = Math.max(...values, 1);
  const minVal = Math.min(...values);
  const range = maxVal - minVal || 1;

  const points = sorted.map((h, i) => ({
    x: padding.left + (i / Math.max(sorted.length - 1, 1)) * chartW,
    y: padding.top + chartH - ((h.hot_value_norm - minVal) / range) * chartH,
    ...h,
  }));

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");

  const areaPath = points.length > 1
    ? `${linePath} L${points[points.length - 1].x},${padding.top + chartH} L${points[0].x},${padding.top + chartH} Z`
    : "";

  // X-axis labels
  const xLabels = useMemo(() => {
    if (sorted.length <= 1) return [];
    const step = Math.max(1, Math.floor(sorted.length / 6));
    return sorted.filter((_, i) => i % step === 0 || i === sorted.length - 1);
  }, [sorted]);

  return (
    <div style={{ width: "100%", overflow: "hidden" }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: "block" }}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + chartH * (1 - ratio);
          return (
            <g key={ratio}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y}
                stroke="#f0f0f0" strokeWidth={1} />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fill="#999" fontSize={11}>
                {(minVal + range * ratio).toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Area fill */}
        {areaPath && (
          <path d={areaPath} fill="rgba(245, 34, 45, 0.08)" />
        )}

        {/* Line */}
        <path d={linePath} fill="none" stroke="#f5222d" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

        {/* Data dots */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={3} fill="#fff" stroke="#f5222d" strokeWidth={2}>
            <title>{`${p.hot_value}\n${new Date(p.snapshot_at).toLocaleDateString("zh-CN")}`}</title>
          </circle>
        ))}

        {/* X-axis labels */}
        {xLabels.map((h, i) => {
          const idx = sorted.indexOf(h);
          const x = padding.left + (idx / Math.max(sorted.length - 1, 1)) * chartW;
          return (
            <text key={i} x={x} y={height - 8} textAnchor="middle" fill="#999" fontSize={11}>
              {new Date(h.snapshot_at).toLocaleDateString("zh-CN", { month: "short", day: "numeric" })}
            </text>
          );
        })}

        {/* Y-axis label */}
        <text x={12} y={padding.top + chartH / 2} textAnchor="middle" fill="#bbb" fontSize={11}
          transform={`rotate(-90, 12, ${padding.top + chartH / 2})`}>
          热度值
        </text>
      </svg>
    </div>
  );
}
