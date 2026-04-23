from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import LandedCostResult, RankedQuote, RecommendationCard


def test_analysis_run_route_accepts_quote_ids(monkeypatch):
    async def fake_run_analysis(quote_ids, quantity_mt, urgency, hedge_preference):
        assert quote_ids == ["quote-1", "quote-2"]
        assert quantity_mt == 100
        assert urgency == "normal"
        assert hedge_preference == "balance"
        return (
            "run-123",
            RecommendationCard(
                recommended_quote_id="quote-1",
                expected_landed_cost_myr=123456.0,
                confidence_score=0.95,
                backup_options=[],
                timing="lock_now",
                hedge_pct=60.0,
                reasons=["Lowest p50 landed cost"],
                caveat=None,
                why_not_others={"quote-2": "Higher landed cost"},
                impact_summary="Test summary",
            ),
        )

    monkeypatch.setattr("app.api.routes.analysis.run_analysis_service", fake_run_analysis)

    client = TestClient(app)
    response = client.post(
        "/analysis/run",
        json={
            "quote_ids": ["quote-1", "quote-2"],
            "quantity_mt": 100,
            "urgency": "normal",
            "hedge_preference": "balance",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-123"
    assert payload["recommendation"]["recommended_quote_id"] == "quote-1"


def test_hedge_simulate_uses_stored_run_result(monkeypatch):
    ranked_quotes = [
        RankedQuote(
            rank=1,
            delta_vs_winner=0.0,
            cost_result=LandedCostResult(
                quote_id="quote-1",
                material_cost_myr_p10=100.0,
                material_cost_myr_p50=110.0,
                material_cost_myr_p90=120.0,
                freight_cost_myr=10.0,
                tariff_cost_myr=5.0,
                moq_penalty=0.0,
                trust_penalty=1.0,
                total_landed_p10=116.0,
                total_landed_p50=126.0,
                total_landed_p90=146.0,
            ),
        )
    ]

    monkeypatch.setattr(
        "app.api.routes.analysis.get_result_for_run",
        lambda run_id: {"ranked_quotes": ranked_quotes},
    )

    client = TestClient(app)
    response = client.post("/analysis/run-123/hedge-simulate", json={"hedge_ratio": 50})

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "hedge_ratio": 50.0,
        "adjusted_p50": 126.0,
        "adjusted_p90": 136.0,
        "impact_vs_unhedged": 10.0,
    }
