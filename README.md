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
pip install -e ".[dev]"
```

Note: dependencies use minimum version bounds rather than exact pins, since this is a demonstration project rather than a deployed service

## Dataset
Create a `dataset/` folder in the project root if it doesn't exist.
Download TCGA_Reports.csv.zip from https://github.com/tatonetti-lab/tcga-path-reports and unzip it into `dataset/`. 
This is a pre-cleaned version of TCGA pathology reports (Kefeli & Tatonetti, 2024, Patterns), originally scanned PDFs, processed via AWS Textract (optical character recognition)

## Usage
Set your Groq API key (get one at console.groq.com free of charge):

```powershell
$env:GROQ_API_KEY = "your-key-here"
```

Run the full pipeline:

```powershell
python -m pathology_extraction.pipeline
```

This will, for each model configured in `config.py` (`MODELS`):
1. Extract structured fields from a random sample of pathology reports (diagnosis, tumor site, grade, stage, margins), each paired with a verbatim evidence quote from the source report.
2. Score each extraction for grounding (is the evidence actually in the report?) and value/evidence consistency (does the value faithfully reflect its own evidence?).
3. Compute a composite confidence score per field and per report.
4. Generate two review queues: `review_queue_all.csv` (report-level, flags reports needing human review and why) and `review_queue_field_level.csv` (field-level detail for flagged reports).

Then it compares extractions across both models and writes `results/model_agreement.csv`, showing where the models agree or disagree on each field.

All outputs are written under `results/<model_name>/` and `results/model_agreement.csv` (gitignored, regenerated on each run).

To adjust the sample size or which models are compared, edit `RAND_SUBSET` and `MODELS` in `config.py`.

### Running the API

Terminal 1, start the server:
```powershell
.venv\Scripts\Activate.ps1
$env:GROQ_API_KEY = "your-key-here"
uvicorn pathology_extraction.api:app --reload
```

Terminal 2, test it with a real report:
```powershell
.venv\Scripts\Activate.ps1
python examples/call_api.py
```

The endpoint returns extracted fields (diagnosis, tumor site, grade, stage, margins) each paired with a confidence score based on evidence grounding and value/evidence consistency.
Note this uses a single model (no cross-model agreement), since agreement requires comparing multiple models' output, which isn't meaningful for a single synchronous request.

For quick exploration of the endpoint (schema, simple manual tests), visit `http://127.0.0.1:8000/docs`.
Note: testing `/extract` with real report text through the `/docs` UI requires manually escaping newlines in the pasted JSON; `examples/call_api.py` is the recommended way to test with real data.


## Features

- **Structured extraction**: pulls predefined fields from unstructured pathology report text using an LLM (Groq API), with each field paired with a verbatim source quote as evidence.
- **Grounding-based confidence, not self-reported**: each extraction is checked for whether its cited evidence actually appears in the source report, and whether the extracted value is consistent with its own evidence.
- **Composite confidence score**: combines grounding, value/evidence consistency, and cross-model agreement into one weighted score per field. 
- **Human-in-the-loop review queues**: a report-level sorted list of extractions that need reviewing and a field-level detail view.
- **Multi-model comparison and agreement analysis**: runs extraction through multiple models and flags fields where they disagree.
- **PDF text ingestion**: a standalone utility for extracting text from text-based PDF pathology reports, for input not already available as clean text.
- **REST API**: a FastAPI wrapper exposing extraction and confidence scoring as a `/extract` endpoint.


## Project structure
```text
pathology-report-extraction/
├── dataset/
├── docs/
│   └── limitations.md
│   ├── roadmap.md
├── results/
├── src/
│   └── pathology_extraction/
│       ├── __init__.py
│       ├── api.py
│       ├── config.py
│       ├── extraction.py
│       ├── model_agreement.py
│       ├── pdf_ingest.py
│       ├── pipeline.py
│       ├── review.py
│       ├── schema.py
│       ├── text_processing.py
│       └── validation.py
├── tests/
│   ├── fixtures/
│   │   ├── blank_test.pdf
│   │   └── test_report.pdf
│   ├── test_api.py
│   ├── test_review.py
│   └── test_validation.py
├── .gitignore
├── pyproject.toml
└── README.md
```


## Status
Core validation, scoring, and API logic covered by unit tests; orchestration and LLM-calling code intentionally untested.


## Documentation

- [Limitations and design tradeoffs](docs/limitations.md)
- [Project roadmap](docs/roadmap.md)