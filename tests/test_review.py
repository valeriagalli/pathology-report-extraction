"""
Test suite for the review module.
"""

from pytest import approx

from pathology_extraction.review import (
    compute_field_composite_score,
)


def test_compute_composite_validation_score(field_results):
    tumor_site = field_results["tumor_site"]
    composite_score = compute_field_composite_score(
        tumor_site, agreement=tumor_site["agreement"]
    )
    assert composite_score == approx(0.82, abs=0.01)


def test_compute_composite_validation_score_no_field(field_results):
    grade = field_results["grade"]
    composite_score = compute_field_composite_score(grade, agreement=grade["agreement"])
    assert composite_score is None


def test_compute_composite_validation_score_single_model(field_results_single_model):
    margins = field_results_single_model["margins"]
    composite_score = compute_field_composite_score(margins, agreement=None)
    assert composite_score == approx(0.31, abs=0.01)
