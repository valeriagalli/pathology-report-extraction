
## Roadmap

### v0.1 — Single-model extraction
- [x] PDF text ingestion
- [x] Extraction schema
- [x] LLM extraction agent (direct Groq API)
- [x] Validation and human-in-the-loop review
- [x] End-to-end pipeline over TCGA-Reports dataset

### v0.2 — Multi-model extraction
- [x] Multi-model extraction support
- [x] Cross-model agreement analysis
- [x] Composite confidence score
- [x] Integrate model agreement into review workflow
- [x] Partial unit test coverage

### v0.3 — Packaging and deployment
- [x] Restructure to src/ layout with pyproject.toml
- [x] FastAPI wrapper exposing extraction + confidence as an endpoint
- [x] Deploy to Cloud Run 
- [x] GitHub Actions CI running the test suite on push

### Possible improvements
- [ ] Deployment-level testing in CI (verify the live service, not just unit tests)
- [ ] Larger, labeled validation set for confidence-threshold calibration
- [ ] Expand unit test coverage to extraction.py (would require mocking the Groq client)
- [ ] Custom Swagger UI or file-upload support for large report text in `/docs`
- [ ] `docs/architecture.md` design-rationale write-up