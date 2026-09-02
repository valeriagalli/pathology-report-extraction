
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
- [x] Partial unit test coverage

### v0.3 — Packaging and deployment (planned)
- [x] Restructure to src/ layout with pyproject.toml
- [ ] FastAPI wrapper exposing extraction + confidence as an endpoint
- [ ] Deploy to Cloud Run or AWS Lambda