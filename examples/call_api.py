"""Example: send a sample report to a running API instance and print the result."""

import sys
import requests
import pandas as pd
from pathology_extraction.config import REPORTS_FP


def main():
    reports_df = pd.read_csv(REPORTS_FP)
    sample_report = reports_df.sample(n=1).iloc[0]["text"]

    try:
        response = requests.post(
            "http://127.0.0.1:8000/extract", json={"report_text": sample_report}
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Could not connect. Is the API running? Start it with:")
        print("  uvicorn pathology_extraction.api:app --reload")
        sys.exit(1)

    print(response.json())


if __name__ == "__main__":
    main()