from typing import Any, Dict, List, Optional

from app.schemas.analysis import LandedCostResult, RankedQuote


def build_ai_context(
    ranked_quotes: List[RankedQuote],
    costs: List[LandedCostResult],
    fx_sims: Dict[str, Any],
    macro_snapshot: Optional[Dict[str, Any]],
    urgency: str,
    hedge_preference: str,
) -> str:
    """
    Assemble a structured text context for the AI reasoning model.
    Includes ranked results, cost breakdowns, FX summary, urgency, and hedge preference.
    """
    context_lines = [
        "# Procurement Analysis Context",
        f"**Urgency Level:** {urgency}",
        f"**Hedge Preference:** {hedge_preference}",
        "\n## FX Simulation Summary",
    ]

    for pair, sim in fx_sims.items():
        # sim could be FxSimulationResult or a dict representation
        if hasattr(sim, "current_spot"):
            context_lines.append(
                f"- Pair: {sim.pair} | Current Spot: {sim.current_spot:.4f} | Implied Volatility: {sim.implied_vol:.2%}"
            )
        else:
            context_lines.append(
                f"- Pair: {sim.get('pair', pair)} | Current Spot: {sim.get('current_spot', 0):.4f} | Implied Volatility: {sim.get('implied_vol', 0):.2%}"
            )

    context_lines.append("\n## Ranked Quotes (Deterministic Engine)")
    
    # Map quote_id to cost details
    cost_map = {c.quote_id: c for c in costs}

    for ranked in ranked_quotes:
        cost = cost_map[ranked.cost_result.quote_id]
        context_lines.append(f"### Rank {ranked.rank}: Quote {cost.quote_id}")
        context_lines.append(f"- Delta vs Winner: RM {ranked.delta_vs_winner:,.2f}")
        context_lines.append(f"- Landed Cost (P50 expected): RM {cost.total_landed_p50:,.2f}")
        context_lines.append(f"- Landed Cost (P90 worst-case): RM {cost.total_landed_p90:,.2f}")
        context_lines.append(f"- Cost Breakdown (P50):")
        context_lines.append(f"  - Material: RM {cost.material_cost_myr_p50:,.2f}")
        context_lines.append(f"  - Freight: RM {cost.freight_cost_myr:,.2f}")
        context_lines.append(f"  - Tariff: RM {cost.tariff_cost_myr:,.2f}")
        context_lines.append(f"  - MOQ Penalty: RM {cost.moq_penalty:,.2f}")
        context_lines.append(f"  - Supplier Risk Penalty: RM {cost.trust_penalty:,.2f}")

    if macro_snapshot:
        context_lines.append("\n## Macro Context")
        context_lines.append(str(macro_snapshot))

    return "\n".join(context_lines)
