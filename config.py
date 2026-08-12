"""Shared paths and constants for the pathology extraction pipeline."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "dataset"
REPORTS_FP = DATA_DIR / "TCGA_Reports.csv"
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_DIRECT_API_DIR = RESULTS_DIR / "directAPI"
RESUTLS_LLAMA_DIR = RESULTS_DIR / "llamaindex"

MODEL_NAME = "openai/gpt-oss-120b"
