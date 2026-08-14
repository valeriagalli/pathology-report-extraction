"""Build and run a structured extractor over pathology report text."""

import json
from pathlib import Path

import pandas as pd
from groq import Groq

from review import get_clean_error
from schema import PathologyExtraction

client = Groq()


def build_extractor(
    model_name: str, prompt: str, response_format: dict, raw_report: str = ""
) -> PathologyExtraction:
    """Query the LLM to extract structured pathology information.

    Args:
        model_name: Model identifier passed to the Groq client.
        prompt: System prompt for the LLM.
        response_format: Groq API response format specification (e.g., JSON schema).
        raw_report: The raw report text to extract from.

    Returns:
        A validated `PathologyExtraction` instance.
    """

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": f"Pathology report text:\n{raw_report}"},
        ],
        response_format=response_format,
        temperature=0,
    )

    extracted = completion.choices[0].message.content

    result = PathologyExtraction.model_validate(json.loads(extracted))
    return result


def run_extraction(
    reports_df_all: pd.DataFrame,
    subset: int | None,
    model_name: str,
    prompt: str,
    response_format: dict,
    output_dir: Path,
) -> tuple[list[Path], list[dict[str, str]]]:
    """Run field extraction from raw report text pipeline.

    Args:
        reports_df_all: DataFrame containing raw reports with 'patient_filename'
            and 'text' columns.
        subset: Number of reports to sample randomly; if None, process all reports.
        model_name: Model identifier passed to the Groq client.
        response_format: Groq API response format specification.
        output_dir: Directory to save extracted JSON files.

    Returns:
        A tuple of (extraction_files, failed_extractions) where extraction_files
        is a list of Path objects to successfully extracted JSON files and
        failed_extractions is a list of dicts with 'report_id' and 'error' keys.
    """
    failed_extractions = []
    extraction_files = []
    if subset:
        reports_df = reports_df_all.sample(n=subset, random_state=10)
    else:
        reports_df = reports_df_all
    for _, row in reports_df.iterrows():
        report_id = row["patient_filename"]
        report_text = row["text"]

        id_result_fp = output_dir / f"{report_id}.json"
        # report already extracted
        if id_result_fp.is_file():
            extraction_files.append(id_result_fp)
            continue
        else:
            # extract report
            try:
                extracted = build_extractor(
                    model_name, prompt, response_format, report_text
                )
            except Exception as e:
                error_msg = get_clean_error(e)
                print(f"\nFAILED {report_id}: {error_msg}")
                failed_extractions.append({"report_id": report_id, "error": error_msg})
                continue
            with open(id_result_fp, "w") as res_fp:
                json.dump(extracted.model_dump(), res_fp, indent=2)
            extraction_files.append(id_result_fp)
            print(f"Saved extracted data for {report_id}")

    return extraction_files, failed_extractions
