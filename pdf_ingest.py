"""PDF ingestion: extract text from a text-based PDF pathology report."""

from pathlib import Path

import pdfplumber

test_fixtures_dir = Path("./test_fixtures")
MIN_CHARS = 50 

def extract_text_from_pdf(fp):
   pages = []

   with pdfplumber.open(fp) as pdf:
    for page in pdf.pages:
        text = page.extract_text(layout=True) 
        if text is not None:
           pages.append(text)

    full_text = "\n".join(pages).strip()

    if len(full_text) < MIN_CHARS:
       raise ValueError(f"{fp} returned less than {MIN_CHARS} characters."
                 "Empty PDF or scanned, no text detected.")
    
    return full_text


if __name__ == "__main__":
    files = list(test_fixtures_dir.glob("*.pdf"))
    succeeded = []
    failed = []

    for fp in files:
        try:
            full_text = extract_text_from_pdf(fp)
            print(f"OK   {fp.name}: {len(full_text)} characters")
            succeeded.append(fp.name)
        except ValueError as e:
            print(f"FAIL {fp.name}: {e}")
            failed.append((fp.name, str(e)))

    print(f"\n{len(succeeded)}/{len(files)} succeeded.")
    print("Succeeded:", succeeded)
    print("Failed:")
    
    for name, reason in failed:
        print(f"  - {name}: {reason}")