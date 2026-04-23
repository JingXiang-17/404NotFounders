import uuid

from app.schemas.analysis import LandedCostResult
from app.services.recommendation_engine_service import rank_quotes


def test_rank_quotes():
    quote_id_1 = str(uuid.uuid4())
    quote_id_2 = str(uuid.uuid4())
    quote_id_3 = str(uuid.uuid4())

    cost_1 = LandedCostResult(
        quote_id=quote_id_1,
        material_cost_myr_p10=0.0,
        material_cost_myr_p50=0.0,
        material_cost_myr_p90=0.0,
        freight_cost_myr=0.0,
        tariff_cost_myr=0.0,
        moq_penalty=0.0,
        trust_penalty=0.0,
        total_landed_p10=1000.0,
        total_landed_p50=1200.0,
        total_landed_p90=1500.0,
    )

    cost_2 = LandedCostResult(
        quote_id=quote_id_2,
        material_cost_myr_p10=0.0,
        material_cost_myr_p50=0.0,
        material_cost_myr_p90=0.0,
        freight_cost_myr=0.0,
        tariff_cost_myr=0.0,
        moq_penalty=0.0,
        trust_penalty=0.0,
        total_landed_p10=1000.0,
        total_landed_p50=1100.0,
        total_landed_p90=1400.0,
    )

    # Cost 3 has same p50 as Cost 2, but worse p90
    cost_3 = LandedCostResult(
        quote_id=quote_id_3,
        material_cost_myr_p10=0.0,
        material_cost_myr_p50=0.0,
        material_cost_myr_p90=0.0,
        freight_cost_myr=0.0,
        tariff_cost_myr=0.0,
        moq_penalty=0.0,
        trust_penalty=0.0,
        total_landed_p10=1000.0,
        total_landed_p50=1100.0,
        total_landed_p90=1450.0,
    )

    costs = [cost_1, cost_2, cost_3]
    ranked = rank_quotes(costs)

    assert len(ranked) == 3

    # Cost 2 should be first
    assert ranked[0].cost_result.quote_id == quote_id_2
    assert ranked[0].rank == 1
    assert ranked[0].delta_vs_winner == 0.0

    # Cost 3 should be second (tiebreaker on p90)
    assert ranked[1].cost_result.quote_id == quote_id_3
    assert ranked[1].rank == 2
    assert ranked[1].delta_vs_winner == 0.0

    # Cost 1 should be third
    assert ranked[2].cost_result.quote_id == quote_id_1
    assert ranked[2].rank == 3
    assert ranked[2].delta_vs_winner == 100.0  # 1200 - 1100
