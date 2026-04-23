"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { LandedCostResult } from "@/lib/types";

interface CostBreakdownProps {
  cost: LandedCostResult;
}

export function CostBreakdown({ cost }: CostBreakdownProps) {
  const formatCurrency = (val: number) => `RM ${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

  return (
    <Accordion className="w-full">
      <AccordionItem value="breakdown" className="border-b-0 border-border">
        <AccordionTrigger className="py-2 text-sm text-secondary-text hover:text-foreground hover:no-underline">
          View Cost Breakdown
        </AccordionTrigger>
        <AccordionContent className="pt-2 pb-4 space-y-2">
          <div className="flex justify-between text-[13px]">
            <span className="text-secondary-text">Material Cost (p50)</span>
            <span className="font-mono text-foreground">{formatCurrency(cost.material_cost_myr_p50)}</span>
          </div>
          <div className="flex justify-between text-[13px]">
            <span className="text-secondary-text">Freight Estimate</span>
            <span className="font-mono text-foreground">{formatCurrency(cost.freight_cost_myr)}</span>
          </div>
          <div className="flex justify-between text-[13px]">
            <span className="text-secondary-text">Import Tariff</span>
            <span className="font-mono text-foreground">{formatCurrency(cost.tariff_cost_myr)}</span>
          </div>
          {cost.moq_penalty > 0 && (
            <div className="flex justify-between text-[13px]">
              <span className="text-[var(--color-warning)]">MOQ Dead-Stock Penalty</span>
              <span className="font-mono text-[var(--color-warning)]">+{formatCurrency(cost.moq_penalty)}</span>
            </div>
          )}
          {cost.trust_penalty > 0 && (
            <div className="flex justify-between text-[13px]">
              <span className="text-[var(--color-warning)]">Trust Risk Penalty</span>
              <span className="font-mono text-[var(--color-warning)]">+{formatCurrency(cost.trust_penalty)}</span>
            </div>
          )}
          <div className="mt-2 flex justify-between border-t border-border pt-2 text-[13px] font-bold">
            <span className="text-foreground">Total Landed (p50)</span>
            <span className="font-mono text-primary">{formatCurrency(cost.total_landed_p50)}</span>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
