from __future__ import annotations

from urllib.parse import urlparse

from app.core.constants import (
    SUPPORTED_COUNTRY_CODES,
    SUPPORTED_DESTINATION_PORT,
    SUPPORTED_HS_CODE,
    SUPPORTED_IMPORT_COUNTRY,
    SUPPORTED_INCOTERM,
    SUPPORTED_ORIGIN_COUNTRIES,
    SUPPORTED_PORT_CODES,
    SUPPORTED_PRODUCT_NAME,
)
from app.core.exceptions import ValidationError
from app.repositories.reference_repository import ReferenceRepository
from app.schemas.common import ensure_iso_date, ensure_required_keys


class ReferenceDataService:
    def __init__(self, repository: ReferenceRepository) -> None:
        self.repository = repository

    def validate_all(self) -> dict[str, int]:
        freight_rows = self.repository.load_json("freight_rates.json")
        tariff_rows = self.repository.load_json("tariffs_my_hs.json")
        port_rows = self.repository.load_json("ports.json")
        source_rows = self.repository.load_json("source_registry.json")

        self._validate_freight_rows(freight_rows)
        self._validate_tariff_rows(tariff_rows)
        self._validate_port_rows(port_rows)
        self._validate_source_rows(source_rows)

        return {
            "freight_rates": len(freight_rows),
            "tariffs": len(tariff_rows),
            "ports": len(port_rows),
            "resin_sources": len(source_rows),
        }

    def _validate_freight_rows(self, rows: list[dict]) -> None:
        for row in rows:
            ensure_required_keys(
                row,
                {
                    "origin_country",
                    "origin_port",
                    "destination_port",
                    "incoterm",
                    "currency",
                    "rate_value",
                    "rate_unit",
                    "valid_from",
                    "valid_to",
                    "source_note",
                },
                "Freight row",
            )
            if row["origin_country"] not in SUPPORTED_ORIGIN_COUNTRIES:
                raise ValidationError("Freight row origin_country is outside supported corridors")
            if row["destination_port"] != SUPPORTED_DESTINATION_PORT:
                raise ValidationError("Freight row destination_port must be MYPKG")
            if row["incoterm"] != SUPPORTED_INCOTERM:
                raise ValidationError("Freight row incoterm must be FOB")
            if row["origin_port"] not in SUPPORTED_PORT_CODES:
                raise ValidationError("Freight row origin_port must be a supported port code")
            ensure_iso_date(row["valid_from"], "Freight valid_from")
            ensure_iso_date(row["valid_to"], "Freight valid_to")

    def _validate_tariff_rows(self, rows: list[dict]) -> None:
        for row in rows:
            ensure_required_keys(
                row,
                {
                    "hs_code",
                    "product_name",
                    "import_country",
                    "tariff_rate_pct",
                    "tariff_type",
                    "source_note",
                },
                "Tariff row",
            )
            if row["hs_code"] != SUPPORTED_HS_CODE:
                raise ValidationError("Tariff row hs_code must be 3902.10")
            if row["product_name"] != SUPPORTED_PRODUCT_NAME:
                raise ValidationError("Tariff row product_name must be PP Resin")
            if row["import_country"] != SUPPORTED_IMPORT_COUNTRY:
                raise ValidationError("Tariff row import_country must be MY")

    def _validate_port_rows(self, rows: list[dict]) -> None:
        for row in rows:
            ensure_required_keys(
                row,
                {"port_code", "port_name", "country_code", "latitude", "longitude", "is_destination_hub"},
                "Port row",
            )
            if row["port_code"] not in SUPPORTED_PORT_CODES:
                raise ValidationError("Port row port_code must be in the supported set")
            if row["country_code"] not in SUPPORTED_COUNTRY_CODES:
                raise ValidationError("Port row country_code must be supported")

    def _validate_source_rows(self, rows: list[dict]) -> None:
        for row in rows:
            ensure_required_keys(
                row,
                {
                    "source_name",
                    "url",
                    "domain",
                    "expected_region",
                    "expected_content_type",
                    "language",
                    "priority",
                    "notes",
                    "enabled",
                },
                "Source row",
            )
            parsed = urlparse(row["url"])
            if parsed.scheme not in {"http", "https"}:
                raise ValidationError("Source row URL must be http or https")
            if row["domain"] not in parsed.netloc:
                raise ValidationError("Source row domain must match the URL host")

