from pdfminer.high_level import extract_text
import docx
import os

def extract_resume_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text(file_path)

    elif ext == ".docx":
        doc = docx.Document(file_path)
        return " ".join([p.text for p in doc.paragraphs])

    else:
        return ""