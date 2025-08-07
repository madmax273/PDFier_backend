import fitz  # PyMuPDF
from io import BytesIO

async def protect_pdf_content(pdf_content: bytes, password: str, permissions: dict) -> bytes:
    """
    Protect a PDF with password and permissions using PyMuPDF
    
    Args:
        pdf_content: Raw PDF content as bytes
        password: Password for the PDF
        permissions: Dictionary containing permissions like:
            {
                "printing": "high",  # 'none', 'low', or 'high'
                "modifying": False,
                "copying": False,
                "form_filling": False
            }
    
    Returns:
        bytes: Protected PDF content
    """
    # Open the PDF
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    output = BytesIO()
    
    # Set encryption options
    encrypt_meth = fitz.PDF_ENCRYPT_AES_256  # Strongest encryption
    
    # Convert permissions to PyMuPDF format
    perm = 0
    if permissions.get("printing") == "high":
        perm |= fitz.PDF_PERM_PRINT  # Allow high-quality printing
    elif permissions.get("printing") == "low":
        perm |= fitz.PDF_PERM_PRINT_LOW_RES  # Allow low-quality printing only
    
    if permissions.get("modifying"):
        perm |= fitz.PDF_PERM_MODIFY
    if permissions.get("copying"):
        perm |= fitz.PDF_PERM_COPY
    if permissions.get("form_filling"):
        perm |= fitz.PDF_PERM_ANNOTATE | fitz.PDF_PERM_FORM
    
    # Set the encryption
    doc.save(
        output,
        encryption=encrypt_meth,
        owner_pw=password,  # Owner password (required for permissions)
        user_pw=password,   # User password (can be same as owner)
        permissions=perm
    )
    
    protected_pdf = output.getvalue()
    doc.close()
    
    return protected_pdf
