## Limitations

**Confidence calibration is based on a small, manually-reviewed sample, not a labeled dataset.**
There's no ground-truth-labeled version of this corpus to compute precision/recall against. Thresholds (e.g. `VALUE_EVIDENCE_SIMILARITY_TH`, `EVIDENCE_SEMANTIC_SIMILARITY_TH`) were set by manually inspecting a small number of real extractions and judging faithfulness by eye, not by statistical calibration against a larger labeled set.

**Value/evidence matching struggles with short, code-like fields.**
Semantic embedding similarity works well for free-text fields (diagnosis, tumor site) but performs poorly on short structured tokens like grade/stage codes (e.g. "G3", "pT1"), where exact or near-exact character matching is more reliable. The current implementation combines lexical and semantic matching for evidence grounding, and folds this into a composite score alongside value/evidence consistency and, when available, cross-model agreement.

**Grounding checks operate on local text windows, not the full document.**
The evidence-grounding check compares a claimed quote against a small window of nearby text, not the entire report. This was a deliberate design choice, but it also means the check can correctly catch cases where a model stitches together phrases from two non-adjacent parts of a report into one fabricated evidence quote (observed during development), a case where the model's cited evidence doesn't correspond to any real contiguous span of text.

**Composite score weights are placeholders, not independently validated.**
The weighting between grounding, value/evidence consistency, and model agreement in the composite score is a reasonable default chosen for demonstration, not a domain-informed decision. In a real deployment, these weights, and what counts as an acceptable review threshold, should be set and iterated on by domain experts, not by the engineer building the pipeline.

**Cross-model agreement doesn't resolve disagreement, it surfaces it.**
When two models disagree on a field, the system doesn't attempt to pick a "winner" based on composite score, a self-consistency measure isn't a reliable arbiter of correctness across models. Disagreement is treated as its own review trigger, with both values shown to the human reviewer.

**Structured-output reliability varies significantly by model.**
`openai/gpt-oss-120b` reliably supports strict JSON-schema enforcement. During development, `qwen/qwen3.6-27b` (a Groq preview model) failed structured-output validation entirely under the same schema, succeeding on short reports but failing on longer, more complex ones. Requiring structured output enforcement limits model availability, at least on Groq.

**No hosted deployment.**
The FastAPI wrapper runs and is tested locally, but hasn't been deployed to any cloud environment yet. The natural next step would be Cloud Run or AWS Lambda. The API also has no authentication and hasn't been tested under concurrent load, appropriate for a local demonstration, not a production deployment as-is.

**Test coverage is targeted, not exhaustive.**
Unit tests cover the core validation, scoring, and review logic, the functions where real bugs were found and fixed during development. Orchestration code (`pipeline.py`) and the LLM-calling code itself (`extraction.py`) are not unit tested; testing them meaningfully would require mocking the API client.

**Uses a pre-cleaned, OCR'd dataset rather than raw PDFs.**
Raw TCGA pathology reports are only available as scanned PDF images; this project uses TCGA-Reports (Kefeli & Tatonetti, 2024), an already-OCR'd, published version. A separate PDF text-ingestion utility (`pdf_ingest.py`) is included for text-based (non-scanned) PDF input.