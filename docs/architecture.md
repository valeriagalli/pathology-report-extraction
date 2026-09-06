# Architecture and Design Decisions

Rationale behind key design choices. See the README for what the system does;
this document explains why it's built this way.

## Direct API calls, not an orchestration framework

Extraction uses direct Groq API calls rather than LangChain/LlamaIndex.

Frameworks add value when chaining multiple steps or swapping providers
frequently; for a single extraction call per report, they add a dependency
without a corresponding benefit.

## Grounding-based confidence, not self-reported

LLM self-reported confidence is poorly calibrated, models tend to report high
confidence regardless of correctness. 

Confidence is instead computed
independently: whether cited evidence appears in the source report, and
whether the value is consistent with that evidence. This catches a real
failure mode self-reported confidence can't: schema-valid output that is
factually wrong.

Two checks exist because they catch different failures: evidence grounding
catches fabricated quotes; value/evidence consistency catches unfaithful
paraphrasing of real evidence.

## Grounding uses local text windows, not whole-document matching

Comparing evidence against an entire multi-page report dilutes semantic
similarity, even exact matches score low. Evidence is instead matched against
a local window of nearby sentences.

Tradeoff: this can miss evidence spliced together from distant, non-adjacent 
parts of a report, a known limitation.

## Field-type-aware matching

Semantic similarity works well for free-text fields (diagnosis, tumor site)
but performs poorly on short, code-like fields (grade, stage), where
character-level matching is more reliable. 

Both scores are computed; the composite score weights them per field type.

## Composite score computed at review time

Composite score requires cross-model agreement data, which only exists once
all models have run. It's computed in the review layer, not during per-model
validation, where agreement isn't yet available.

Weights are configurable, since setting them is a domain decision, not an engineering one.

## Model disagreement is a review trigger, not auto-resolved

Composite score measures self-consistency, not cross-model correctness, a
model can be internally consistent and still wrong. 

When models disagree, both values are surfaced to the reviewer
rather than a model being automatically selected.

## Minimal web interface alongside the API

Swagger UI's auto-generated docs require manually escaping newlines for
multi-line report text. 

A single HTML route reusing the existing `/extract`
endpoint avoids this without adding a separate frontend project.

## Cloud Run deployment via Dockerfile

The initial buildpacks-based deploy built successfully but failed its startup
health check silently. Root cause, found by running the container locally via
Docker: insufficient default memory for loading the embedding model. 

An explicit Dockerfile enables local reproduction of container issues; increased
memory allocation resolved the failure. Full troubleshooting history in
[deployment.md](deployment.md).