"""
Resume parser to extract candidate information from uploaded files
"""

import PyPDF2
from docx import Document
import re
from typing import Dict, Optional

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX: {e}")
    return text

def extract_resume_info(file_path: str) -> Dict[str, str]:
    """Extract structured information from resume"""
    
    # Determine file type and extract text
    if file_path.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported file format"}
    
    # Extract basic information
    resume_info = {
        "raw_text": text[:2000],  # First 2000 chars for context
        "experience_keywords": extract_keywords(text, ["python", "java", "sql", "aws", "ml", "data", "product", "leadership", "agile"]),
        "education": extract_education(text),
    }
    
    return resume_info

def extract_keywords(text: str, keywords: list) -> list:
    """Extract relevant keywords from resume"""
    found_keywords = []
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    return found_keywords

def extract_education(text: str) -> str:
    """Extract education information"""
    # Look for common degree patterns
    degrees = re.findall(r'(B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|MBA|PhD|BE|BTech|MTech|BCA|MCA)\s*(?:in|,)?\s*([^,\n]*)', text, re.IGNORECASE)
    if degrees:
        return ", ".join([f"{d[0]} in {d[1]}" for d in degrees[:2]])
    return "Not specified"

def format_resume_context(resume_info: Dict) -> str:
    """Format resume info as context for interview"""
    context = f"""
CANDIDATE BACKGROUND:
- Key Skills: {', '.join(resume_info.get('experience_keywords', ['Not extracted']))}
- Education: {resume_info.get('education', 'Not specified')}
- Resume Excerpt: {resume_info.get('raw_text', 'No text extracted')[:500]}...

Use this information to personalize questions and make the interview contextual to the candidate's background.
"""
    return context
