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
├── results/
│   └── directAPI/                    # gitignored, generated outputs
│       ├── extractions/
│       │   ├── failed_extractions.csv
│       │   └── <patient_id>.json
│       │   └── ...
│       └── validation/
│           ├── validation_overview.csv
│           ├── field_results.csv
│           └── ...
├── test_fixtures/
│   ├── test_report.pdf
│   └── blank_test.pdf
├── pdf_ingest.py
├── report.py
├── extractor.py
├── confidence.py
├── schema.py
├── config.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Roadmap

### v0.1 (in progress)
- [x] PDF text ingestion
- [x] Extraction schema
- [x] LLM extraction agent (direct Groq API)
- [x] Grounding-based confidence scoring
- [ ] Review queue
- [ ] End-to-end pipeline over TCGA-Reports dataset


## Status
Early development, not all modules built/tested yet






