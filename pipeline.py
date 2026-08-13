"""Orchestration pipeline to run extraction from raw report text."""

import pandas as pd

from confidence import run_confidence_validation
from config import (
    GPT_OSS_EXTRACTIONS_DIR,
    GPT_OSS_MODEL_NAME,
    GPT_OSS_VALIDATION_DIR,
    RAND_SUBSET,
    REPORTS_FP,
    RESPONSE_FORMAT,
)
from extractor import run_extraction


def main():
    GPT_OSS_EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    GPT_OSS_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    reports_df = pd.read_csv(REPORTS_FP)

    extraction_files, failed_extractions = run_extraction(
        reports_df,
        RAND_SUBSET,
        GPT_OSS_MODEL_NAME,
        RESPONSE_FORMAT,
        GPT_OSS_EXTRACTIONS_DIR,
    )

    print(f"\nGPT-OSS failed: {len(failed_extractions)} / {RAND_SUBSET}")
    if failed_extractions:
        pd.DataFrame(failed_extractions).to_csv(
            GPT_OSS_EXTRACTIONS_DIR / "failed_extractions.csv", index=False
        )

    extraction_files = GPT_OSS_EXTRACTIONS_DIR.glob("*.json")

    validation_overview, field_results_df = run_confidence_validation(
        extraction_files,
        reports_df,
    )
    validation_overview.to_csv(
        GPT_OSS_VALIDATION_DIR / "validation_overview.csv",
        float_format="%.2f",
        index=False,
    )
    field_results_df.to_csv(
        GPT_OSS_VALIDATION_DIR / "field_results.csv", float_format="%.2f", index=False
    )


if __name__ == "__main__":
    main()
