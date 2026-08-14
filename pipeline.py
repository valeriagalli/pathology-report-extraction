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
from review import generate_field_level_review, generate_overall_review


def main() -> None:
    """Run the extraction, validation, and review pipeline."""
    GPT_OSS_EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    GPT_OSS_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    reports_df = pd.read_csv(REPORTS_FP)

    # Extract structured reports
    extraction_files, failed_extractions = run_extraction(
        reports_df,
        RAND_SUBSET,
        GPT_OSS_MODEL_NAME,
        RESPONSE_FORMAT,
        GPT_OSS_EXTRACTIONS_DIR,
    )

    # Log failed extractions
    print(f"\nGPT-OSS failed: {len(failed_extractions)} / {RAND_SUBSET}")
    if failed_extractions:
        pd.DataFrame(failed_extractions).to_csv(
            GPT_OSS_EXTRACTIONS_DIR / "failed_extractions.csv", index=False
        )

    # Validate extraction
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

    # Flag for human review
    review_queue_all = generate_overall_review(validation_overview, failed_extractions)
    review_queue_all.to_csv(
        GPT_OSS_VALIDATION_DIR / "review_queue_all.csv", index=False
    )
    review_queue_fields = generate_field_level_review(
        field_results_df, review_queue_all
    )
    review_queue_fields.to_csv(
        GPT_OSS_VALIDATION_DIR / "review_queue_field_level.csv", index=False
    )


if __name__ == "__main__":
    main()
