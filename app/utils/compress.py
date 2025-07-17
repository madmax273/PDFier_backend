def compress_pdf_content(pdf_content: bytes, compression_level: str) -> bytes:
    """
    Compress PDF content based on the compression level.
    """
    print(f"Compressing PDF content with level: {compression_level}")
    import fitz
    from io import BytesIO

    doc = fitz.open(stream=pdf_content, filetype="pdf")
    output = BytesIO()
    
    # Set compression parameters based on level
    if compression_level == "low":
        compress = True
        clean = True
    elif compression_level == "medium":
        compress = True
        clean = True
        doc.save(output, garbage=3, deflate=True, clean=clean)
        doc = fitz.open(stream=output.getvalue(), filetype="pdf")
        output = BytesIO()
    elif compression_level == "high":
        compress = True
        clean = True
        # Save twice for higher compression
        doc.save(output, garbage=3, deflate=True, clean=clean)
        doc = fitz.open(stream=output.getvalue(), filetype="pdf")
        output = BytesIO()
        doc.save(output, garbage=3, deflate=True, clean=clean)
        doc = fitz.open(stream=output.getvalue(), filetype="pdf")
        output = BytesIO()
    
    # Final save with appropriate compression
    doc.save(output, garbage=3, deflate=compress, clean=clean)
    compressed_pdf = output.getvalue()
    doc.close()
    
    return compressed_pdf