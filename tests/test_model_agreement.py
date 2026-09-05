"""
Test suite for the model agreement module.
"""

import pytest

from pathology_extraction.model_agreement import (
    calculate_field_agreement,
    run_model_agreement,
)
from pathology_extraction.schema import ExtractedField, PathologyExtraction


def test_field_agreement_with_consensus():
    """Test that field agreement is calculated correctly
    swhen there is a consensus among models."""
    report_id = "test_report_consensus"
    report_model1 = PathologyExtraction(
        diagnosis=ExtractedField(
            value="Renal cell carcinoma, papillary subtype",
            evidence="4. Lower pole renal mass-right: Renal cell carcinoma, "
            "papillary subtype.",
        ),
        tumor_site=ExtractedField(
            value="right lower pole of kidney",
            evidence="Source of Specimen(s). 4: Lower Pole Renal Mass-Right",
        ),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value="pT2 Nx Mx", evidence="pTNM: T2 Nx Mx."),
        margins=ExtractedField(
            value="Free of tumor", evidence="The deep margin is free of tumor."
        ),
    )

    report_model2 = PathologyExtraction(
        diagnosis=ExtractedField(
            value="Renal cell carcinoma, papillary subtype.",
            evidence="Lower pole renal mass-right: Renal cell carcinoma, "
            "papillary subtype.",
        ),
        tumor_site=ExtractedField(
            value="Lower pole renal mass-right", evidence="Lower pole renal mass-right"
        ),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value="T2 Nx Mx", evidence="pTNM: T2 Nx Mx."),
        margins=ExtractedField(
            value="free of tumor", evidence="The deep margin is free of tumor."
        ),
    )

    model_results = [report_model1, report_model2]

    agreement_results = calculate_field_agreement(report_id, model_results)

    # Sanity checks for agreement results
    for result in agreement_results:
        assert result["consensus_value"] is not None
        assert 0 <= result["agreement"] <= 1
    assert len(agreement_results) == len(PathologyExtraction.model_fields)
    assert_agreement_is_one_of_valid_fractions(model_results, agreement_results)

    # Actual agreement checks for specific fields
    diagnosis_result = next(
        r for r in agreement_results if r["field_name"] == "diagnosis"
    )
    assert diagnosis_result["agreement"] == 1.0
    tumor_site_result = next(
        r for r in agreement_results if r["field_name"] == "tumor_site"
    )
    assert tumor_site_result["agreement"] == 0.5


def assert_agreement_is_one_of_valid_fractions(model_results, agreement_results):
    """Helper function to assert that the agreement values
    are valid fractions based on the number of models."""
    n_models = len(model_results)
    valid_fractions = [i / n_models for i in range(1, n_models + 1)]
    print(valid_fractions)

    for result in agreement_results:
        assert any(
            result["agreement"] == pytest.approx(valid_fraction)
            for valid_fraction in valid_fractions
        ), f"{result['field_name']}: agreement not in {valid_fractions}"


def test_field_agreement_one_missing_one_present():
    """Test that agreement is calculated correctly when one model
    has a missing value and another has a present value."""
    report_id = "test-report-missing-vs-present"
    report_model1 = PathologyExtraction(
        diagnosis=ExtractedField(value=None, evidence=None),
        tumor_site=ExtractedField(value=None, evidence=None),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value=None, evidence=None),
        margins=ExtractedField(value=None, evidence=None),
    )
    report_model2 = PathologyExtraction(
        diagnosis=ExtractedField(value="Renal cell carcinoma", evidence="..."),
        tumor_site=ExtractedField(value=None, evidence=None),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value=None, evidence=None),
        margins=ExtractedField(value=None, evidence=None),
    )
    model_results = [report_model1, report_model2]

    agreement_results = calculate_field_agreement(report_id, model_results)

    diagnosis_result = next(
        r for r in agreement_results if r["field_name"] == "diagnosis"
    )
    assert diagnosis_result["agreement"] == 1 / len(model_results)


def test_run_model_agreement_find_common_files(tmp_path):
    """Test that run_model_agreement correctly identifies
    common extraction files across models and returns
    a dataframe with the expected columns."""
    model1_dir = tmp_path / "model1"
    model1_dir.mkdir()
    model2_dir = tmp_path / "model2"
    model2_dir.mkdir()

    report = PathologyExtraction(
        diagnosis=ExtractedField(value="...", evidence="..."),
        tumor_site=ExtractedField(value=None, evidence=None),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value=None, evidence=None),
        margins=ExtractedField(value=None, evidence=None),
    )
    (model1_dir / "report1.json").write_text(report.model_dump_json())
    (model2_dir / "report1.json").write_text(report.model_dump_json())

    models_config = {
        "model1": {"extraction_dir": model1_dir},
        "model2": {"extraction_dir": model2_dir},
    }

    agreement_df = run_model_agreement(models_config)  # Should not raise any exceptions
    assert not agreement_df.empty
    assert set(agreement_df.columns) == {
        "report_id",
        "field_name",
        "consensus_value",
        "agreement",
    }
    assert set(agreement_df["report_id"]) == {"report1"}


def test_run_model_agreement_excludes_non_common_files(tmp_path):
    """Test that run_model_agreement only processes files
    that are common across all models."""
    model1_dir = tmp_path / "model1"
    model1_dir.mkdir()
    model2_dir = tmp_path / "model2"
    model2_dir.mkdir()

    report = PathologyExtraction(
        diagnosis=ExtractedField(value="...", evidence="..."),
        tumor_site=ExtractedField(value=None, evidence=None),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value=None, evidence=None),
        margins=ExtractedField(value=None, evidence=None),
    )
    (model1_dir / "report1.json").write_text(report.model_dump_json())
    (model1_dir / "report3.json").write_text(report.model_dump_json())
    (model2_dir / "report1.json").write_text(report.model_dump_json())
    (model2_dir / "report2.json").write_text(report.model_dump_json())

    models_config = {
        "model1": {"extraction_dir": model1_dir},
        "model2": {"extraction_dir": model2_dir},
    }

    agreement_df = run_model_agreement(models_config)  # Should not raise any exceptions
    assert set(agreement_df["report_id"]) == {"report1"}
