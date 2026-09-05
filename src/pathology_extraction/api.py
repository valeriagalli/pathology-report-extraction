"""
FastAPI module to expose the pathology report extraction.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from pathology_extraction.config import MODELS
from pathology_extraction.extraction import build_extractor
from pathology_extraction.schema import PathologyExtraction
from pathology_extraction.validation import (
    validate_field_evidence,
    validate_field_value,
)

app = FastAPI()


class ExtractionRequest(BaseModel):
    """Defines the request body for the extraction endpoint."""

    report_text: str


class FieldScore(BaseModel):
    """Defines the structure of each field's score in the extraction response."""

    value: str | None
    evidence: str | None
    value_evidence_score: float | None
    evidence_semantic_score: float | None


class ExtractionResponse(BaseModel):
    """Defines the response body for the extraction endpoint."""

    fields: dict[str, FieldScore]


@app.post("/extract", response_model=ExtractionResponse)
def extract_report(request: ExtractionRequest):
    """Extract structured fields from a pathology report and validate them."""
    model_config = MODELS["gpt_oss_120b"]
    extraction = build_extractor(
        model_config["name"],
        model_config["prompt"],
        model_config["response_format"],
        request.report_text,
    )

    from pathology_extraction.text_processing import normalize_string

    raw_clean = normalize_string(request.report_text)

    fields = {}
    for field_name in PathologyExtraction.model_fields:
        field = getattr(extraction, field_name)
        if field.value is None or field.evidence is None:
            fields[field_name] = FieldScore(
                value=None,
                evidence=None,
                value_evidence_score=None,
                evidence_semantic_score=None,
            )
            continue

        value_score, _ = validate_field_value(field.value, field.evidence)
        _, semantic_score, _ = validate_field_evidence(field.evidence, raw_clean)

        fields[field_name] = FieldScore(
            value=field.value,
            evidence=field.evidence,
            value_evidence_score=value_score,
            evidence_semantic_score=semantic_score,
        )

    return ExtractionResponse(fields=fields)
