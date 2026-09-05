## Features

- **Structured extraction**: pulls diagnosis, tumor site, grade, stage, and margin status from unstructured pathology report text using an LLM (Groq API), with each field paired with a verbatim source quote as evidence.
- **Grounding-based confidence, not self-reported**: each extraction is checked for whether its cited evidence actually appears in the source report (lexical + semantic matching), and whether the extracted value is consistent with its own evidence.
- **Composite confidence score**: combines grounding, value/evidence consistency, and (when available) cross-model agreement into one configurable, weighted score per field. 
Weights are configurable parameters, meant to be set by domain experts rather than hardcoded engineering defaults.
- **Human-in-the-loop review queues**: two-tier review output: a report-level triage list with plain-language reasons for review, and a field-level detail view for drilling into flagged cases.
- **Multi-model comparison and agreement analysis**: runs extraction through two independent models and flags fields where they disagree. More models are possible depending on availability.
- **PDF text ingestion**: a separate utility (`pdf_ingest.py`) for extracting text from text-based PDF pathology reports, for cases where input isn't already available as clean CSV text.
- **REST API**: a FastAPI wrapper exposing extraction and confidence scoring as a `/extract` endpoint, so the pipeline can be called by other services rather than only run as a batch script.
- **Web interface**: a minimal HTML form at `/` for pasting report text directly and viewing extraction results in the browser, no client scripting required.