import json
import pandas as pd
from groq import Groq
from pathlib import Path

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
ROOT_DIR = Path().resolve()
DATA_DIR = ROOT_DIR / "dataset"
RESULT_API_DIR = ROOT_DIR / "results_directAPI"
RESULT_API_DIR.mkdir(exist_ok=True)

REPORTS_FP = DATA_DIR / "TCGA_Reports.csv"

client = Groq()

def build_extractor(model_name: str = "openai/gpt-oss-120b", raw_report: str = ""):

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system", 
                "content": PROMPT_TEMPLATE,
            },
            {
                "role": "user", 
                "content": f"Pathology report text:\n{raw_report}"
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "pathology_extraction",
                "strict": True,
                "schema": PathologyExtraction.model_json_schema(),
            },
        },
        temperature = 0,
    )

    extracted = completion.choices[0].message.content

    result = PathologyExtraction.model_validate(json.loads(extracted))
    return result


if __name__ == "__main__":

    reports_df = pd.read_csv(REPORTS_FP)
    print(reports_df.head())

    for _, row in reports_df.sample(n=5, random_state=42).iterrows():
        report_id = row["patient_filename"]
        report_text = row["text"]
        id_result_fp = RESULT_API_DIR / f"{report_id}.json"
        try:
            extracted = build_extractor("openai/gpt-oss-120b", report_text)
        except Exception as e:
            print(f"FAILED {id}: {e}")
        with open(id_result_fp, "w") as res_fp:
            json.dump(extracted.model_dump(), res_fp, indent=2)
        print(f"Saved extracted data for {report_id}")
         

   
