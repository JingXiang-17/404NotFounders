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
      <AccordionItem value="breakdown" className="border-b-0 border-outline-variant">
        <AccordionTrigger className="py-2 text-sm text-secondary hover:text-on-background hover:no-underline font-medium">
          View Cost Breakdown
        </AccordionTrigger>
        <AccordionContent className="pt-2 pb-4 space-y-2">
          <div className="flex justify-between text-[13px]">
            <span className="text-secondary">Material Cost (p50)</span>
            <span className="font-data-mono font-medium text-on-background">{formatCurrency(cost.material_cost_myr_p50)}</span>
          </div>
          <div className="flex justify-between text-[13px]">
            <span className="text-secondary">Freight Estimate</span>
            <span className="font-data-mono font-medium text-on-background">{formatCurrency(cost.freight_cost_myr)}</span>
          </div>
          <div className="flex justify-between text-[13px]">
            <span className="text-secondary">Import Tariff</span>
            <span className="font-data-mono font-medium text-on-background">{formatCurrency(cost.tariff_cost_myr)}</span>
          </div>
          {cost.moq_penalty > 0 && (
            <div className="flex justify-between text-[13px]">
              <span className="text-[#b07d00]">MOQ Dead-Stock Penalty</span>
              <span className="font-data-mono font-medium text-[#b07d00]">+{formatCurrency(cost.moq_penalty)}</span>
            </div>
          )}
          {cost.trust_penalty > 0 && (
            <div className="flex justify-between text-[13px]">
              <span className="text-[#ba1a1a]">Trust Risk Penalty</span>
              <span className="font-data-mono font-medium text-[#ba1a1a]">+{formatCurrency(cost.trust_penalty)}</span>
            </div>
          )}
          <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 text-[13px] font-bold">
            <span className="text-on-background">Total Landed (p50)</span>
            <span className="font-data-mono text-[#004aad] text-sm">{formatCurrency(cost.total_landed_p50)}</span>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
