"""Generate confidence score of the extracted fields."""

from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
from sentence_transformers import util

from config import (
    EVIDENCE_SEMANTIC_SIMILARITY_TH,
    STR_EMBEDDING_MODEL,
    VALUE_EVIDENCE_SIMILARITY_TH,
)
from report import detect_text_units, normalize_string
from schema import ExtractedField, PathologyExtraction


def load_and_validate_result(file: Path) -> PathologyExtraction | None:
    """Load and validate a saved extraction JSON into the schema object.

    Returns `None` if validation fails.
    """
    with open(file, "r") as f:
        try:
            report = PathologyExtraction.model_validate_json(f.read())
        except Exception as e:
            print(f"FAILED {file.stem}: {e}")
            return None
    return report


def load_raw_report(reports_df: pd.DataFrame, report_id: str) -> str | None:
    """Return the raw report text for `report_id`, or `None` if missing."""
    matches = reports_df.loc[reports_df["patient_filename"] == report_id, "text"]
    if matches.empty:
        print(f"No raw report text found for patient ID {report_id}")
        return None
    return matches.iloc[0]


def embed_string(string: str) -> object:
    """Encode text into an embedding tensor used for similarity comparisons."""
    return STR_EMBEDDING_MODEL.encode(string, convert_to_tensor=True)


def embedded_strings_similarity(embedding1: object, embedding2: object) -> float:
    """Return the cosine similarity between two encoded text embeddings."""
    return util.cos_sim(embedding1, embedding2).item()


def find_best_text_unit(evidence: str, text_units: list[str]) -> tuple[float, int]:
    """Return the best matching text unit for the evidence string."""
    matches = []
    for i, unit in enumerate(text_units):
        matches.append((SequenceMatcher(None, evidence, unit).ratio(), i))
    return max(matches, default=(0.0, 0), key=lambda x: x[0])


def combine_adjacent_units(selected_index: int, text_units: list[str]) -> list[str]:
    """Return a small span of text units around the selected index."""
    start = max(0, selected_index - 1)
    end = min(len(text_units), selected_index + 2)
    return text_units[start:end]


def validate_field_value(value: str, evidence: str) -> tuple[float | None, bool]:
    """Validate that the extracted value is consistent with the evidence.

    Args:
        value: The extracted field value.
        evidence: The supporting evidence text for the value.

    Returns:
        A tuple of (similarity_score, passed) where similarity_score is the
        semantic similarity between value and evidence (None if direct match),
        and passed is True if validation succeeded.
    """
    if value in evidence:
        print("Value-evidence consistency:\tDIRECT MATCH\t✅ PASS")
        passed = True
        similarity_score = None

    else:
        similarity_score = embedded_strings_similarity(
            embed_string(value),
            embed_string(evidence),
        )

        passed = similarity_score > VALUE_EVIDENCE_SIMILARITY_TH

        print(
            f"\tValue-evidence consistency:\t"
            f"{similarity_score:.2f}\t"
            f"{'✅ PASS' if passed else '❌ FAIL'}"
        )

    if not passed:
        print(f"\t\tValue:\t{value}")
        print(f"\t\tEvidence:\t{evidence}")

    return similarity_score, passed


def validate_field_evidence(
    evidence: str, report_raw_clean: str
) -> tuple[float, float | None, bool]:
    """Validate that the evidence text is grounded in the raw report.

    Args:
        evidence: The supporting evidence text.
        report_raw_clean: The cleaned raw report text.

    Returns:
        A tuple of (lexical_score, semantic_score, passed) where lexical_score
        is the sequence matching ratio, semantic_score is the embedding similarity
        (None if direct match), and passed is True if validation succeeded.
    """
    evidence_embedded = embed_string(evidence)

    text_units = detect_text_units(report_raw_clean)
    best_lexical_score, best_unit_index = find_best_text_unit(evidence, text_units)

    candidate_units = combine_adjacent_units(best_unit_index, text_units)
    candidate = " ".join(candidate_units)
    print("Evidence Grounding")
    if evidence in candidate:
        semantic_match_score = 1.0
        passed = True
        print("\tEvidence grounding\tDIRECT MATCH\t✅ PASS")
    else:
        semantic_match_score = embedded_strings_similarity(
            evidence_embedded,
            embed_string(candidate),
        )
        passed = semantic_match_score > EVIDENCE_SEMANTIC_SIMILARITY_TH

        print(f"\tEvidence lexical:\t{best_lexical_score:.2f}")
        print(
            f"\tEvidence semantic:\t{semantic_match_score:.2f}  "
            f"{'✅ PASS' if passed else '❌ FAIL'}"
        )

    if not passed:
        print(f"\t\tEvidence:\t{evidence}")
        print(f"\t\tCandidate:\t{candidate}")

    return best_lexical_score, semantic_match_score, passed


