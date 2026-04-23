"use client";

import { Slider } from "@/components/ui/slider";

interface HedgeSliderProps {
  hedgeRatio: number;
  onHedgeChange: (value: number) => void;
  expectedLandedCost: number;
}

export function HedgeSlider({ hedgeRatio, onHedgeChange, expectedLandedCost }: HedgeSliderProps) {
  return (
    <div className="mt-6 rounded-lg border border-border bg-[var(--color-surface-elevated)] p-4">
      <div className="flex justify-between items-center mb-4">
        <label className="text-sm font-bold text-foreground">Hedge Ratio</label>
        <span className="font-mono font-medium text-primary">{hedgeRatio}%</span>
      </div>
      
      <Slider
        value={[hedgeRatio]}
        max={100}
        step={1}
        onValueChange={(vals) => onHedgeChange(Array.isArray(vals) ? vals[0] : (vals as number))}
        className="mb-4"
      />
      
      <div className="text-center text-[13px] text-secondary-text">
        At {hedgeRatio}% hedge: expected landed cost{" "}
        <span className="font-mono font-medium text-foreground">RM {expectedLandedCost.toLocaleString()}/MT</span> (p50)
      </div>
    </div>
  );
}
