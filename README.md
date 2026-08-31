# Pathology Report Extraction

Structured field extraction from unstructured pathology reports using LLMs, with grounding-based confidence scoring to flag low-confidence extractions for human review.


## Installation (Windows)

### PowerShell

Clone the repository:

```bash
git clone https://github.com/<your_username>/pathology-report-extraction.git
cd pathology-report-extraction
```

Create a virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
pip install -r requirements.txt
```

For development (linting, tests): 
```powershell
pip install -r requirements_dev.txt
```

## Dataset

Download TCGA_Reports.csv.zip from https://github.com/tatonetti-lab/tcga-path-reports and unzip it into dataset/. 
This is a pre-cleaned version of TCGA pathology reports (Kefeli & Tatonetti, 2024, Patterns), originally scanned PDFs, processed via AWS Textract (optical character recognition)

## Usage
Set your Groq API key (get one at console.groq.com, no credit card required):

```powershell
$env:GROQ_API_KEY = "your-key-here"
```

Run the full pipeline:

```powershell
python pipeline.py
```

This will, for each model configured in `config.py` (`MODELS`):
1. Extract structured fields from a random sample of pathology reports (diagnosis, tumor site, grade, stage, margins), each paired with a verbatim evidence quote from the source report.
2. Score each extraction for grounding (is the evidence actually in the report?) and value/evidence consistency (does the value faithfully reflect its own evidence?).
3. Compute a composite confidence score per field and per report.
4. Generate two review queues: `review_queue_all.csv` (report-level, flags reports needing human review and why) and `review_queue_field_level.csv` (field-level detail for flagged reports).

Then it compares extractions across both models and writes `results/model_agreement.csv`, showing where the models agree or disagree on each field.

All outputs are written under `results/<model_name>/` and `results/model_agreement.csv` (gitignored, regenerated on each run).

To adjust the sample size or which models are compared, edit `RAND_SUBSET` and `MODELS` in `config.py`.


## Features

- **Structured extraction**: pulls diagnosis, tumor site, grade, stage, and margin status from unstructured pathology report text using an LLM (Groq API), with each field paired with a verbatim source quote as evidence.
- **Grounding-based confidence, not self-reported**: each extraction is checked for whether its cited evidence actually appears in the source report (lexical + semantic matching), and whether the extracted value is consistent with its own evidence.
- **Composite confidence score**: combines grounding and value/evidence consistency into one configurable, weighted score per field. Weights are configurable parameters (e.g., to be set by domain experts like Clinical Informatics Lead).
- **Human-in-the-loop review queues**: two-tier review output: a report-level triage list with plain-language reasons for review, and a field-level detail view for drilling into flagged cases.
- **Multi-model comparison and agreement analysis**: runs extraction through two independent models and flags fields where they disagree. More models are possible depending on availability.
- **PDF text ingestion**: a separate utility (`pdf_ingest.py`) for extracting text from text-based PDF pathology reports, for cases where input isn't already available as clean CSV text.

## Limitations

**Confidence calibration is based on a small, manually-reviewed sample, not a labeled dataset.**
There's no ground-truth-labeled version of this corpus to compute precision/recall against. Thresholds (e.g. `VALUE_EVIDENCE_SIMILARITY_TH`, `EVIDENCE_SEMANTIC_SIMILARITY_TH`) were set by manually inspecting a small number of real extractions and judging faithfulness by eye, not by statistical calibration against a larger labeled set. With more time, this would need a proper annotated validation set.

**Composite score weights are placeholders, not clinically validated.**
The weighting between grounding and value/evidence consistency in the composite score is a reasonable default I chose for demonstration, not a clinically informed decision. In a real deployment, these weights (and what counts as an acceptable threshold) should be set and iterated on by clinical domain experts — e.g. a Clinical Informatics Lead, per the role description — not by the engineer building the pipeline.

**Value/evidence matching struggles with short, code-like fields.**
Semantic embedding similarity works well for free-text fields (diagnosis, tumor site) but performs poorly on short structured tokens like grade/stage codes (e.g. "G3", "pT1"), where exact or near-exact character matching is actually more reliable. The current implementation uses hybrid lexical+semantic.

**Cross-model agreement doesn't resolve disagreement, it surfaces it.**
When two models disagree on a field, the system doesn't attempt to pick a "winner" based on composite score — a self-consistency measure isn't a reliable arbiter of correctness across models. Disagreement is treated as its own review trigger, with both values shown to the human reviewer.

**Structured-output reliability varies significantly by model.**
`openai/gpt-oss-120b` reliably supports strict JSON-schema enforcement. During development, `qwen/qwen3.6-27b` (a Groq preview model) failed structured-output validation entirely under the same schema, succeeding on short reports but failing on longer, more complex ones — this became a data point about model selection, not just an obstacle.

**No deployment.**
Given the one-week scope, this was built and validated as a local pipeline, not deployed. The natural next step would be a lightweight FastAPI wrapper exposing an endpoint that accepts report text and returns extraction + confidence output, deployed on a small Lambda or Cloud Run instance. Deliberately out of scope this week in favor of extraction accuracy and confidence-scoring rigor.

**Limited unit test coverage.**
Not yet implemented, given time constraints.

**Uses a pre-cleaned, OCR'd dataset rather than raw PDFs.**
Raw TCGA pathology reports are only available as scanned PDF images; this project uses TCGA-Reports (Kefeli & Tatonetti, 2024), an already-OCR'd, published version, so that development time went toward extraction and confidence logic rather than re-solving OCR. A separate PDF text-ingestion utility (`pdf_ingest.py`) is included for text-based (non-scanned) PDF input.


## Project structure
```text
pathology-report-extraction/
├── dataset/
│   └── TCGA_Reports.csv              # gitignored, fetch separately
├── results/                           # gitignored, generated outputs
│   ├── <model_name>/
│   │   ├── extraction/
│   │   │   ├── failed_extractions.csv
│   │   │   └── <patient_id>.json
│   │   ├── review/
│   │   │   ├── review_queue_all.csv
│   │   │   └── review_queue_field_level.csv
│   │   └── validation/
│   │       ├── validation_overview.csv
│   │       └── field_results.csv
│   └── model_agreement.csv
├── test_fixtures/
│   ├── blank_test.pdf
│   └── test_report.pdf
├── .gitignore
├── config.py
├── extraction.py
├── model_agreement.py
├── pdf_ingestion.py
├── pipeline.py
├── README.md
├── requirements.txt
├── review.py
├── schema.py
├── validation.py
└── text_processing.py
```

## Roadmap

### v0.1 — Single-model extraction
- [x] PDF text ingestion
- [x] Extraction schema
- [x] LLM extraction agent (direct Groq API)
- [x] Validation and human-in-the-loop review
- [x] End-to-end pipeline over TCGA-Reports datasetgit li

### v0.2 — Multi-model extraction
- [x] Multi-model extraction support
- [x] Cross-model agreement analysis
- [x] Composite confidence score
- [x] Integrate model agreement into review workflow
- [ ] Unit test coverage


## Status
Functional end-to-end pipeline: extraction, confidence scoring, and human-review queues working across two models. 
Unit tests and model-agreement review integration in progress.