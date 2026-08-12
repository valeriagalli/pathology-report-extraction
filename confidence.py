"""Generate confidence score of the extracted fields."""

from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer, util

from config import DIRECT_API_VALIDATION_DIR
from report import detect_text_units, normalize_string
from schema import PathologyExtraction

EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
VALUE_EVIDENCE_SIMILARITY_TH = 0.75
EVIDENCE_SEMANTIC_SIMILARITY_TH = 0.75


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
    """Encode text into an embedding tensor."""
    return EMBEDDING_MODEL.encode(string, convert_to_tensor=True)


def embedded_strings_similarity(string1: object, string2: object) -> float:
    """Compare two embeddings and return a similarity score."""
    return util.cos_sim(string1, string2).item()


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
    field_name: str, extracted_field: PathologyExtraction | None, report_raw_clean: str
) -> dict[str, float | bool | None]:
    """Validate one field and return a dictionary of result metrics."""
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
) -> tuple[dict, dict]:
    """Validate the extracted report and return summary and per-field results."""

    # Validate extraction completeness (field completeness and evidence coverage)
    field_completeness, evidence_coverage = validate_extraction_completeness(
        report_extracted
    )

    value_evidence_matches = []
    evidence_report_matches = []

    field_results = {}

    # For each field validate value-evidence consistency and evidence-report grounding
    report_raw_clean = normalize_string(report_raw)
    for field_name in PathologyExtraction.model_fields:
        extracted_field = getattr(report_extracted, field_name)

        if extracted_field.value is None or extracted_field.evidence is None:
            continue

        field_result = validate_field(field_name, extracted_field, report_raw_clean)
        field_results[field_name] = field_result
        if field_result["value_evidence_pass"]:
            value_evidence_matches.append(field_name)
        if field_result["evidence_grounding_pass"]:
            evidence_report_matches.append(field_name)

    # Report a score for value-evidence consistency and evidence-report grounding
    fields_with_value_and_evidence = sum(
        getattr(report_extracted, field_name).value is not None
        and getattr(report_extracted, field_name).evidence is not None
        for field_name in PathologyExtraction.model_fields
    )
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
        "Report ID": report_id,
        "Field Completeness": field_completeness,
        "Evidence Coverage": evidence_coverage,
        "Value-Evidence Consistency": value_evidence_consistency,
        "Evidence-Report Grounding": evidence_report_grounding,
    }

    print("\nValidation results overview")
    for key, item in validation_result.items():
        print(f"{key}\t{item}")

    return validation_result, field_results


def run_confidence_validation(extraction_files, reports_raw_df):
    validation_results = []
    for file in extraction_files:
        report_id = file.stem
        print(f"\n========== Validating\t{report_id} ========== ")

        report_raw = load_raw_report(reports_raw_df, report_id)

        report_extracted = load_and_validate_result(file)

        if report_raw is not None and report_extracted is not None:
            validation_result, field_results = validate_extraction(
                report_id, report_raw, report_extracted
            )

            validation_results.append(validation_result)

            field_results_df = pd.DataFrame(field_results)
            field_results_df.to_csv(
                DIRECT_API_VALIDATION_DIR / f"{report_id}_field_results.csv"
            )

    validation_overview = pd.DataFrame(validation_results)
    validation_overview.to_csv(
        DIRECT_API_VALIDATION_DIR / "validation_overview.csv", index=False
    )
