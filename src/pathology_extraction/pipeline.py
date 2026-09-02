"""Orchestration pipeline to run extraction from raw report text."""

import logging
from pathlib import Path

import pandas as pd

from pathology_extraction.config import (
    LOG_LEVEL,
    MODELS,
    RAND_SEED,
    RAND_SUBSET,
    REPORTS_FP,
    RESULTS_DIR,
)
from pathology_extraction.extraction import run_extraction
from pathology_extraction.model_agreement import run_model_agreement
from pathology_extraction.review import (
    generate_field_level_review,
    generate_overall_review,
)
from pathology_extraction.validation import run_confidence_validation

logging.basicConfig(level=LOG_LEVEL, format="%(message)s")
logger = logging.getLogger(__name__)


def run_model_extraction(reports_df: pd.DataFrame, model_config: dict) -> None:
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
    if failed_extractions is not None:
        logger.info(
            f"\n{model_config['name']} failed: "
            f"{len(failed_extractions)} / {RAND_SUBSET}"
        )

    failed_extractions_df = pd.DataFrame(failed_extractions)
    if not failed_extractions_df.empty:
        failed_extractions_df.to_csv(
            extraction_dir / "failed_extractions.csv",
            index=False,
        )

    return extraction_files, failed_extractions_df


def run_model_validation(
    reports_df: pd.DataFrame, model_config: dict, extraction_files: list[Path]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute confidence metrics for a model's extractions. No review logic."""
    validation_dir = model_config["validation_dir"]
    validation_dir.mkdir(parents=True, exist_ok=True)

    validation_overview, field_results_df = run_confidence_validation(
        extraction_files, reports_df
    )
    validation_overview.to_csv(
        validation_dir / "validation_overview.csv", float_format="%.2f", index=False
    )
    field_results_df.to_csv(
        validation_dir / "field_results.csv", float_format="%.2f", index=False
    )

    return validation_overview, field_results_df


def run_model_review(
    model_config: dict,
    validation_overview: pd.DataFrame,
    field_results_df: pd.DataFrame,
    failed_extractions_df: pd.DataFrame,
    agreement_df: pd.DataFrame | None,
) -> None:
    """Build and save review queues from already-computed validation metrics."""
    review_dir = model_config["review_dir"]
    review_dir.mkdir(parents=True, exist_ok=True)

    review_queue_all = generate_overall_review(
        validation_overview, failed_extractions_df, agreement_df
    )
    review_queue_all.to_csv(review_dir / "review_queue_all.csv", index=False)

    review_queue_fields = generate_field_level_review(
        field_results_df, review_queue_all, agreement_df
    )
    review_queue_fields.to_csv(review_dir / "review_queue_field_level.csv", index=False)


def main() -> None:
    """Run extraction and persist any failed-extraction records for review."""
    try:
        reports_df = pd.read_csv(REPORTS_FP)
    except FileNotFoundError:
        logger.error(
            f"Dataset not found at {REPORTS_FP}. "
            "Download TCGA_Reports.csv.zip from "
            "https://github.com/tatonetti-lab/tcga-path-reports and "
            "unzip it into dataset/. See README.md for details."
        )

    # Run extraction pipeline for each model
    extraction_results = {}
    for model_name, model_config in MODELS.items():
        extraction_results[model_name] = run_model_extraction(reports_df, model_config)

    # Evaluate extrction agreement across models
    agreement_df = run_model_agreement(MODELS)
    agreement_df.to_csv(
        RESULTS_DIR / "model_agreement.csv",
        index=False,
    )

    # Run validation per model and review queue
    for model_name, model_config in MODELS.items():
        extraction_files, failed_extractions_df = extraction_results[model_name]
        validation_overview, field_results_df = run_model_validation(
            reports_df, model_config, extraction_files
        )
        # Review based on each model and agreement across models
        run_model_review(
            model_config,
            validation_overview,
            field_results_df,
            failed_extractions_df,
            agreement_df,
        )


if __name__ == "__main__":
    main()
