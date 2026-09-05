"""Review of the extraction for human in the loop validation."""

import re

import pandas as pd

from pathology_extraction.config import (
    COMPOSITE_SCORE_TH,
    DEFAULT_WEIGHTS,
    MAX_ERROR_MSG_LEN,
    MODEL_AGREEMENT_TH,
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
    if row["value_evidence_inconsistency"]:
        reasons.append("value/evidence mismatch")
    if row["evidence_grounding_missing"]:
        reasons.append("evidence not grounded")
    if row["low_composite_score"]:
        reasons.append("low composite confidence score")
    if row["model_disagreement"]:
        reasons.append("model disagreement")
    return "; ".join(reasons)


def compute_field_composite_score(
    field_result: dict, agreement: float | None = None, weights: dict = DEFAULT_WEIGHTS
) -> float | None:
    """Compute a composite score for a field based on
    its grounding, consistency, and agreement."""
    grounding_score = field_result.get("evidence_semantic_score")
    value_score = field_result.get("value_evidence_score")
    if grounding_score is None or value_score is None:
        return None

    if agreement is not None:
        return (
            weights["evidence_grounding"] * grounding_score
            + weights["value_evidence_consistency"] * value_score
            + weights["model_agreement"] * agreement
        )
    # Fallback: no agreement data available, rescale remaining two weights
    total = weights["evidence_grounding"] + weights["value_evidence_consistency"]
    return (weights["evidence_grounding"] / total) * grounding_score + (
        weights["value_evidence_consistency"] / total
    ) * value_score


def compute_report_composite_score(
    report_id, field_level_review_df: pd.DataFrame
) -> float | None:
    """Compute the composite score for a report based on its field results.

    Args:
        field_level_review_df: DataFrame containing field-level review queue results.
        report_id: The ID of the report for which to compute the composite score.

    Returns:
        The composite score for the report, None if no valid field scores are available.
    """

    valid_scores = field_level_review_df[
        field_level_review_df["report_id"] == report_id
    ]["composite_score"].dropna()
    if not valid_scores.empty:
        return valid_scores.mean()
    return None


def generate_overall_review(
    field_level_review_df: pd.DataFrame,
    failed_extractions: pd.DataFrame | None,
) -> pd.DataFrame:
    """Build a review queue from failed extractions and low-confidence results.

    Args:
        field_level_review_df: DataFrame containing field-level review queue results.
        failed_extractions: Extraction failures with ``report_id`` and ``error`` keys.

    Returns:
        A DataFrame containing review flags for each affected report.
    """
    grouped = field_level_review_df.groupby("report_id")

    composite_score = grouped["composite_score"].mean()
    low_composite_score = composite_score < COMPOSITE_SCORE_TH
    value_evidence_inconsistency = grouped["value_evidence_pass"].apply(
        lambda s: (~s).any()
    )
    evidence_grounding_missing = grouped["evidence_grounding_pass"].apply(
        lambda s: (~s).any()
    )
    model_disagreement = grouped["model_disagreement"].any()

    review_queue_df = pd.DataFrame(
        {
            "report_id": composite_score.index,
            "failed_extraction": None,
            "value_evidence_inconsistency": value_evidence_inconsistency.values,
            "evidence_grounding_missing": evidence_grounding_missing.values,
            "low_composite_score": low_composite_score.values,
            "model_disagreement": model_disagreement.values,
        }
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

    # Filter out report ids that do not need review
    review_queue_df = review_queue_df[
        review_queue_df["failed_extraction"].notna()
        | review_queue_df["value_evidence_inconsistency"]
        | review_queue_df["evidence_grounding_missing"]
        | review_queue_df["low_composite_score"]
        | review_queue_df["model_disagreement"]
    ]

    review_queue_df["review_reason"] = review_queue_df.apply(
        build_review_reason, axis=1
    )

    review_queue_df["composite_score_mean"] = composite_score.reindex(
        review_queue_df["report_id"]
    ).values.round(2)
    review_queue_df["composite_score_min"] = (
        grouped["composite_score"]
        .min()
        .reindex(review_queue_df["report_id"])
        .values.round(2)
    )
    review_queue_df["failed_extraction"] = (
        review_queue_df["failed_extraction"].fillna(False).astype(bool)
    )

    overview_queue_df = review_queue_df[
        [
            "report_id",
            "failed_extraction",
            "value_evidence_inconsistency",
            "evidence_grounding_missing",
            "low_composite_score",
            "model_disagreement",
            "composite_score_min",
        ]
    ].sort_values("composite_score_min")

    print(
        review_queue_df[
            [
                "value_evidence_inconsistency",
                "evidence_grounding_missing",
                "low_composite_score",
                "model_disagreement",
            ]
        ].corr()
    )
    return overview_queue_df


def generate_field_level_review(
    field_results_df: pd.DataFrame,
    agreement_df: pd.DataFrame | None = None,
    agreement_th: float = MODEL_AGREEMENT_TH,
) -> pd.DataFrame:
    """Build a field-level review queue from field results and model agreement."""
    field_level_review_df = field_results_df.copy()

    if agreement_df is not None and not agreement_df.empty:
        field_level_review_df = field_level_review_df.merge(
            agreement_df[["report_id", "field_name", "agreement"]],
            on=["report_id", "field_name"],
            how="left",
        )
        field_level_review_df["model_disagreement"] = (
            field_level_review_df["agreement"] < agreement_th
        )
    else:
        field_level_review_df["model_disagreement"] = False

    field_level_review_df["composite_score"] = field_level_review_df.apply(
        lambda row: compute_field_composite_score(row, row["agreement"]), axis=1
    )

    return field_level_review_df
