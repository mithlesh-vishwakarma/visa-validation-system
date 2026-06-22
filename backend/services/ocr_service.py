"""
OCR Document Processing Service
=================================
Extracts text from PDF and image files, routes to AI document analyzers,
and returns structured data with confidence scores.

Pipeline:
    Upload → OCR Extraction → Text Cleaning → AI Analyzer → Structured Data

Supported formats: PDF, PNG, JPG, JPEG, DOCX
OCR method: pdfplumber for PDFs; placeholder for images (future: Tesseract/Azure OCR)
"""

import re
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Map user-facing document names to category slugs
# Allows flexible matching from both legacy free-text names and new slugs
NAME_TO_CATEGORY = {
    'passport': 'passport',
    'bank statement': 'bank_statement',
    'bank_statement': 'bank_statement',
    'salary slip': 'salary_slip',
    'salary_slip': 'salary_slip',
    'payslip': 'salary_slip',
    'pay slip': 'salary_slip',
    'employment letter': 'employment_letter',
    'employment_letter': 'employment_letter',
    'employment letter/noc': 'employment_letter',
    'tax return': 'tax_return',
    'tax_return': 'tax_return',
    'itr': 'tax_return',
    'income tax return': 'tax_return',
    'travel history': 'travel_history',
    'travel_history': 'travel_history',
    'invitation letter': 'invitation_letter',
    'invitation_letter': 'invitation_letter',
    'hotel booking': 'hotel_booking',
    'hotel_booking': 'hotel_booking',
    'flight booking': 'flight_booking',
    'flight_booking': 'flight_booking',
    'flight reservation': 'flight_booking',
    'cover letter': 'cover_letter',
    'cover_letter': 'cover_letter',
    'photo': 'other',
}


def resolve_category(name: str, existing_category: str = None) -> str:
    """
    Resolve a document category slug from a free-text name.
    If the Document already has a valid category, prefer it.

    Args:
        name: User-provided document name (e.g., "Passport", "Bank Statement")
        existing_category: Already stored category slug (if any)

    Returns:
        Category slug string
    """
    if existing_category and existing_category != 'other':
        return existing_category
    name_clean = name.lower().strip()
    return NAME_TO_CATEGORY.get(name_clean, 'other')


def extract_document_data(file_path: str, doc_type: str, file_name: str = "",
                           existing_category: str = None) -> dict:
    """
    Main OCR entry point — extracts text from a file and routes to the
    appropriate AI document analyzer.

    Args:
        file_path: Absolute path to the uploaded file
        doc_type: User-provided document type name (e.g., "Passport")
        file_name: Original filename
        existing_category: Already-resolved category slug

    Returns:
        dict: {
            "category": str,
            "raw_text": str,
            "confidence_score": float,
            "extracted_data": dict,    # Heuristic/regex extracted fields
            "ai_analysis": dict,       # Deep AI structured analysis
        }
    """
    category = resolve_category(doc_type, existing_category)
    raw_text = ""
    confidence_score = 0.0

    is_pdf = file_path.lower().endswith('.pdf')

    if is_pdf and os.path.exists(file_path):
        raw_text, confidence_score = _extract_pdf_text(file_path)
    elif os.path.exists(file_path):
        raw_text, confidence_score = _extract_image_text(file_path)

    if not raw_text.strip():
        raise ValueError(
            f"OCR text extraction failed: No text could be extracted from '{file_name}'. "
            f"Please ensure it is a valid, clear, and readable document."
        )

    # Heuristic regex extraction (fast, always runs)
    extracted_data = _parse_text_heuristics(raw_text, category)

    # AI structured analysis via document analyzers (routed through configured AI Provider)
    from services.ai_provider import get_ai_provider
    ai_provider = get_ai_provider()
    ai_analysis = ai_provider.analyze_document(category, raw_text, extracted_data)

    return {
        "category": category,
        "raw_text": raw_text,
        "confidence_score": confidence_score,
        "extracted_data": extracted_data,
        "ai_analysis": ai_analysis,
    }


def _extract_pdf_text(file_path: str) -> tuple[str, float]:
    """
    Extract text from a PDF file using Tesseract OCR.
    Converts PDF pages to images using PyMuPDF (fitz), then runs Tesseract.
    """
    try:
        import pytesseract # type: ignore
        from PIL import Image
        import fitz # type: ignore
        import io

        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        logger.info(f"Running Tesseract OCR on PDF: {file_path}")
        text_parts = []
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            page_text = pytesseract.image_to_string(img)
            if page_text.strip():
                text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()

        if full_text:
            alnum_count = sum(1 for c in full_text if c.isalnum())
            total_len = len(full_text.replace(" ", "").replace("\n", ""))
            confidence = min(1.0, alnum_count / max(total_len, 1) * 1.5)
        else:
            confidence = 0.0

        logger.info(f"PDF OCR complete: {len(full_text)} chars, confidence: {confidence:.2f}")
        return full_text, round(confidence, 3)

    except Exception as e:
        logger.error(f"PDF OCR extraction error: {e}")
        return "", 0.0


