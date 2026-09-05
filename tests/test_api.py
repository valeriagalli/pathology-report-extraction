"""
Test suite for the api module.
"""

import pandas as pd
from fastapi.testclient import TestClient

from pathology_extraction.api import app
from pathology_extraction.config import REPORTS_FP

client = TestClient(app)


def test_extract_endpoint_returns_200():
    """Test that the /extract endpoint returns a 200 status code
    for a valid request."""
    response = client.post("/extract", json={"report_text": "some report text"})
    assert response.status_code == 200


def test_extract_endpoint_with_real_report():
    """Test that the /extract endpoint returns a valid response
    when provided with a real report from the dataset."""
    reports_df = pd.read_csv(REPORTS_FP)
    sample_report = reports_df.sample(n=1, random_state=42).iloc[0]["text"]

    response = client.post("/extract", json={"report_text": sample_report})
    assert response.status_code == 200

    data = response.json()
    assert "fields" in data
    assert "diagnosis" in data["fields"]
