"use client";

import { Area, AreaChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { FxSimulationResult, HedgeScenarioResult, LandedCostScenario, ResinPriceScenario } from "@/lib/types";

interface FxFanChartProps {
  data: FxSimulationResult | ResinPriceScenario | LandedCostScenario | HedgeScenarioResult;
  valuePrefix?: string;
}

interface ChartDatum {
  day: number;
  p10: number;
  p50: number;
  p90: number;
  p10ToP50: [number, number];
  p50ToP90: [number, number];
}

function formatChartValue(valuePrefix: string, value: number) {
  return `${valuePrefix}${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function FanTooltip({
  active,
  label,
  payload,
  valuePrefix,
}: {
  active?: boolean;
  label?: string | number;
  payload?: Array<{ payload?: ChartDatum }>;
  valuePrefix: string;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const point = payload[0]?.payload as ChartDatum | undefined;
  if (!point) {
    return null;
  }

  return (
    <div className="rounded border border-outline-variant bg-white px-3 py-2 font-data-mono text-sm shadow-[0_4px_6px_rgba(0,0,0,0.1)] z-50">
      <div className="mb-2 text-secondary font-sans font-semibold">Day {label}</div>
      <div className="text-[#ba1a1a]">p90 : {formatChartValue(valuePrefix, point.p90)}</div>
      <div className="mt-1 text-[#004aad]">p50 : {formatChartValue(valuePrefix, point.p50)}</div>
      <div className="mt-1 text-[#00f5d4]">p10 : {formatChartValue(valuePrefix, point.p10)}</div>
    </div>
  );
}

export function FxFanChart({ data, valuePrefix = "" }: FxFanChartProps) {
  // Range bands keep the fan inside p10-p90 instead of filling down to the axis baseline.
  const pointCount = Math.min(
    data.p10_envelope.length,
    data.p50_envelope.length,
    data.p90_envelope.length,
  );
  const chartData: ChartDatum[] = Array.from({ length: pointCount }, (_, i) => ({
    day: i,
    p10: data.p10_envelope[i],
    p50: data.p50_envelope[i],
    p90: data.p90_envelope[i],
    p10ToP50: [data.p10_envelope[i], data.p50_envelope[i]],
    p50ToP90: [data.p50_envelope[i], data.p90_envelope[i]],
  }));

  return (
    <div className="mt-4 h-[320px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 12, right: 24, left: 18, bottom: 8 }}>
          <XAxis 
            dataKey="day" 
            stroke="#cbd5e1" 
            tick={{ fill: "#64748b", fontSize: 11, fontFamily: "Inter" }}
            tickFormatter={(val) => `D${val}`}
          />
          <YAxis 
            domain={['auto', 'auto']} 
            stroke="#cbd5e1" 
            tick={{ fill: "#64748b", fontSize: 11, fontFamily: "Inter" }}
            tickFormatter={(value) =>
              Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })
            }
            width={86}
          />
          <Tooltip content={<FanTooltip valuePrefix={valuePrefix} />} />
          <Area 
            type="monotone" 
            dataKey="p50ToP90" 
            stroke="none" 
            fill="#ff6b6b" 
            fillOpacity={0.15} 
            isAnimationActive={false}
          />
          <Area 
            type="monotone" 
            dataKey="p10ToP50" 
            stroke="none"
            fill="#004aad" 
            fillOpacity={0.15} 
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="p90"
            stroke="rgba(255, 107, 107, 0.7)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="p50"
            stroke="#004aad"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="p10" 
            stroke="rgba(0, 245, 212, 0.7)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