def validate_field(
    field_name: str, extracted_field: ExtractedField | None, report_raw_clean: str
) -> dict[str, float | bool | None]:
    """Validate one extracted field against its evidence and the source report.

    Args:
        field_name: Name of the schema field being validated.
        extracted_field: Extracted value and supporting evidence, if available.
        report_raw_clean: Normalized raw report text.

    Returns:
        Validation metrics, or an empty dictionary for unpopulated fields.
    """
    print("\nField name:\t", field_name)
    if extracted_field is None:
        return {}
    if extracted_field.value is not None and extracted_field.evidence is None:
        print(f"WARNING: existing value but missing evidence for {field_name}")

    if extracted_field.value is None or extracted_field.evidence is None:
        return {}

    value = normalize_string(extracted_field.value)
    evidence = normalize_string(extracted_field.evidence)
    value_evidence_score, value_evidence_pass = validate_field_value(value, evidence)
    evidence_lexical_score, evidence_semantic_score, evidence_grounding_pass = (
        validate_field_evidence(evidence, report_raw_clean)
    )

    field_result = {
        "value_evidence_score": value_evidence_score,
        "value_evidence_pass": value_evidence_pass,
        "evidence_lexical_score": evidence_lexical_score,
        "evidence_semantic_score": evidence_semantic_score,
        "evidence_grounding_pass": evidence_grounding_pass,
    }

    return field_result


def validate_extraction_completeness(
    report_extracted: PathologyExtraction,
) -> tuple[float, float]:
    """Calculate field completeness and evidence coverage metrics.

    Args:
        report_extracted: The extracted pathology report object.

    Returns:
        A tuple of (field_completeness, evidence_coverage) where field_completeness
        is the ratio of fields with values and evidence_coverage is the ratio of
        fields with evidence.
    """
    expected_fields = len(report_extracted.model_dump().values())
    fields_with_value = sum(
        getattr(report_extracted, field_name).value is not None
        for field_name in PathologyExtraction.model_fields
    )

    fields_with_evidence = sum(
        getattr(report_extracted, field_name).evidence is not None
        for field_name in PathologyExtraction.model_fields
    )

    field_completeness = fields_with_value / expected_fields
    evidence_coverage = fields_with_evidence / expected_fields

    return field_completeness, evidence_coverage


def validate_extraction(
    report_id: str, report_raw: str, report_extracted: PathologyExtraction
) -> tuple[dict[str, float | str], list[dict[str, float | bool | str | None]]]:
    """Validate the extracted report and return summary metrics and per-field results.

    Args:
        report_id: Unique identifier for the report.
        report_raw: The raw report text.
        report_extracted: The extracted pathology report object.

    Returns:
        A tuple of (validation_result, field_results) where validation_result
        contains summary metrics (field_coverage, evidence_coverage, value_evidence_consistency,
        evidence_report_grounding) and field_results is a list of per-field metrics.
    """

    # Validate extraction completeness (field completeness and evidence coverage)
    field_coverage, evidence_coverage = validate_extraction_completeness(
        report_extracted
    )

    value_evidence_matches = []
    evidence_report_matches = []

    field_results_list = []

    # For each field validate value-evidence consistency and evidence-report grounding
    report_raw_clean = normalize_string(report_raw)
    for field_name in PathologyExtraction.model_fields:
        extracted_field = getattr(report_extracted, field_name)

        if extracted_field.value is None or extracted_field.evidence is None:
            continue

        field_result = validate_field(field_name, extracted_field, report_raw_clean)
        record = {
            "report_id": report_id,
            "field_name": field_name,
            **field_result,
        }
        field_results_list.append(record)

        if field_result["value_evidence_pass"]:
            value_evidence_matches.append(field_name)
        if field_result["evidence_grounding_pass"]:
            evidence_report_matches.append(field_name)

    # Calculate ratios based on populated fields
    fields_with_value_and_evidence = len(field_results_list)

    # Report a score for value-evidence consistency evidence-report grounding
    value_evidence_consistency = (
        len(value_evidence_matches) / fields_with_value_and_evidence
        if fields_with_value_and_evidence
        else 0.0
    )
    evidence_report_grounding = (
        len(evidence_report_matches) / fields_with_value_and_evidence
        if fields_with_value_and_evidence
        else 0.0
    )

    validation_result = {
        "report_id": report_id,
        "field_coverage": field_coverage,
        "evidence_coverage": evidence_coverage,
        "value_evidence_consistency": value_evidence_consistency,
        "evidence_report_grounding": evidence_report_grounding,
    }

    print("\nValidation results overview")
    for key, item in validation_result.items():
        print(f"{key}\t{item}")

    return validation_result, field_results_list


def run_confidence_validation(
    extraction_files: list[Path], reports_raw_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run confidence validation pipeline on extracted reports.

    Args:
        extraction_files: List of Path objects to extracted JSON files.
        reports_raw_df: DataFrame containing raw report texts with 'patient_filename'
            and 'text' columns.

    Returns:
        A tuple of (validation_overview, field_results) where validation_overview
        is a DataFrame of summary metrics per report and field_results is a
        DataFrame of per-field validation results.
    """
    validation_results = []
    all_field_results = []

    for file in extraction_files:
        report_id = file.stem
        print(f"\n========== Validating\t{report_id} ========== ")

        report_raw = load_raw_report(reports_raw_df, report_id)

        report_extracted = load_and_validate_result(file)

        if report_raw is not None and report_extracted is not None:
            validation_result, field_results_list = validate_extraction(
                report_id, report_raw, report_extracted
            )

            validation_results.append(validation_result)

            all_field_results.extend(field_results_list)

    validation_overview = pd.DataFrame(validation_results)
    field_results = pd.DataFrame(all_field_results)

    return validation_overview, field_results
