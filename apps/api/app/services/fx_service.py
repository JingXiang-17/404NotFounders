import logging
import math
from typing import List

import numpy as np

from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.analysis import FxSimulationResult

logger = logging.getLogger(__name__)


def simulate_fx_paths(
    pair: str,
    horizon_days: int = 90,
    n_paths: int = 1000,
    snapshot_repository: SnapshotRepository | None = None,
) -> FxSimulationResult:
    """
    Run geometric Brownian motion simulation for FX rates.
    Loads FX snapshot, calculates daily log returns, estimates volatility,
    and returns projected paths over the horizon.
    """
    if snapshot_repository is None:
        snapshot_repository = SnapshotRepository()

    dataset_candidates = [f"fx/{pair.upper()}", f"market/fx_{pair.lower()}"]
    envelope = None
    dataset_name = dataset_candidates[0]
    for candidate in dataset_candidates:
        envelope = snapshot_repository.read_latest(candidate)
        if envelope and envelope.data:
            dataset_name = candidate
            break

    if not envelope or not envelope.data:
        raise ValueError(f"No snapshot data found for {', '.join(dataset_candidates)}")

    # Ensure data is sorted by date ascending
    records = sorted(envelope.data, key=lambda x: x["date"])
    
    close_prices = [float(record["close"]) for record in records]
    if len(close_prices) < 2:
        raise ValueError(f"Not enough historical data to simulate paths for {dataset_name}")

    current_spot = close_prices[-1]

    # Calculate daily log returns
    closes_arr = np.array(close_prices)
    log_returns = np.diff(np.log(closes_arr))

    # Fit simple historical volatility (using the last 30 days if available)
    window = min(30, len(log_returns))
    recent_log_returns = log_returns[-window:]
    daily_vol = np.std(recent_log_returns)
    implied_vol_annualized = float(daily_vol * np.sqrt(252))

    # Run geometric Brownian motion simulation
    dt = 1.0 / 252.0  # Time step in years (trading days)
    mu = 0.0  # Assuming drift is zero

    # Generate random paths
    # paths shape: (n_paths, horizon_days)
    Z = np.random.normal(0, 1, (n_paths, horizon_days))
    daily_returns_sim = np.exp((mu - 0.5 * implied_vol_annualized**2) * dt + implied_vol_annualized * np.sqrt(dt) * Z)
    
    # Prepend the current spot to the beginning, then take cumulative product
    # We only need horizon_days steps ahead.
    paths = np.zeros((n_paths, horizon_days))
    paths[:, 0] = current_spot * daily_returns_sim[:, 0]
    for t in range(1, horizon_days):
        paths[:, t] = paths[:, t - 1] * daily_returns_sim[:, t]

    # Calculate percentiles across all paths for each day
    p10_envelope = np.percentile(paths, 10, axis=0).tolist()
    p50_envelope = np.percentile(paths, 50, axis=0).tolist()
    p90_envelope = np.percentile(paths, 90, axis=0).tolist()

    return FxSimulationResult(
        pair=pair,
        current_spot=float(current_spot),
        implied_vol=implied_vol_annualized,
        p10_envelope=p10_envelope,
        p50_envelope=p50_envelope,
        p90_envelope=p90_envelope,
        horizon_days=horizon_days,
    )
