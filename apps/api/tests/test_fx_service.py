from app.schemas.common import SnapshotEnvelope
from app.services.fx_service import simulate_fx_paths


class FakeSnapshotRepository:
    def __init__(self) -> None:
        self.lookups = []

    def read_latest(self, dataset: str):
        self.lookups.append(dataset)
        if dataset == "fx/USDMYR":
            return SnapshotEnvelope(
                dataset="fx/USDMYR",
                source="yfinance",
                fetched_at="2026-04-23T10:00:00Z",
                as_of="2026-04-22",
                status="success",
                record_count=4,
                data=[
                    {"date": "2026-04-19", "close": 4.70},
                    {"date": "2026-04-20", "close": 4.72},
                    {"date": "2026-04-21", "close": 4.71},
                    {"date": "2026-04-22", "close": 4.73},
                ],
            )
        return None


def test_simulate_fx_paths_reads_current_snapshot_dataset():
    repository = FakeSnapshotRepository()

    result = simulate_fx_paths(pair="USDMYR", snapshot_repository=repository, n_paths=5, horizon_days=3)

    assert result.pair == "USDMYR"
    assert repository.lookups[0] == "fx/USDMYR"
    assert len(result.p50_envelope) == 3
