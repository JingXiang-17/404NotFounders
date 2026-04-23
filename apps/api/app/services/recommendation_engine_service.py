from typing import List

from app.schemas.analysis import LandedCostResult, RankedQuote


def rank_quotes(costs: List[LandedCostResult]) -> List[RankedQuote]:
    """
    Rank quotes based on total landed cost.
    Primary sort: total_landed_p50 ascending
    Secondary sort: total_landed_p90 ascending (tiebreaker)
    """
    if not costs:
        return []

    # Sort costs by p50, then p90
    sorted_costs = sorted(costs, key=lambda c: (c.total_landed_p50, c.total_landed_p90))
    
    winner_p50 = sorted_costs[0].total_landed_p50
    
    ranked_quotes = []
    for index, cost in enumerate(sorted_costs):
        rank = index + 1
        delta_vs_winner = cost.total_landed_p50 - winner_p50
        ranked_quotes.append(
            RankedQuote(
                rank=rank,
                delta_vs_winner=delta_vs_winner,
                cost_result=cost,
            )
        )
        
    return ranked_quotes
