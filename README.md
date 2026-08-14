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
venv\Scripts\Activate.ps1
```

Install the project:

```powershell
pip install -r requirements.txt
```

## Dataset

Download TCGA_Reports.csv.zip from https://github.com/tatonetti-lab/tcga-path-reports and unzip it into dataset/. 
This is a pre-cleaned version of TCGA pathology reports (Kefeli & Tatonetti, 2024, Patterns), originally scanned PDFs, processed via AWS Textract (optical character recognition)


## Usage




## Features


## Project structure
```text
pathology-report-extraction/
├── dataset/
│   └── TCGA_Reports.csv              # gitignored, fetch separately
├── results/                           # gitignored, generated outputs
│   ├── <model_name>/
│   │   ├── extractions/
│   │   │   ├── failed_extractions.csv
│   │   │   └── <patient_id>.json
│   │   └── validation/
│   │       ├── validation_overview.csv
│   │       ├── field_results.csv
│   │       ├── review_queue_all.csv
│   │       └── review_queue_field_level.csv
│   └── agreement/
│       └── model_agreement.csv
├── test_fixtures/
│   ├── test_report.pdf
│   └── blank_test.pdf
├── pdf_ingest.py
├── report.py
├── extractor.py
├── confidence.py
├── model_agreement.py
├── review.py
├── schema.py
├── config.py
├── pipeline.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Roadmap

### v0.1 — Single-model extraction
- [x] PDF text ingestion
- [x] Extraction schema
- [x] LLM extraction agent (direct Groq API)
- [x] Validation and human-in-the-loop review
- [x] End-to-end pipeline over TCGA-Reports dataset
- [ ] Unit test coverage

### v0.2 — Multi-model extraction
- [x] Multi-model extraction support
- [x] Cross-model agreement analysis
- [ ] Composite confidence score
- [ ] Integrate model agreement into review workflow
- [ ] Organize model-specific and cross-model results


## Status
Early development, not all modules built/tested yet