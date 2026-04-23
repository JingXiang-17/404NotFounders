from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.core.exceptions import ValidationFailed
from app.core.settings import AppSettings


class FreightRate(BaseModel):
    model_config = {"extra": "allow"}


class Tariff(BaseModel):
    model_config = {"extra": "allow"}


class Port(BaseModel):
    model_config = {"extra": "allow"}


class SupplierSeed(BaseModel):
    model_config = {"extra": "allow"}


class ReferenceRepository:
    def __init__(self, ref_root: Any = None) -> None:
        if hasattr(ref_root, "reference_dir"):
            self.ref_dir = Path(ref_root.reference_dir)
        elif ref_root is None:
            self.ref_dir = Path(AppSettings.from_env().reference_dir)
        else:
            self.ref_dir = Path(ref_root)

    def list_reference_files(self) -> list[Path]:
        return sorted(self.ref_dir.glob("*.json"))

    def load_json(self, filename: str) -> Any:
        return self._load_json(filename)

    def _load_json(self, filename: str) -> Any:
        filepath = self.ref_dir / filename
        if not filepath.exists():
            raise ValidationFailed(f"Reference file {filename} not found in {self.ref_dir}")
        try:
            with filepath.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValidationFailed(f"Failed to parse {filename}: {str(exc)}") from exc

    def get_freight_rates(self) -> List[FreightRate]:
        data = self._load_json("freight_rates.json")
        try:
            return [FreightRate(**item) for item in data]
        except PydanticValidationError as exc:
            raise ValidationFailed(f"Validation failed for freight_rates.json: {exc}") from exc

    def get_tariffs(self) -> List[Tariff]:
        data = self._load_json("tariffs_my_hs.json")
        try:
            return [Tariff(**item) for item in data]
        except PydanticValidationError as exc:
            raise ValidationFailed(f"Validation failed for tariffs_my_hs.json: {exc}") from exc

    def get_ports(self) -> List[Port]:
        data = self._load_json("ports.json")
        try:
            return [Port(**item) for item in data]
        except PydanticValidationError as exc:
            raise ValidationFailed(f"Validation failed for ports.json: {exc}") from exc

    def get_supplier_seeds(self) -> List[SupplierSeed]:
        data = self._load_json("supplier_seeds.json")
        try:
            return [SupplierSeed(**item) for item in data]
        except PydanticValidationError as exc:
            raise ValidationFailed(f"Validation failed for supplier_seeds.json: {exc}") from exc
