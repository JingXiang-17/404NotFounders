import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Dict, List, Any

from app.core.config import settings
from app.core.exceptions import ValidationFailed

class FreightRate(BaseModel):
    model_config = {"extra": "allow"}

class Tariff(BaseModel):
    model_config = {"extra": "allow"}

class Port(BaseModel):
    model_config = {"extra": "allow"}

class SupplierSeed(BaseModel):
    model_config = {"extra": "allow"}

class ReferenceRepository:
    def __init__(self, ref_dir: Path = settings.REFERENCE_DIR):
        self.ref_dir = ref_dir

    def _load_json(self, filename: str) -> Any:
        filepath = self.ref_dir / filename
        if not filepath.exists():
            raise ValidationFailed(f"Reference file {filename} not found in {self.ref_dir}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationFailed(f"Failed to parse {filename}: {str(e)}")

    def get_freight_rates(self) -> List[FreightRate]:
        data = self._load_json("freight_rates.json")
        try:
            return [FreightRate(**item) for item in data]
        except ValidationError as e:
            raise ValidationFailed(f"Validation failed for freight_rates.json: {e}")

    def get_tariffs(self) -> List[Tariff]:
        data = self._load_json("tariffs_my_hs.json")
        try:
            return [Tariff(**item) for item in data]
        except ValidationError as e:
            raise ValidationFailed(f"Validation failed for tariffs_my_hs.json: {e}")

    def get_ports(self) -> List[Port]:
        data = self._load_json("ports.json")
        try:
            return [Port(**item) for item in data]
        except ValidationError as e:
            raise ValidationFailed(f"Validation failed for ports.json: {e}")

    def get_supplier_seeds(self) -> List[SupplierSeed]:
        data = self._load_json("supplier_seeds.json")
        try:
            return [SupplierSeed(**item) for item in data]
        except ValidationError as e:
            raise ValidationFailed(f"Validation failed for supplier_seeds.json: {e}")
