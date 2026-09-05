"""Example: send a sample report to a running API instance and print the result."""

import sys

import pandas as pd
import requests

from pathology_extraction.api import ExtractionResponse
from pathology_extraction.config import REPORTS_FP


def print_result(response_data: ExtractionResponse):
    for field_name, field in response_data.fields.items():
        print(f"{field_name}:")
        print(f"  value: {field.value}")
        print(f"  evidence: {field.evidence}")
        if field.value_evidence_score is not None:
            print(f"  value_evidence_score: {field.value_evidence_score:.2f}")
        if field.evidence_semantic_score is not None:
            print(f"  evidence_semantic_score: {field.evidence_semantic_score:.2f}")
        print()


def main():
    """Send a sample report to the API and print the response."""
    reports_df = pd.read_csv(REPORTS_FP)
    sample_row = reports_df.sample(n=1).iloc[0]
    report_id = sample_row["patient_filename"]
    sample_report = sample_row["text"]

    print(f"Report ID: {report_id}\n")
    print(f"Raw report text:\n{sample_report}\n")

    try:
        response = requests.post(
            "http://127.0.0.1:8000/extract", json={"report_text": sample_report}
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Could not connect. Is the API running? Start it with:")
        print("  uvicorn pathology_extraction.api:app --reload")
        sys.exit(1)

    response_data = ExtractionResponse.model_validate(response.json())
    print_result(response_data)


if __name__ == "__main__":
    main()
