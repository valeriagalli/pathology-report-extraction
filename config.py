"""Shared paths and constants for the pathology extraction pipeline."""

from pathlib import Path

from sentence_transformers import SentenceTransformer

from schema import PathologyExtraction

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "dataset"
REPORTS_FP = DATA_DIR / "TCGA_Reports.csv"
RESULTS_DIR = ROOT_DIR / "results"

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
RAND_SUBSET = 150
RAND_SEED = 42

# ---------------------------------------------------------------------------
# Raw text processing
# ---------------------------------------------------------------------------
MIN_TEXT_LEN = 10
MAX_SEGMENT_LEN = 200

# ---------------------------------------------------------------------------
# Model prompt
# ---------------------------------------------------------------------------
PROMPT = """
You are extracting structured clinical information from pathology reports.

The report may contain OCR artifacts such as typos, garbled characters, or
formatting noise from scanned PDFs. Correct an obvious OCR artifact only when
the intended text is unambiguous from the surrounding context. Do not infer
clinical information that is not supported by the report.

Extract the following information:

- primary diagnosis
- tumor site
- tumor grade
- pathological stage
- surgical margin status

For each field:

- Return the extracted value only when it is explicitly supported by the report.
- Do not infer information that is not stated in the report.
- If the information is absent or cannot be determined, return null.
- Provide the relevant text from the report as evidence for every extracted value.
- Preserve the meaning and terminology of the original report.
- Do not use external knowledge to fill missing information.

Return the result as valid JSON using exactly the following structure:

{
  "diagnosis": {
    "value": null,
    "evidence": null
  },
  "tumor_site": {
    "value": null,
    "evidence": null
  },
  "grade": {
    "value": null,
    "evidence": null
  },
  "stage": {
    "value": null,
    "evidence": null
  },
  "margins": {
    "value": null,
    "evidence": null
  }
}

Use exactly these field names and do not add or remove fields.

"""

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
MODELS = {
    "gpt_oss": {
        "name": "openai/gpt-oss-120b",
        "prompt": PROMPT,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "pathology_extraction",
                "strict": True,
                "schema": PathologyExtraction.model_json_schema(),
            },
        },
        "extraction_dir": RESULTS_DIR / "gpt_oss" / "extraction",
        "review_dir": RESULTS_DIR / "gpt_oss" / "review",
        "validation_dir": RESULTS_DIR / "gpt_oss" / "validation",
    },
    "gpt_oss_20": {
            "name": "openai/gpt-oss-20b",
            "prompt": PROMPT,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "pathology_extraction",
                    "strict": True,
                    "schema": PathologyExtraction.model_json_schema(),
                },
            },
            "extraction_dir": RESULTS_DIR / "gpt_oss_20" / "extraction",
            "review_dir": RESULTS_DIR / "gpt_oss_20" / "review",
            "validation_dir": RESULTS_DIR / "gpt_oss_20" / "validation",
        },
}

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
STR_EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
VALUE_EVIDENCE_SIMILARITY_TH = 0.75
EVIDENCE_SEMANTIC_SIMILARITY_TH = 0.75

# ---------------------------------------------------------------------------
# Settings for human review
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS = {
    "evidence_grounding": 0.4,
    "value_evidence_consistency": 0.3,
    "model_agreement": 0.3,
}
EVIDENCE_REPORT_GROUNDING_TH = 0.70
VALUE_EVIDENCE_CONSISTENCY_TH = 0.70
MAX_ERROR_MSG_LEN = 200
