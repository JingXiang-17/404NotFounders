from pydantic import BaseModel, Field
from typing import List, Literal, Any
from datetime import datetime

class SnapshotEnvelope(BaseModel):
    dataset: str
    source: str
    fetched_at: datetime
    as_of: datetime
    status: Literal["success", "partial", "failed"]
    record_count: int
    data: List[Any]
