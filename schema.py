"""Extraction schema of the relevant fields from unstructured reports."""

from pydantic import BaseModel, ConfigDict, Field


class ExtractedField(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str | None 
    evidence: str | None 


class PathologyExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnosis: ExtractedField = Field(description="Primary diagnosis, e.g. 'Renal cell carcinoma, clear cell type'")
    tumor_site: ExtractedField = Field(description="Anatomical site/organ of the tumor, e.g. 'Kidney, left upper pole'")
    grade: ExtractedField = Field(description="Tumor grade, e.g. 'Fuhrman Nuclear Grade II/IV' or 'Gleason 7 (3+4)'")
    stage: ExtractedField = Field(description="Pathological stage, e.g. 'pT1' or 'pT2N0M0', TNM notation if present")
    margins: ExtractedField = Field(description="Surgical margin status, e.g. 'Free of tumor' or 'Positive'")


if __name__ == "__main__":
    dummy_extraction = PathologyExtraction(
        diagnosis=ExtractedField(value="Renal cell carcinoma, clear cell type", evidence="..."),
        tumor_site=ExtractedField(value="Kidney, left upper pole", evidence="..."),
        grade=ExtractedField(value=None, evidence=None),
        stage=ExtractedField(value=None, evidence=None),
        margins=ExtractedField(value=None, evidence=None),
    )
    print(dummy_extraction)