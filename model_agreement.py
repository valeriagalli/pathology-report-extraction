"""Calculate agreement across different extration models."""

import logging
from collections import Counter

import pandas as pd

from schema import PathologyExtraction
from text_processing import normalize_string

logger = logging.getLogger(__name__)


def get_common_extraction_files(models_config: dict) -> list[str]:
    """Find extraction files common across multiple extraction models."""
    file_sets = []
    for model_config in models_config.values():
        files = model_config["extraction_dir"].glob("*.json")
        filenames = {file.name for file in files}
        file_sets.append(filenames)

    common_files = set.intersection(*file_sets)
    return list(common_files)


def calculate_field_agreement(
    report_id: str, model_results: list[PathologyExtraction]
) -> list[dict[str, str | float]]:
    """Calculate field agreement across models for a single report.

    Args:
        report_id: Identifier for the report.
        model_results: List of extraction results from different models.

    Returns:
        List of agreement metrics for each field.
    """
    agreement_results = []

    for field in PathologyExtraction.model_fields:
        values = [
            normalize_string(getattr(result, field).value)
            if getattr(result, field).value is not None
            else None
            for result in model_results
        ]

        counts = Counter(values)
        consensus_value, consensus_count = counts.most_common(1)[0]

        agreement_results.append(
            {
                "report_id": report_id,
                "field": field,
                "consensus_value": consensus_value
                if consensus_value is not None
                else "MISSING",
                "agreement": consensus_count / len(values),
            }
        )

    return agreement_results


def run_model_agreement(models_config: dict) -> pd.DataFrame:
    """Calculate field agreement across all extraction models.

    Args:
        models_config: Configuration dict with model extraction directories.

    Returns:
        DataFrame with agreement metrics for all reports and fields.
    """
    common_filenames = get_common_extraction_files(models_config)
    logger.info(
        f"Comparing {len(common_filenames)} reports across {len(models_config)} models"
    )

    agreement_results = []

    # parse extracted reports common to all models
    for filename in common_filenames:
        report_id = filename
        model_results = []

        # Load specific report from every model
        for model_config in models_config.values():
            file = model_config["extraction_dir"] / report_id

            with open(file) as f:
                model_result = PathologyExtraction.model_validate_json(f.read())
            model_results.append(model_result)  # same report, different models

        # Calculate agreement
        agreement = calculate_field_agreement(report_id, model_results)

        # Append to list containing agreement for all files
        agreement_results.extend(agreement)

    agreement_df = pd.DataFrame(agreement_results)
    return agreement_df
