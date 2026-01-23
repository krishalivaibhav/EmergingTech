from io import BytesIO

from pypdf import PdfReader


class PDFParsingError(RuntimeError):
    """Raised when PDF content cannot be extracted safely."""


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        raise PDFParsingError("Uploaded PDF file is empty.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:  # pragma: no cover - parser-specific failures
        raise PDFParsingError("Unable to read the PDF file.") from exc

    page_text: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            page_text.append(text.strip())

    parsed_text = "\n".join(page_text).strip()
    if not parsed_text:
        raise PDFParsingError(
            "No readable text found in the PDF. Try a text-based PDF or paste resume text manually."
        )

    return parsed_text

