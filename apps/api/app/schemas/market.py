from datetime import date

from pydantic import BaseModel


class SnapshotRefreshSummary(BaseModel):
    dataset: str
    source: str
    fetched_at: str
    as_of: str | None
    status: str
    record_count: int


class FXSnapshotRecord(BaseModel):
    pair: str
    date: date
    open: float
    high: float
    low: float
    close: float


class EnergySnapshotRecord(BaseModel):
    symbol: str
    series_name: str
    date: date
    open: float
    high: float
    low: float
    close: float