def _extract_image_text(file_path: str) -> tuple[str, float]:
    """
    Extract text from an image file using Tesseract OCR.
    """
    try:
        import pytesseract # type: ignore
        from PIL import Image

        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        logger.info(f"Running Tesseract OCR on image: {file_path}")
        img = Image.open(file_path)
        raw_text = pytesseract.image_to_string(img)

        full_text = raw_text.strip()
        if full_text:
            alnum_count = sum(1 for c in full_text if c.isalnum())
            total_len = len(full_text.replace(" ", "").replace("\n", ""))
            confidence = min(1.0, alnum_count / max(total_len, 1) * 1.5)
        else:
            confidence = 0.0

        logger.info(f"Image OCR complete: {len(full_text)} chars, confidence: {confidence:.2f}")
        return full_text, round(confidence, 3)

    except Exception as e:
        logger.error(f"Image OCR extraction error: {e}")
        return "", 0.0


def _parse_text_heuristics(text: str, category: str) -> dict:
    """
    Fast heuristic/regex extraction — runs before the AI analyzer.
    Provides fallback fields if the AI analyzer can't extract them.
    """
    data = {}
    normalized = text.lower()

    if category == 'passport':
        passport_match = re.search(r'\b([A-Z][0-9]{7,8})\b', text)
        data['passport_number'] = passport_match.group(0) if passport_match else None

        name_match = re.search(
            r'(?:surname|given\s+name|full\s+name|name)\s*:?\s*([A-Za-z\s]{2,40})',
            text, re.IGNORECASE
        )
        data['name'] = name_match.group(1).strip() if name_match else None

        expiry_match = re.search(
            r'(?:expiry|exp|valid until|date of expiry)\s*:?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{4}|\d{4}[/\-.]\d{2}[/\-.]\d{2})',
            text, re.IGNORECASE
        )
        if expiry_match:
            data['expiry_date'] = _normalize_date(expiry_match.group(1))

    elif category == 'bank_statement':
        balance_match = re.search(
            r'(?:closing|available|current)\s+balance\s*:?\s*(?:inr|rs\.?|₹)?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if balance_match:
            try:
                data['bank_balance'] = float(balance_match.group(1).replace(',', ''))
            except ValueError:
                pass

        name_match = re.search(r'(?:account holder|customer|name)\s*:?\s*([A-Za-z\s]{2,40})', text, re.IGNORECASE)
        data['name'] = name_match.group(1).strip() if name_match else None

    elif category in ('tax_return', 'itr'):
        income_match = re.search(
            r'(?:gross total income|total income|taxable income)\s*:?\s*(?:inr|rs\.?|₹)?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if income_match:
            try:
                data['total_income'] = float(income_match.group(1).replace(',', ''))
            except ValueError:
                pass
        name_match = re.search(r'(?:name|taxpayer)\s*:?\s*([A-Za-z\s]{2,40})', text, re.IGNORECASE)
        data['name'] = name_match.group(1).strip() if name_match else None

    elif category == 'salary_slip':
        salary_match = re.search(
            r'(?:gross salary|gross pay|net salary|net pay)\s*:?\s*(?:inr|rs\.?|₹)?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if salary_match:
            try:
                data['salary'] = float(salary_match.group(1).replace(',', ''))
            except ValueError:
                pass
        company_match = re.search(r'^([A-Z][A-Za-z\s&\.]{5,60}(?:Pvt|Ltd|Inc|Corp|Limited))', text, re.IGNORECASE | re.MULTILINE)
        data['company_name'] = company_match.group(1).strip() if company_match else None

    elif category == 'employment_letter':
        comp_match = re.search(r'([A-Z][A-Za-z\s&\.]{3,60}(?:Ltd|Pvt|Inc|Corp|Limited|Solutions|Technologies))', text)
        data['company_name'] = comp_match.group(1).strip() if comp_match else None
        desig_match = re.search(r'(?:designation|position|post)\s*:?\s*([A-Za-z\s]{2,50})', text, re.IGNORECASE)
        data['designation'] = desig_match.group(1).strip() if desig_match else None

    return data


# Mock generation code removed as mock data fallbacks are disabled.


def _normalize_date(date_str: str) -> str:
    """Normalize a date string to YYYY-MM-DD."""
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return date_str
