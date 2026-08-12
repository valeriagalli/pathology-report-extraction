"""Inspect raw report text and segment in meaningful sections."""

import re

import pandas as pd

from config import REPORTS_FP

MIN_TEXT_LEN = 10
MAX_SEGMENT_LEN = 200


def flag_short_report(report_id, report_text: str):
    if len(report_text.strip()) < MIN_TEXT_LEN:
        print(f"WARNING: unusually short report {report_id}: text length = {len(report_text)}")


def detect_text_units(text: str):
    return [unit.strip() for unit in re.split(r"\.\s+", text) if unit.strip()]


def clean_whitespace(text: str) -> str:
    """Normalize whitespace without changing character case."""
    if not text:
        return ""
    return " ".join(text.split())


def normalize_string(text: str) -> str:
    """Normalize text for case-insensitive matching."""
    return clean_whitespace(text).casefold()


def segment_text(text: str, max_length: int = MAX_SEGMENT_LEN):
    text_units = detect_text_units(text)
    segments = []
    current = ""

    for text_unit in text_units:
        if current and len(current) + 1 + len(text_unit) > max_length:
            segments.append(current)
            current = text_unit
        else:
            current = f"{current} {text_unit}".strip()

    if current:
        segments.append(current)

    return segments


if __name__ == "__main__":
    reports_raw_df = pd.read_csv(REPORTS_FP).copy()
    reports_raw_df["n_periods"] = reports_raw_df["text"].str.count(r"\.")
    reports_raw_df["n_characters"] = reports_raw_df["text"].str.len()
    n_text_units = []
    n_segments = []
    for _, row in reports_raw_df.iterrows():
        report_id = row["patient_filename"]
        report_text = row["text"]
        flag_short_report(report_id, report_text)
        report_text_clean = normalize_string(report_text)
        n_text_units.append(len(detect_text_units(report_text_clean)))
        n_segments.append(len(segment_text(report_text_clean)))

    reports_raw_df["n_text_units"] = n_text_units
    reports_raw_df["n_segments"] = n_segments
    print(reports_raw_df.drop(columns=["text"]).describe())