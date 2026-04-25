import json
import logging
from typing import Any, AsyncGenerator, Callable, Dict, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage

try:
    from langgraph.graph import END, StateGraph
except ImportError:
    StateGraph = None
    END = None

from app.providers.llm_provider import build_llm_provider

logger = logging.getLogger(__name__)

COMPARISON_SYSTEM_PROMPT = """You are LintasNiaga's procurement analyst. You have been given ranked supplier quotes with full cost breakdowns, FX simulation results, PP resin benchmark context, and market context. Your job is to:
1. Confirm or adjust the winner (you may only swap rank #1 and #2, and only for: reliability, downside risk, MOQ lock-up, urgency mismatch, or disruption risk)
2. Recommend timing: lock_now or wait
3. Recommend hedge ratio (0-100)
4. Give top 3 reasons for your recommendation in plain SME language, explicitly connecting the decision to the fan chart, strongest risk drivers, and any relevant news or market snapshots in the context
5. Add one caveat only if there is a material risk
6. Explain why each non-winning supplier was not chosen (one sentence each)
7. Provide a brief impact summary that says what happened, why it matters, and what the SME should do next.
If the 30-day landed-cost Monte Carlo p50 path trends lower and urgency allows, timing can be "wait" with a reason such as wait/requote/order later. If the path trends higher or P90 tail risk is high, prefer "lock_now" and a higher hedge ratio.
Treat PP resin as a market benchmark only, not a Monte Carlo price driver. Use resin_benchmark and market_price_risks to tell the SME whether each supplier quote is below market, fair, premium, or suspiciously high/low. If a quote is far below benchmark, warn about validity, quality/spec mismatch, hidden fees, or bait pricing instead of treating it as automatically good. Do not change deterministic rank purely because of the resin benchmark unless the bounded swap rule is justified by reliability, downside risk, MOQ lock-up, urgency mismatch, or disruption risk.
Use the P90-P50 spread as the risk budget: if the SME can tolerate that RM downside amount, advice can be neutral/monitor; if not, recommend hedge, lock, or stage the order. Do not invent news; only mention news/events present in the provided context.
Return ONLY a valid JSON object. Do not include markdown, prose, code fences, or thinking text. Match this schema:
{
  "recommended_quote_id": "uuid",
  "timing": "lock_now | wait",
  "hedge_ratio": 70,
  "top_3_reasons": ["reason1", "reason2", "reason3"],
  "caveat": "caveat or null",
  "backup_quote_id": "uuid",
  "backup_rationale": "reason",
  "why_not_others": {"uuid1": "reason", "uuid2": "reason"},
  "impact_summary": "summary"
}
"""

SINGLE_QUOTE_SYSTEM_PROMPT = """You are LintasNiaga's procurement analyst. You are evaluating a single supplier quote, not comparing multiple suppliers. Use PP resin benchmark context when judging whether the material price is fair, premium, suspiciously low, or high risk.
Your job is to:
1. Evaluate the quote as proceed, review_carefully, or do_not_recommend
2. Recommend timing: lock_now or wait
3. Recommend hedge ratio (0-100)
4. Give top 3 reasons for your recommendation in plain SME language, explicitly connecting the decision to the fan chart, strongest risk drivers, and any relevant news or market snapshots in the context
5. Add one caveat only if there is a material risk
6. Explain the main downside risk in one sentence
7. Provide a brief impact summary that says what happened, why it matters, and what the SME should do next.
If the 30-day landed-cost Monte Carlo p50 path trends lower and urgency allows, timing can be "wait" with a reason such as wait/requote/order later. If the path trends higher or P90 tail risk is high, prefer "lock_now" and a higher hedge ratio.
Treat PP resin as a market benchmark only, not a Monte Carlo price driver. Use resin_benchmark and market_price_risks to explain whether the quoted material price is below market, fair, premium, or suspiciously high/low. If it is far below benchmark, tell the SME to verify grade/spec, quote validity, hidden charges, and supplier credibility instead of blindly accepting it.
Use the P90-P50 spread as the risk budget: if the SME can tolerate that RM downside amount, advice can be neutral/monitor; if not, recommend hedge, lock, or stage the order. Do not invent news; only mention news/events present in the provided context.
Return ONLY a valid JSON object. Do not include markdown, prose, code fences, or thinking text. Match this schema:
{
  "recommended_quote_id": "uuid",
  "evaluation_label": "proceed | review_carefully | do_not_recommend",
  "timing": "lock_now | wait",
  "hedge_ratio": 50,
  "top_3_reasons": ["reason1", "reason2", "reason3"],
  "caveat": "caveat or null",
  "backup_quote_id": null,
  "backup_rationale": null,
  "why_not_others": {},
  "impact_summary": "summary"
}
"""


class OrchestratorState(TypedDict):
    context_str: str
    system_prompt: str
    ai_json_output: Dict[str, Any]
    messages: list[Any]
    trace_url: str | None


async def node_reason_recommendation(state: OrchestratorState) -> OrchestratorState:
    logger.info("Executing AI reasoning node")
    provider = build_llm_provider()
    
    messages = [
        SystemMessage(content=state["system_prompt"]),
        HumanMessage(content=state["context_str"]),
    ]
    
    # LLMProvider sets up the Langfuse callback implicitly.
    # No try/except — failures must surface to the caller.
    callbacks = provider._callbacks()
    response = provider.client.invoke(
        messages,
        config={"callbacks": callbacks},
    )
    content = response.content if isinstance(response.content, str) else str(response.content)
    parsed_json = provider._clean_json(content)
    state["ai_json_output"] = parsed_json
    state["trace_url"] = provider.trace_url_from_callbacks(callbacks)
    return state


def build_ai_graph() -> Any:
    if StateGraph is None:
        raise RuntimeError("langgraph is not installed")
        
    workflow = StateGraph(OrchestratorState)
    workflow.add_node("reason_recommendation", node_reason_recommendation)
    workflow.set_entry_point("reason_recommendation")
    workflow.add_edge("reason_recommendation", END)
    
    return workflow.compile()


def get_reasoning_system_prompt(*, single_quote_mode: bool) -> str:
    return SINGLE_QUOTE_SYSTEM_PROMPT if single_quote_mode else COMPARISON_SYSTEM_PROMPT


async def stream_analyst_explanation(
    context_str: str,
    *,
    on_trace_url: Callable[[str], None] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream the explanation for the SSE endpoint.
    Returns markdown explanation.
    """
    provider = build_llm_provider()
    messages = [
        SystemMessage(content="You are LintasNiaga's procurement analyst. Summarize the procurement recommendation based on the context in 2-3 clear paragraphs for the user."),
        HumanMessage(content=context_str),
    ]
    
    try:
        callbacks = provider._callbacks()
        async for chunk in provider.client.astream(
            messages,
            config={
                "callbacks": callbacks,
                "run_name": "lintasniaga-streamed-analyst-explanation",
                "metadata": {"langfuse_tags": ["stream", "analyst-explanation", "lintasniaga"]},
            },
        ):
            reasoning = chunk.additional_kwargs.get("reasoning_content", "")
            if reasoning:
                pass
                
            content = chunk.content
            if content:
                yield content
        trace_url = provider.trace_url_from_callbacks(callbacks)
        if trace_url and on_trace_url:
            on_trace_url(trace_url)
    except Exception as exc:
        logger.error(f"Streaming failed: {exc}")
        import json as _json
        yield f"data: {_json.dumps({'error': True, 'message': str(exc), 'type': 'langfuse_stream_error'})}\n\n"
        raise
