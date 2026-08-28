"""PDF ingestion: extract text from a text-based PDF pathology report."""

import logging
from pathlib import Path

import pdfplumber

test_fixtures_dir = Path("./test_fixtures")
MIN_CHARS = 50
logger = logging.getLogger(__name__)


def extract_text_from_pdf(fp: Path) -> str:
    """Extract text from a PDF file.

    Args:
        fp: Path or string path to a PDF file.

    Returns:
        The extracted text.

    Raises:
        ValueError: If extracted text is shorter than `MIN_CHARS` (likely scanned).
    """
    pages = []

    with pdfplumber.open(fp) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if text is not None:
                pages.append(text)

    full_text = "\n".join(pages).strip()

    if len(full_text) < MIN_CHARS:
        raise ValueError(
            f"{fp} returned less than {MIN_CHARS} characters."
            "Empty PDF or scanned, no text detected."
        )

    return full_text


if __name__ == "__main__":
    files = list(test_fixtures_dir.glob("*.pdf"))
    succeeded = []
    failed = []

    for fp in files:
        try:
            full_text = extract_text_from_pdf(fp)
            logger.debug(f"OK   {fp.name}: {len(full_text)} characters")
            succeeded.append(fp.name)
        except ValueError as e:
            logger.warning(f"FAIL {fp.name}: {e}")
            failed.append((fp.name, str(e)))

    logger.info(f"{len(succeeded)}/{len(files)} succeeded.")
    logger.debug(f"Succeeded: {succeeded}")
    logger.debug(f"Failed: {failed}")

    for name, reason in failed:
        logger.debug(f"  - {name}: {reason}")
