"""
Common pytest fixtures for testing the pathology_extraction package.
"""

import pytest

from pathology_extraction.schema import ExtractedField, PathologyExtraction


@pytest.fixture
def well_grounded_report():
    """A report where every populated field is exactly grounded in its evidence."""
    report = PathologyExtraction(
        diagnosis=ExtractedField(
            value="High grade muscle invasive urothelial cell carcinoma",
            evidence="High grade muscle invasive urothelial cell carcinoma",
        ),
        tumor_site=ExtractedField(
            value="Right bladder wall", evidence="Right bladder wall"
        ),
        grade=ExtractedField(value="G3", evidence="pT3bG3"),
        stage=ExtractedField(value="pT3b", evidence="pT3bG3"),
        margins=ExtractedField(value=None, evidence=None),
    )
    return report


@pytest.fixture
def non_grounded_report():
    """A report where some populated field lack the corresponding evidence.

    Based on extraction output for TCGA-4V-A9QX.57310D54-B73F-472F-90BC-D83DB3B7C210
    (GPT-OSS-120B). The margins field's evidence splices two non-adjacent
    sentences from the source report into one fabricated quote."""

    report = PathologyExtraction(
        diagnosis=ExtractedField(
            value="Type AB thymoma",
            evidence="Conclusion : Type AB thymoma in 19 cm major axis ,"
            " with widely invasive invasion in the lung parenchyma stage 3 "
            "according to the classification of Masaoka resection. surgical complete.",
        ),
        tumor_site=ExtractedField(
            value="Thymus",
            evidence="Macroscopic examination : Piece weighing 1208 g thymectomy fresh"
            " and measuring 19 x 17 x 8 cm.",
        ),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(
            value="Stage 3 (Masaoka)",
            evidence="Conclusion : Type AB thymoma in 19 cm major axis ,"
            " with widely invasive invasion in the lung parenchyma stage 3 "
            "according to the classification of Masaoka resection.",
        ),
        margins=ExtractedField(
            value="Negative",
            evidence="The limits of resection inked in green appear "
            "microscopically healthy. surgical complete.",
        ),
    )
    return report


@pytest.fixture
def non_grounded_report_raw_text():
    """Raw text of a report where some populated fields have evidence not grounded.
    (TCGA-4V-A9QX.57310D54-B73F-472F-90BC-D83DB3B7C210)"""

    raw_text = (
        "Macroscopic examination : Piece weighing 1208 g thymectomy fresh and "
        "measuring 19 x 17 x 8 cm. it. extended by a pulmonary resection lingula "
        "measuring 8 X 5 X 2 cm When cut , it. is a yellowish white tumor "
        "lobulated showing necrotic and remodeling. a small yellowish nodule. "
        "Lymph node latero- tracheal top right measuring 1.5 cm in diameter. "
        "Microscopic examination : 1) Thymectomy : Many samples were taken "
        "( 1A to 1D ) The tumor has an architecture. lobulated It comprises an "
        "epithelial cell proliferation primarily. fusiform These cells are "
        "grouped together in small bundles . They are arranged. also small "
        "beaches. Lymphocyte contigent is also abundant enough. mixed with "
        "epithelial contigent. Presence of some beaches fibrosis with "
        "remodeling. inflammatory with tablecloths foamy histiocytes . No "
        "outbreak of differentiation. medulla. Presence of a range of tumor "
        "necrosis Presence of some clear spaces. perivascular (1B) . The tumor "
        "is highly infiltrative and invades the lung parenchyma. (1E) The "
        "limits of resection inked in green appear microscopically healthy. "
        "Some areas appear much richer in epithelial cells with a. scarcity of "
        "accompanying lymphocytes. After immunohistochemistry epithelial cells "
        "express cytokeratin KL1. and focally CD20. However, they are negative "
        "for CD5 and CD117. 2) Lymph node latÃ©rotrachÃ©al top right : This is "
        "a little modified lymph node No histological evidence of. malignancy. "
        "Conclusion : Type AB thymoma in 19 cm major axis , with widely "
        "invasive invasion in the. lung parenchyma stage 3 according to the "
        "classification of Masaoka resection. surgical complete."
    )

    return raw_text


@pytest.fixture
def field_results():
    """Validation results for the non-grounded report
    (TCGA-4V-A9QX.57310D54-B73F-472F-90BC-D83DB3B7C210)."""

    field_results = {
        "diagnosis": {
            "value_evidence_score": 1.0,
            "evidence_semantic_score": 0.96,
            "agreement": 1.0,
            "composite_score": 0.99,
        },
        "tumor_site": {
            "value_evidence_score": 0.41,
            "evidence_semantic_score": 0.99,
            "agreement": 1.0,
            "composite_score": 0.82,
        },
        "grade": {
            "value_evidence_score": None,
            "evidence_semantic_score": None,
            "agreement": None,
            "composite_score": None,
        },
        "stage": {
            "value_evidence_score": 0.32,
            "evidence_semantic_score": 0.97,
            "agreement": 0.5,
            "composite_score": 0.63,
        },
        "margins": {
            "value_evidence_score": 0.06,
            "evidence_semantic_score": 0.50,
            "agreement": 0.5,
            "composite_score": 0.37,
        },
    }

    return field_results


@pytest.fixture
def field_results_single_model():
    """Validation results for the non-grounded report
    (TCGA-4V-A9QX.57310D54-B73F-472F-90BC-D83DB3B7C210).
    with model agreement removed and composite score recalculated."""

    field_results_single_model = {
        "diagnosis": {
            "value_evidence_score": 1.0,
            "evidence_semantic_score": 0.96,
            "composite_score": 0.98,
        },
        "tumor_site": {
            "value_evidence_score": 0.41,
            "evidence_semantic_score": 0.99,
            "composite_score": 0.74,
        },
        "stage": {
            "value_evidence_score": 0.32,
            "evidence_semantic_score": 0.97,
            "composite_score": 0.69,
        },
        "margins": {
            "value_evidence_score": 0.06,
            "evidence_semantic_score": 0.50,
            "composite_score": 0.31,
        },
    }

    return field_results_single_model
