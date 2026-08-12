"""Shared paths and constants for the pathology extraction pipeline."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "dataset"
REPORTS_FP = DATA_DIR / "TCGA_Reports.csv"
RESULTS_DIR = ROOT_DIR / "results"

DIRECT_API_DIR = RESULTS_DIR / "direct_api"
DIRECT_API_EXTRACTIONS_DIR = DIRECT_API_DIR / "extractions"
DIRECT_API_VALIDATION_DIR = DIRECT_API_DIR / "validation"

DIRECT_API_MODEL_NAME = "openai/gpt-oss-120b"

RAND_SUBSET = 20
