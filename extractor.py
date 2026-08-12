"""Build and run a structured extractor over pathology report text."""

import json

from groq import Groq

from config import (
    DIRECT_API_EXTRACTIONS_DIR,
    DIRECT_API_MODEL_NAME,
)
from schema import PathologyExtraction

PROMPT_TEMPLATE = """
You are extracting structured clinical information from pathology reports.

The report may contain OCR artifacts such as typos, garbled characters, or
formatting noise from scanned PDFs. Correct an obvious OCR artifact only when
the intended text is unambiguous from the surrounding context. Do not infer
clinical information that is not supported by the report.

Extract the following information:
- primary diagnosis
- tumor site
- tumor grade
- pathological stage
- surgical margin status

For each field:
- Return the extracted value only when it is explicitly supported by the report.
- Do not infer information that is not stated in the report.
- If the information is absent or cannot be determined, return null.
- Provide the relevant text from the report as evidence for every extracted value.
- Preserve the meaning and terminology of the original report.
- Do not use external knowledge to fill missing information.

Return the result according to the provided extraction schema.

"""


client = Groq()


def build_extractor(
    model_name: str = DIRECT_API_MODEL_NAME, raw_report: str = ""
) -> PathologyExtraction:
    """Query the LLM to extract structured pathology information.

    Args:
        model_name: Model identifier passed to the Groq client.
        raw_report: The raw report text to extract from.

    Returns:
        A validated `PathologyExtraction` instance.
    """

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": PROMPT_TEMPLATE,
            },
            {"role": "user", "content": f"Pathology report text:\n{raw_report}"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "pathology_extraction",
                "strict": True,
                "schema": PathologyExtraction.model_json_schema(),
            },
        },
        temperature=0,
    )

    extracted = completion.choices[0].message.content

    result = PathologyExtraction.model_validate(json.loads(extracted))
    return result


def run_extraction(reports_df_all, subset=None) -> list[str]:
    failed_extractions = []
    extraction_files = []
    if subset:
        reports_df = reports_df_all.sample(n=subset, random_state=42)
    else:
        reports_df = reports_df_all
    for _, row in reports_df.iterrows():
        report_id = row["patient_filename"]
        report_text = row["text"]

        id_result_fp = DIRECT_API_EXTRACTIONS_DIR / f"{report_id}.json"
        try:
            extracted = build_extractor("openai/gpt-oss-120b", report_text)
        except Exception as e:
            print(f"FAILED {report_id}: {e}")
            failed_extractions.append(report_id)
            continue
        with open(id_result_fp, "w") as res_fp:
            json.dump(extracted.model_dump(), res_fp, indent=2)
        extraction_files.append(id_result_fp)
        print(f"Saved extracted data for {report_id}")

    return extraction_files, failed_extractions
