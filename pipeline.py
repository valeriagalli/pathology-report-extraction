"""Orchestration pipeline to run extraction from raw report text."""

import logging

import pandas as pd

from confidence import run_confidence_validation
from config import LOG_LEVEL, MODELS, RAND_SEED, RAND_SUBSET, REPORTS_FP, RESULTS_DIR
from extractor import run_extraction
from model_agreement import run_model_agreement
from review import generate_field_level_review, generate_overall_review


def run_model_pipeline(reports_df: pd.DataFrame, model_config: dict) -> None:
    """Run extraction, validation, and review with a selected model.
    Saves results to dedicated subfolders.

    Args:
        reports_df: DataFrame containing raw reports.
        model_config: Configuration dict for the extraction model.
    """
    # Create directories
    extraction_dir = model_config["extraction_dir"]
    review_dir = model_config["review_dir"]
    validation_dir = model_config["validation_dir"]
    extraction_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    # Extract structured reports
    extraction_files, failed_extractions = run_extraction(
        reports_df,
        RAND_SUBSET,
        RAND_SEED,
        model_config["name"],
        model_config["prompt"],
        model_config["response_format"],
        extraction_dir,
    )

    # Evaluate and save failed extractions
    print(f"\n{model_config['name']} failed: {len(failed_extractions)} / {RAND_SUBSET}")

    failed_extractions_df = pd.DataFrame(failed_extractions)
    if not failed_extractions_df.empty:
        failed_extractions_df.to_csv(
            extraction_dir / "failed_extractions.csv",
            index=False,
        )

    # Validate extractions
    validation_overview, field_results_df = run_confidence_validation(
        extraction_files,
        reports_df,
    )
    # Save overall validation result
    validation_overview.to_csv(
        validation_dir / "validation_overview.csv",
        float_format="%.2f",
        index=False,
    )
    # Save field level validation results
    field_results_df.to_csv(
        validation_dir / "field_results.csv",
        float_format="%.2f",
        index=False,
    )

    # Create and save review queue based on overall validation
    review_queue_all = generate_overall_review(
        validation_overview,
        failed_extractions_df,
    )
    review_queue_all.to_csv(
        review_dir / "review_queue_all.csv",
        index=False,
    )

    # Create and save review queue based on field level validation
    review_queue_fields = generate_field_level_review(
        field_results_df,
        review_queue_all,
    )
    review_queue_fields.to_csv(
        review_dir / "review_queue_field_level.csv",
        index=False,
    )


def main() -> None:
    """Run extraction and persist any failed-extraction records for review."""
    reports_df = pd.read_csv(REPORTS_FP)

    # Run extraction pipeline for each model
    for model_config in MODELS.values():
        run_model_pipeline(reports_df, model_config)

    # Evaluate agreement across models
    agreement_df = run_model_agreement(MODELS)
    agreement_df.to_csv(
        RESULTS_DIR / "model_agreement.csv",
        index=False,
    )


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL, format="%(message)s")
    main()
