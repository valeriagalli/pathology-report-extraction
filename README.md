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
├── dataset
│   └── TCGA_Reports.csv      # gitignored, fetch separately
├── test_fixtures/
│   ├── test_report.pdf
│   └── blank_test.pdf
├── requirements.txt
├── pdf_ingest.py
├── .gitignore
└── README.md
```

## Roadmap

### v0.1 (in progress)
- [x] PDF text ingestion
- [ ] Extraction schema
- [ ] LLM extraction agent
- [ ] Grounding-based confidence scoring
- [ ] End-to-end pipeline over TCGA-Reports dataset


## Status
Early development, not all modules built/tested yet






