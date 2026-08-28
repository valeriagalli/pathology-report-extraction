"""Review of the extraction for human in the loop validation."""

import re

import pandas as pd

from config import (
    COMPOSITE_SCORE_TH,
    EVIDENCE_REPORT_GROUNDING_TH,
    MAX_ERROR_MSG_LEN,
    MODEL_AGREEMENT_TH,
    VALUE_EVIDENCE_CONSISTENCY_TH,
)


def get_clean_error(e: object, max_len: int = MAX_ERROR_MSG_LEN) -> str:
    """Return a concise error message from an SDK exception or error value.

    Args:
        e: Exception or other value representing an extraction failure.
        max_len: Maximum length of the returned message before truncation.

    Returns:
        A normalized error message suitable for logs and review queues.
    """
    # Groq/OpenAI exceptions store the clean payload in e.body
    if hasattr(e, "body") and isinstance(e.body, dict):
        err_dict = e.body.get("error", {})
        if isinstance(err_dict, dict) and "message" in err_dict:
            msg = str(err_dict["message"])
            return msg if len(msg) <= max_len else msg[:max_len] + "..."

    # Fallback if e.body doesn't exist: regex out 'message': '...' from str(e)
    raw = str(e)
    match = re.search(r"['\"]message['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw)
    msg = match.group(1) if match else raw

    error_msg_truncated = msg if len(msg) <= max_len else msg[:max_len] + "..."

    return error_msg_truncated


def build_review_reason(row: pd.Series) -> str:
    """Return a string explaining the reason for human review based on the issue."""
    reasons = []
    if pd.notna(row["failed_extraction"]):
        reasons.append("extraction failed")
    if row["value_evidence_inconsistency"]:
        reasons.append("value/evidence mismatch")
    if row["evidence_grounding_missing"]:
        reasons.append("evidence not grounded")
    if row["low_composite_score"]:
        reasons.append("low composite confidence score")
    return "; ".join(reasons)


def generate_overall_review(
    validation_overview: pd.DataFrame,
    failed_extractions: pd.DataFrame | None,
    agreement_df: pd.DataFrame | None = None,
    agreement_th: float = MODEL_AGREEMENT_TH,
) -> pd.DataFrame:
    """Build a review queue from failed extractions and low-confidence results.

    Args:
        validation_overview: Per-report confidence metrics.
        failed_extractions: Extraction failures with ``report_id`` and ``error`` keys.

    Returns:
        A DataFrame containing review flags for each affected report.
    """
    # Base queue from validation overview
    if validation_overview is not None and not validation_overview.empty:
        review_queue_df = pd.DataFrame(
            {
                "report_id": validation_overview["report_id"],
                "failed_extraction": None,
                "value_evidence_inconsistency": (
                    validation_overview["value_evidence_consistency"]
                    < VALUE_EVIDENCE_CONSISTENCY_TH
                ),
                "evidence_grounding_missing": (
                    validation_overview["evidence_report_grounding"]
                    < EVIDENCE_REPORT_GROUNDING_TH
                ),
                "low_composite_score": (
                    validation_overview["composite_score"] < COMPOSITE_SCORE_TH
                ),
            }
        )
    else:
        review_queue_df = pd.DataFrame(
            columns=[
                "report_id",
                "failed_extraction",
                "value_evidence_inconsistency",
                "evidence_grounding_missing",
                "low_composite_score",
                "model_disagreement",
            ]
        )

    # Update existing rows / Add missing rows from failed_extractions
    if failed_extractions is not None and not failed_extractions.empty:
        # Drop empty rows and deduplicate failed extractions by report_id
        failed = failed_extractions.dropna(subset=["report_id"])[
            ["report_id", "error"]
        ].drop_duplicates(subset=["report_id"], keep="last")

        review_queue_df = pd.merge(review_queue_df, failed, on="report_id", how="outer")

        # Merge error column into failed_extraction
        review_queue_df["failed_extraction"] = review_queue_df[
            "failed_extraction"
        ].fillna(review_queue_df["error"])
        review_queue_df.drop(columns=["error"], inplace=True)

        # Fill boolean flags for reports that failed completely
        review_queue_df["value_evidence_inconsistency"] = review_queue_df[
            "value_evidence_inconsistency"
        ].fillna(False)
        review_queue_df["evidence_grounding_missing"] = review_queue_df[
            "evidence_grounding_missing"
        ].fillna(False)

    # Model agreement
    if agreement_df is not None and not agreement_df.empty:
        low_agreement_ids = set(
            agreement_df.loc[agreement_df["agreement"] < agreement_th, "report_id"]
        )
        review_queue_df["model_disagreement"] = review_queue_df["report_id"].isin(
            low_agreement_ids
        )
    else:
        review_queue_df["model_disagreement"] = False

    # Filter out report ids that do not need review
    review_queue_df = review_queue_df[
        review_queue_df["failed_extraction"].notna()
        | review_queue_df["value_evidence_inconsistency"]
        | review_queue_df["evidence_grounding_missing"]
        | review_queue_df["model_disagreement"]
    ]

    review_queue_df["review_reason"] = review_queue_df.apply(
        build_review_reason, axis=1
    )
    return review_queue_df[
        ["report_id", "review_reason", "failed_extraction", "model_disagreement"]
    ]


def generate_field_level_review(
    field_results_df: pd.DataFrame, review_queue_df: pd.DataFrame
) -> pd.DataFrame:
    """Filter field-level validation results for reports requiring review.

    Args:
        field_results_df: Field-level validation metrics for all reports.
        review_queue_df: DataFrame with report IDs requiring review.

    Returns:
        Field-level results for reports in the review queue.
    """
    field_level_review_df = field_results_df[
        field_results_df["report_id"].isin(review_queue_df["report_id"])
    ]
    return field_level_review_df
