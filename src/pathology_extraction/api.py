"""
FastAPI module to expose the pathology report extraction.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from pathology_extraction.config import MODELS
from pathology_extraction.extraction import build_extractor
from pathology_extraction.schema import PathologyExtraction
from pathology_extraction.text_processing import normalize_string
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
            value_evidence_score=round(value_score, 2),
            evidence_semantic_score=round(semantic_score, 2),
        )

    return ExtractionResponse(fields=fields)


@app.get("/", response_class=HTMLResponse)
def form():
    """Serve a minimal HTML page for manually testing the /extract endpoint."""
    return """
    <html>
    <head><title>Pathology Report Extraction</title></head>
    <body style="font-family: sans-serif; max-width: 700px; margin: 40px auto;">
        <h2>Pathology Report Extraction</h2>
        <p>Paste a pathology report below and click Extract.</p>
        <textarea id="report" rows="15" style="width: 100%;"></textarea><br><br>
        <button onclick="submitReport()">Extract</button>
        <p id="status"></p>
        <pre id="result" style="background: #f4f4f4; padding: 10px; white-space: pre-wrap;"></pre>

        <script>
            async function submitReport() {
                const text = document.getElementById('report').value;
                const status = document.getElementById('status');
                const result = document.getElementById('result');

                if (!text.trim()) {
                    status.textContent = "Please paste some report text first.";
                    return;
                }

                status.textContent = "Extracting... (this can take a few seconds)";
                result.textContent = "";

                try {
                    const res = await fetch('/extract', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({report_text: text})
                    });
                    if (!res.ok) {
                        throw new Error(`Request failed: ${res.status}`);
                    }
                    const data = await res.json();
                    status.textContent = "Done.";
                    result.textContent = JSON.stringify(data, null, 2);
                } catch (err) {
                    status.textContent = "Error: " + err.message;
                }
            }
        </script>
    </body>
    </html>
    """