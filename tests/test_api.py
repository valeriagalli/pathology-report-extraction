"""
Test suite for the api module.
"""
import requests
import pandas as pd

from fastapi.testclient import TestClient

from pathology_extraction.api import app
from pathology_extraction.config import REPORTS_FP

client = TestClient(app)


def test_extract_endpoint_returns_200():
    response = client.post("/extract", json={"report_text": "some report text"})
    assert response.status_code == 200


def test_extract_endpoint_with_real_report():
    reports_df = pd.read_csv(REPORTS_FP)
    sample_report = reports_df.sample(n=1, random_state=42).iloc[0]["text"]

    response = client.post("/extract", json={"report_text": sample_report})
    assert response.status_code == 200

    data = response.json()
    assert "fields" in data
    assert "diagnosis" in data["fields"]