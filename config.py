"""Shared paths and constants for the pathology extraction pipeline."""

from pathlib import Path

from schema import PathologyExtraction

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "dataset"
REPORTS_FP = DATA_DIR / "TCGA_Reports.csv"
RESULTS_DIR = ROOT_DIR / "results"

GPT_OSS_DIR = RESULTS_DIR / "gpt_oss"
GPT_OSS_EXTRACTIONS_DIR = GPT_OSS_DIR / "extractions"
GPT_OSS_VALIDATION_DIR = GPT_OSS_DIR / "validation"

GPT_OSS_MODEL_NAME = "openai/gpt-oss-120b"

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "pathology_extraction",
        "strict": True,
        "schema": PathologyExtraction.model_json_schema(),
    },
}

RAND_SUBSET = 5
