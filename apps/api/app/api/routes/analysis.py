from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.exceptions import NoValidQuotes
from app.schemas.analysis import AnalysisResultPayload, HedgeScenarioResult, RecommendationCard
from app.services.ai_orchestrator_service import stream_analyst_explanation
from app.services.analysis_run_service import (
    get_context_for_run,
    get_result_for_run,
    run_analysis as run_analysis_service,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRunRequest(BaseModel):
    quote_ids: List[str]
    quantity_mt: float
    urgency: str
    hedge_preference: str


class AnalysisRunResponse(BaseModel):
    run_id: str
    recommendation: RecommendationCard


@router.post("/run", response_model=AnalysisRunResponse)
async def run_analysis(request: AnalysisRunRequest):
    """
    Executes the full deterministic + AI reasoning pipeline for the given quotes.
    Returns the recommendation card and a run_id for streaming the explanation.
    """
    if not request.quote_ids:
        raise HTTPException(status_code=400, detail="No quotes provided for analysis.")

    try:
        run_id, recommendation = await run_analysis_service(
            quote_ids=request.quote_ids,
            quantity_mt=request.quantity_mt,
            urgency=request.urgency,
            hedge_preference=request.hedge_preference,
        )
    except NoValidQuotes as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No valid quotes — please fix or upload new quotes. {str(exc)}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis could not complete — please try again. {str(exc)}",
        ) from exc
    
    return AnalysisRunResponse(run_id=run_id, recommendation=recommendation)


@router.get("/{run_id}/stream")
async def stream_explanation(run_id: str):
    """
    SSE endpoint to stream the LangGraph AI reasoning explanation.
    """
    context_str = get_context_for_run(run_id)
    if not context_str:
        raise HTTPException(status_code=404, detail="Run ID not found or expired.")
        
    async def event_generator():
        async for chunk in stream_analyst_explanation(context_str):
            # SSE format requires "data: <message>\n\n"
            # We replace newlines with a placeholder or handle them cleanly
            safe_chunk = chunk.replace("\n", "\\n")
            yield f"data: {safe_chunk}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{run_id}", response_model=AnalysisResultPayload)
async def get_analysis_result(run_id: str):
    payload = get_result_for_run(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Run ID not found or expired.")
    return payload


class HedgeSimulateRequest(BaseModel):
    hedge_ratio: float  # 0 to 100


@router.post("/{run_id}/hedge-simulate", response_model=HedgeScenarioResult)
async def hedge_simulate(run_id: str, request: HedgeSimulateRequest):
    """
    Pure math deterministic endpoint to recalculate risk exposure 
    based on the hedge slider value.
    """
    run_payload = get_result_for_run(run_id)
    if run_payload is None:
        raise HTTPException(status_code=404, detail="Run ID not found or expired.")

    ranked_quotes = run_payload.ranked_quotes if hasattr(run_payload, "ranked_quotes") else run_payload.get("ranked_quotes")
    if not ranked_quotes:
        raise HTTPException(status_code=404, detail="No ranked quote data found for this run.")

    winner = ranked_quotes[0]
    p50_cost = winner.cost_result.total_landed_p50
    p90_cost = winner.cost_result.total_landed_p90

    ratio = request.hedge_ratio / 100.0
    
    # Calculate the unhedged downside exposure (difference between p90 and p50)
    downside_risk = p90_cost - p50_cost
    
    # The higher the hedge ratio, the closer we get to p50 certainty.
    # The unhedged portion is exposed to the p90 risk.
    adjusted_p50 = p50_cost
    adjusted_p90 = p50_cost + (downside_risk * (1.0 - ratio))
    
    impact = p90_cost - adjusted_p90
    
    return HedgeScenarioResult(
        hedge_ratio=request.hedge_ratio,
        adjusted_p50=adjusted_p50,
        adjusted_p90=adjusted_p90,
        impact_vs_unhedged=impact
    )
