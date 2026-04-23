from typing import Any, Dict, List

from app.schemas.analysis import BackupOption, RankedQuote, RecommendationCard


def _default_comparison_reasons(ranked_quotes: List[RankedQuote]) -> List[str]:
    winner = ranked_quotes[0]
    reasons = [
        f"Lowest expected landed cost at RM {winner.cost_result.total_landed_p50:,.2f}.",
        f"Downside case remains bounded at RM {winner.cost_result.total_landed_p90:,.2f}.",
    ]
    if len(ranked_quotes) > 1:
        delta = ranked_quotes[1].cost_result.total_landed_p50 - winner.cost_result.total_landed_p50
        reasons.append(f"Maintains a RM {delta:,.2f} advantage over the next-best option.")
    else:
        reasons.append("Only one valid quote is available for comparison.")
    return reasons


def _default_single_quote_reasons(ranked_quote: RankedQuote) -> List[str]:
    cost = ranked_quote.cost_result
    spread = cost.total_landed_p90 - cost.total_landed_p50
    reasons = [
        f"Expected landed cost is RM {cost.total_landed_p50:,.2f}.",
        f"Stress-case downside is RM {cost.total_landed_p90:,.2f}, a spread of RM {spread:,.2f}.",
    ]
    if cost.moq_penalty > 0:
        reasons.append(f"MOQ lock-up adds RM {cost.moq_penalty:,.2f} of dead-stock risk.")
    elif cost.trust_penalty > 0:
        reasons.append(f"Supplier risk adds RM {cost.trust_penalty:,.2f} to the landed-cost view.")
    else:
        reasons.append("No major MOQ lock-up penalty is present in the deterministic view.")
    return reasons


def _derive_single_quote_label(ranked_quote: RankedQuote) -> str:
    cost = ranked_quote.cost_result
    downside_ratio = 0.0
    if cost.total_landed_p50 > 0:
        downside_ratio = (cost.total_landed_p90 - cost.total_landed_p50) / cost.total_landed_p50
    if cost.moq_penalty > 0 or cost.trust_penalty > cost.total_landed_p50 * 0.03:
        return "do_not_recommend"
    if downside_ratio > 0.08:
        return "review_carefully"
    return "proceed"


def assemble_recommendation(
    ranked_quotes: List[RankedQuote],
    ai_json: Dict[str, Any],
    single_quote_mode: bool = False
) -> RecommendationCard:
    """
    Assemble the final recommendation card from deterministic ranks and AI bounds.
    """
    if not ranked_quotes:
        raise ValueError("Cannot assemble recommendation with empty quote list.")

    deterministic_winner = ranked_quotes[0]
    
    # Extract AI fields
    recommended_quote_id = ai_json.get("recommended_quote_id", deterministic_winner.cost_result.quote_id)
    timing = ai_json.get("timing", "wait")
    hedge_pct = float(ai_json.get("hedge_ratio", 50.0))
    reasons = ai_json.get("top_3_reasons", [])
    caveat = ai_json.get("caveat")
    why_not_others = ai_json.get("why_not_others", {})
    impact_summary = ai_json.get("impact_summary")
    evaluation_label = ai_json.get("evaluation_label")
    
    # Guardrails: Model can only pick Rank 1 or Rank 2
    valid_picks = [q.cost_result.quote_id for q in ranked_quotes[:2]]
    if recommended_quote_id not in valid_picks:
        # Fall back to deterministic winner if AI hallucinated or picked Rank 3+
        recommended_quote_id = deterministic_winner.cost_result.quote_id
        
    # Find the chosen quote object
    chosen_quote = next((q for q in ranked_quotes if q.cost_result.quote_id == recommended_quote_id), deterministic_winner)
    
    # Build backup options
    backup_options = []
    if not single_quote_mode and len(ranked_quotes) > 1:
        # Use AI backup if specified, else use the other one from top 2
        backup_id = ai_json.get("backup_quote_id")
        backup_rationale = ai_json.get("backup_rationale", "Strong deterministic alternative.")
        
        # If AI didn't provide a valid backup, use the one that wasn't chosen
        if not backup_id or backup_id not in [q.cost_result.quote_id for q in ranked_quotes]:
            other_top_quotes = [q for q in ranked_quotes[:2] if q.cost_result.quote_id != recommended_quote_id]
            if other_top_quotes:
                backup_id = other_top_quotes[0].cost_result.quote_id
                
        if backup_id:
            backup_quote = next(
                (quote for quote in ranked_quotes if quote.cost_result.quote_id == backup_id),
                None,
            )
            premium_vs_winner = (
                backup_quote.cost_result.total_landed_p50 - chosen_quote.cost_result.total_landed_p50
                if backup_quote
                else 0.0
            )
            backup_options.append(BackupOption(
                quote_id=backup_id,
                reason=backup_rationale,
                premium_vs_winner=premium_vs_winner,
            ))
            
    # Calculate confidence: simple heuristic based on delta vs winner and AI agreement
    confidence = 0.95 if chosen_quote.cost_result.quote_id == deterministic_winner.cost_result.quote_id else 0.85
    if single_quote_mode:
        evaluation_label = evaluation_label or _derive_single_quote_label(chosen_quote)
        reasons = reasons or _default_single_quote_reasons(chosen_quote)
        why_not_others = {}
        impact_summary = impact_summary or (
            f"Single-quote evaluation with expected landed cost RM {chosen_quote.cost_result.total_landed_p50:,.2f}."
        )
    else:
        reasons = reasons or _default_comparison_reasons(ranked_quotes)
        evaluation_label = None
        impact_summary = impact_summary or (
            f"Expected landed cost RM {chosen_quote.cost_result.total_landed_p50:,.2f} with deterministic ranking support."
        )
    
    return RecommendationCard(
        recommended_quote_id=chosen_quote.cost_result.quote_id,
        expected_landed_cost_myr=chosen_quote.cost_result.total_landed_p50,
        confidence_score=confidence,
        backup_options=backup_options,
        mode="single_quote" if single_quote_mode else "comparison",
        evaluation_label=evaluation_label,
        timing=timing,
        hedge_pct=hedge_pct,
        reasons=reasons,
        caveat=caveat,
        why_not_others=why_not_others,
        impact_summary=impact_summary
    )
