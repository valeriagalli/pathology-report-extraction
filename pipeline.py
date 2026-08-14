"""Orchestration pipeline to run extraction from raw report text."""

import pandas as pd

from confidence import run_confidence_validation
from config import (
    MODELS,
    RAND_SUBSET,
    REPORTS_FP,
)
from extractor import run_extraction
from review import generate_field_level_review, generate_overall_review


def run_pipeline(reports_df, model_config) -> None:
    """Run extraction, validation, and review with a selected model."""
    extraction_dir = model_config["extraction_dir"]
    validation_dir = model_config["validation_dir"]
    extraction_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    extraction_files, failed_extractions = run_extraction(
        reports_df,
        RAND_SUBSET,
        model_config["name"],
        model_config["prompt"],
        model_config["response_format"],
        extraction_dir,
    )

    print(f"\n{model_config['name']} failed: {len(failed_extractions)} / {RAND_SUBSET}")

    failed_extractions_df = pd.DataFrame({"report_id": failed_extractions})
    if not failed_extractions_df.empty:
        failed_extractions_df.to_csv(
            extraction_dir / "failed_extractions.csv",
            index=False,
        )

    validation_overview, field_results_df = run_confidence_validation(
        extraction_files,
        reports_df,
    )

    validation_overview.to_csv(
        validation_dir / "validation_overview.csv",
        float_format="%.2f",
        index=False,
    )

    field_results_df.to_csv(
        validation_dir / "field_results.csv",
        float_format="%.2f",
        index=False,
    )

    review_queue_all = generate_overall_review(
        validation_overview,
        failed_extractions_df,
    )
    review_queue_all.to_csv(
        validation_dir / "review_queue_all.csv",
        index=False,
    )

    review_queue_fields = generate_field_level_review(
        field_results_df,
        review_queue_all,
    )
    review_queue_fields.to_csv(
        validation_dir / "review_queue_field_level.csv",
        index=False,
    )


def main() -> None:
    """Run extraction and persist any failed-extraction records for review."""
    reports_df = pd.read_csv(REPORTS_FP)

    for model_config in MODELS.values():
        run_pipeline(reports_df, model_config)


if __name__ == "__main__":
    main()
