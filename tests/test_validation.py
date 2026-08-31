"""
Test module for the validation module.
"""

from pathology_extraction.schema import ExtractedField, PathologyExtraction
from pathology_extraction.validation import validate_extraction_completeness


def test_partial_evidence_coverage():
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
