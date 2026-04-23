"use client";

import { Area, AreaChart, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { FxSimulationResult } from "@/lib/types";

interface FxFanChartProps {
  data: FxSimulationResult;
}

export function FxFanChart({ data }: FxFanChartProps) {
  // Convert arrays into an array of objects for Recharts
  const chartData = Array.from({ length: data.horizon_days }, (_, i) => ({
    day: i,
    p10: data.p10_envelope[i],
    p50: data.p50_envelope[i],
    p90: data.p90_envelope[i],
  }));

  return (
    <div className="h-[250px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
          <XAxis 
            dataKey="day" 
            stroke="var(--color-border)" 
            tick={{ fill: "var(--color-secondary-text)", fontSize: 11 }}
            tickFormatter={(val) => `D${val}`}
          />
          <YAxis 
            domain={['auto', 'auto']} 
            stroke="var(--color-border)" 
            tick={{ fill: "var(--color-secondary-text)", fontSize: 11 }}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", color: "var(--color-foreground)" }}
            itemStyle={{ color: "var(--color-primary)" }}
            labelStyle={{ color: "var(--color-secondary-text)" }}
          />
          {/* 
            Overlapping areas (NOT stacked).
            The widest envelope (p90) is drawn first, then p50, then p10 (narrowest).
            Note: "p90" here implies higher cost, so it covers a larger area upwards.
            If p10 < p50 < p90, they will overlap correctly.
          */}
          <Area 
            type="monotone" 
            dataKey="p90" 
            stroke="none" 
            fill="var(--color-primary)" 
            fillOpacity={0.15} 
            isAnimationActive={false}
          />
          <Area 
            type="monotone" 
            dataKey="p50" 
            stroke="var(--color-primary)" 
            strokeWidth={2}
            fill="var(--color-primary)" 
            fillOpacity={0.25} 
            isAnimationActive={false}
          />
          <Area 
            type="monotone" 
            dataKey="p10" 
            stroke="none" 
            fill="var(--color-primary)" 
            fillOpacity={0.35} 
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
