import fitz
from shared.exceptions import DocumentCorruptedError

class FitzDocumentRepository:
    """
    A repository responsible for loading PDF documents using PyMuPDF (fitz).
    """
    def load_pdf(self, file_path: str):
        """Loads a PDF from a file path."""
        try:
            return fitz.open(file_path)
        except Exception as e:
            # Re-raise as a domain-specific exception
            raise DocumentCorruptedError(f"Failed to open PDF '{file_path}': {e}")

    def load_pdf_from_bytes(self, pdf_bytes: bytes):
        """Loads a PDF from a byte stream."""
        try:
            return fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise DocumentCorruptedError(f"Failed to open PDF from bytes: {e}")
