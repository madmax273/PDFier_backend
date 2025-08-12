# app/services/pdf_processing.py

from PyPDF2 import PdfReader # pip install pypdf
from langchain_text_splitters import RecursiveCharacterTextSplitter # pip install langchain-text-splitters
from fastapi import UploadFile
from typing import List

async def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    """Extracts text from a PDF file."""
    try:
        pdf_file.file.seek(0) # Reset file pointer
        reader = PdfReader(pdf_file.file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Could not extract text from PDF: {e}")

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Splits text into chunks with specified size and overlap."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len, # or a token counter if you have one
        separators=["\n\n", "\n", " ", ""] # Prioritize larger breaks
    )
    chunks = text_splitter.split_text(text)
    return chunks