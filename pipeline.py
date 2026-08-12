"""Orchestration pipeline to run extraction from raw report text."""

import pandas as pd

from confidence import run_confidence_validation
from config import (
    DIRECT_API_EXTRACTIONS_DIR,
    DIRECT_API_VALIDATION_DIR,
    RAND_SUBSET,
    REPORTS_FP,
)
from extractor import run_extraction


def main():
    DIRECT_API_EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    DIRECT_API_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    reports_df = pd.read_csv(REPORTS_FP)
    extraction_files, failed_extractions = run_extraction(reports_df, RAND_SUBSET)
    print(f"Failed extractions: {len(failed_extractions)} / {RAND_SUBSET}")

    run_confidence_validation(extraction_files, reports_df)


if __name__ == "__main__":
    main()
