"""
Test suite for the validation module.
"""

from pathology_extraction.config import (
    EVIDENCE_SEMANTIC_SIMILARITY_TH,
    VALUE_EVIDENCE_SIMILARITY_TH,
)
from pathology_extraction.schema import ExtractedField, PathologyExtraction
from pathology_extraction.validation import (
    validate_extraction_completeness,
    validate_field_evidence,
    validate_field_value,
)


def test_partial_evidence_coverage():
    """Test that the evidence coverage is calculated correctly
    when some fields have missing evidence."""
    report = PathologyExtraction(
        diagnosis=ExtractedField(value="...", evidence="..."),
        tumor_site=ExtractedField(value="...", evidence="..."),
        grade=ExtractedField(value="...", evidence="..."),
        stage=ExtractedField(
            value="...", evidence=None
        ),  # value present, evidence missing
        margins=ExtractedField(
            value="...", evidence=None
        ),  # value present, evidence missing
    )
    field_completeness, evidence_coverage = validate_extraction_completeness(report)
    assert field_completeness == 1.0
    assert evidence_coverage == 0.6


def test_no_field_value():
    """Test that the field completeness and evidence coverage are both 0.0
    when all fields have missing values."""
    report = PathologyExtraction(
        diagnosis=ExtractedField(value=None, evidence=None),
        tumor_site=ExtractedField(value=None, evidence=None),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value=None, evidence=None),
        margins=ExtractedField(value=None, evidence=None),
    )
    field_completeness, evidence_coverage = validate_extraction_completeness(report)
    assert field_completeness == 0.0
    assert evidence_coverage == 0.0


def test_full_completeness_and_coverage():
    """Test that the field completeness and evidence coverage are both 1.0
    when all fields have values and evidence."""
    report = PathologyExtraction(
        diagnosis=ExtractedField(value="...", evidence="..."),
        tumor_site=ExtractedField(value="...", evidence="..."),
        grade=ExtractedField(value="...", evidence="..."),
        stage=ExtractedField(value="...", evidence="..."),
        margins=ExtractedField(value="...", evidence="..."),
    )
    field_completeness, evidence_coverage = validate_extraction_completeness(report)
    assert field_completeness == 1.0
    assert evidence_coverage == 1.0


def test_validate_field_value_pass(well_grounded_report):
    """Test that the field value validation passes
    when the value is well-grounded in the evidence."""
    similarity_score, passed = validate_field_value(
        well_grounded_report.diagnosis.value, well_grounded_report.diagnosis.evidence
    )
    assert similarity_score == 1.0
    assert passed is True


def test_validate_field_value_not_pass(non_grounded_report):
    """Test that the field value validation fails
    when the value is not grounded in the evidence."""
    similarity_score, passed = validate_field_value(
        non_grounded_report.tumor_site.value, non_grounded_report.tumor_site.evidence
    )
    assert similarity_score < VALUE_EVIDENCE_SIMILARITY_TH
    assert passed is False


def test_validate_evidence_grounding(non_grounded_report, non_grounded_report_raw_text):
    """Test that the evidence semantic validation passes
    when the evidence is well-grounded in the report text."""
    _, semantic_match_score, passed = validate_field_evidence(
        non_grounded_report.stage.evidence, non_grounded_report_raw_text
    )
    assert semantic_match_score > EVIDENCE_SEMANTIC_SIMILARITY_TH
    assert passed is True


def test_validate_no_evidence_grounding(
    non_grounded_report, non_grounded_report_raw_text
):
    """Test that the evidence semantic validation fails
    when the evidence is not grounded in the report text."""
    _, semantic_match_score, passed = validate_field_evidence(
        non_grounded_report.margins.evidence, non_grounded_report_raw_text
    )
    assert semantic_match_score < EVIDENCE_SEMANTIC_SIMILARITY_TH
    assert passed is False
