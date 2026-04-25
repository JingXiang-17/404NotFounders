"use client";

import { Slider } from "@/components/ui/slider";

interface HedgeSliderProps {
  hedgeRatio: number;
  onHedgeChange: (value: number) => void;
  expectedLandedCost: number;
  className?: string;
}

export function HedgeSlider({ hedgeRatio, onHedgeChange, expectedLandedCost, className = "" }: HedgeSliderProps) {
  return (
    <div className={`rounded-lg border border-outline-variant bg-surface-container-lowest p-4 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <label className="text-sm font-bold text-on-background uppercase tracking-widest text-label-caps">Hedge Ratio</label>
        <span className="font-data-mono font-bold text-[#004aad] text-lg">{hedgeRatio}%</span>
      </div>
      
      <Slider
        value={[hedgeRatio]}
        max={100}
        step={1}
        onValueChange={(vals) => onHedgeChange(Array.isArray(vals) ? vals[0] : (vals as number))}
        className="mb-4 [&_[data-slot=slider-range]]:bg-[#004aad] [&_[data-slot=slider-thumb]]:size-4 [&_[data-slot=slider-thumb]]:border-[#004aad] [&_[data-slot=slider-thumb]]:bg-white [&_[data-slot=slider-track]]:h-1.5 [&_[data-slot=slider-track]]:bg-slate-200"
      />
      
      <div className="text-center text-[13px] text-secondary">
        At <span className="font-semibold text-[#004aad]">{hedgeRatio}%</span> hedge: expected landed cost{" "}
        <span className="font-data-mono font-medium text-on-background">RM {expectedLandedCost.toLocaleString()}</span> (p50)
      </div>
    </div>
  );
}
