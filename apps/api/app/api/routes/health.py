from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.providers.llm_provider import GLMProvider
from app.repositories.snapshot_repository import SnapshotRepository
from app.services.reference_data_service import ReferenceDataService
from app.repositories.reference_repository import ReferenceRepository

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok", 
        "model": settings.MODEL_NAME
    }


@router.get("/health/langfuse")
def langfuse_health_check():
    status = GLMProvider.langfuse_status()
    if not status["enabled"]:
        missing = [
            key
            for key, present in [
                ("LANGFUSE_PUBLIC_KEY", status.get("public_key_present")),
                ("LANGFUSE_SECRET_KEY", status.get("secret_key_present")),
                ("LANGFUSE_HOST", bool(status.get("host"))),
                ("langfuse SDK", status.get("sdk_available")),
            ]
            if not present
        ]
        raise HTTPException(
            status_code=503,
            detail={
                "status": "langfuse_unavailable",
                "message": "Langfuse tracing is NOT enabled. The following are missing or not installed: "
                           + ", ".join(missing),
                **status,
            },
        )
    return status


@router.get("/health/ingestion")
def ingestion_health_check():
    repository = SnapshotRepository()
    datasets = {
        "fx/USDMYR": 30,
        "fx/CNYMYR": 30,
        "fx/THBMYR": 30,
        "fx/IDRMYR": 30,
        "energy/BZ=F": 30,
        "weather": 1,
        "macro": 1,
        "macro_trade": 1,
        "news": 1,
        "resin": 1,
        "holidays": 1,
    }
    statuses = {}
    for dataset, min_records in datasets.items():
        envelope = repository.read_latest(dataset)
        statuses[dataset] = (
            {
                "present": False,
                "status": "missing",
                "source": None,
                "fetched_at": None,
                "as_of": None,
                "record_count": 0,
                "min_required_records": min_records,
                "usable": False,
            }
            if envelope is None
            else {
                "present": True,
                "status": envelope.status,
                "source": envelope.source,
                "fetched_at": envelope.fetched_at,
                "as_of": envelope.as_of,
                "record_count": envelope.record_count,
                "min_required_records": min_records,
                "usable": envelope.status == "success" and envelope.record_count >= min_records,
            }
        )

    missing = [dataset for dataset, status in statuses.items() if not status["present"]]
    non_success = [
        dataset
        for dataset, status in statuses.items()
        if status["present"] and status["status"] != "success"
    ]
    underfilled = [
        dataset
        for dataset, status in statuses.items()
        if status["present"] and status["record_count"] < status["min_required_records"]
    ]
    try:
        reference_counts = ReferenceDataService(ReferenceRepository()).validate_all()
        reference_status = {
            "present": True,
            "status": "success",
            "counts": reference_counts,
            "usable": all(count > 0 for count in reference_counts.values()),
        }
    except Exception as exc:
        reference_status = {
            "present": False,
            "status": "failed",
            "error": str(exc),
            "counts": {},
            "usable": False,
        }
    return {
        "status": (
            "ok"
            if not missing and not non_success and not underfilled and reference_status["usable"]
            else "attention_needed"
        ),
        "checked_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "missing": missing,
        "non_success": non_success,
        "underfilled": underfilled,
        "reference_data": reference_status,
        "datasets": statuses,
    }
