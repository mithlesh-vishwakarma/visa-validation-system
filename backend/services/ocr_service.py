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
        file_name: Original filename (used for mock data hints)
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
        # Image files: future Tesseract integration point
        raw_text, confidence_score = _extract_image_text(file_path)

    if not raw_text.strip():
        logger.warning(f"No text extracted from '{file_name}'. Using smart mock data.")
        return _build_mock_result(category, doc_type, file_name)

    # Heuristic regex extraction (fast, always runs)
    extracted_data = _parse_text_heuristics(raw_text, category)

    # AI structured analysis via document analyzers
    from services.document_analyzers import get_analyzer
    analyzer = get_analyzer(category)
    ai_analysis = analyzer.analyze(raw_text, extracted_data)

    return {
        "category": category,
        "raw_text": raw_text,
        "confidence_score": confidence_score,
        "extracted_data": extracted_data,
        "ai_analysis": ai_analysis,
    }


def _extract_pdf_text(file_path: str) -> tuple[str, float]:
    """
    Extract all text from a PDF file using pdfplumber.

    Returns:
        (raw_text, confidence_score)
    """
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = '\n'.join(text_parts).strip()
        # Confidence heuristic: proportion of non-whitespace chars to total chars
        if full_text:
            non_ws = len(full_text.replace(' ', '').replace('\n', ''))
            confidence = min(1.0, non_ws / max(len(full_text), 1) * 2)
        else:
            confidence = 0.0

        logger.info(f"PDF extraction: {len(full_text)} chars, confidence: {confidence:.2f}")
        return full_text, round(confidence, 3)

    except ImportError:
        logger.error("pdfplumber not installed")
        return "", 0.0
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return "", 0.0


def _extract_image_text(file_path: str) -> tuple[str, float]:
    """
    Placeholder for image OCR (Tesseract / Azure Vision).
    Currently returns empty text and falls back to mock data.
    """
    logger.info(f"Image OCR not yet implemented for: {file_path}")
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


def _build_mock_result(category: str, doc_type: str, file_name: str = "") -> dict:
    """
    Build intelligent mock data when OCR text extraction fails.
    Used for image files and unreadable PDFs.
    """
    from services.document_analyzers import get_analyzer
    mock_extracted = generate_mock_extracted(category, file_name)
    analyzer = get_analyzer(category)
    ai_analysis = analyzer.analyze("", mock_extracted)

    # Give mock data lower confidence than real OCR
    return {
        "category": category,
        "raw_text": "",
        "confidence_score": 0.45,  # Lower confidence for mock data
        "extracted_data": mock_extracted,
        "ai_analysis": ai_analysis,
    }


def generate_mock_extracted(category: str, file_name: str = "") -> dict:
    """
    Generate realistic mock extracted data per document category.
    File name hints (e.g., 'expired_passport.pdf') influence the mock data.
    """
    file_name_lower = file_name.lower()

    if category == 'passport':
        if 'expired' in file_name_lower:
            expiry = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            expiry = (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d')
        return {
            'passport_number': 'P9876543',
            'name': 'Rahul Sharma',
            'expiry_date': expiry,
            'nationality': 'Indian',
            'dob': '1992-08-14',
        }

    elif category == 'bank_statement':
        if 'low' in file_name_lower or 'poor' in file_name_lower:
            balance = 45000.0
        else:
            balance = 380000.0
        return {
            'bank_balance': balance,
            'name': 'Rahul Sharma',
            'account_number': 'XXXX0042',
            'currency': 'INR',
        }

    elif category == 'salary_slip':
        return {
            'salary': 75000.0,
            'company_name': 'Globex Technologies Pvt Ltd',
            'name': 'Rahul Sharma',
            'designation': 'Senior Software Engineer',
        }

    elif category == 'employment_letter':
        return {
            'company_name': 'Globex Technologies Pvt Ltd',
            'designation': 'Senior Software Engineer',
            'name': 'Rahul Sharma',
        }

    elif category == 'tax_return':
        return {
            'total_income': 900000.0,
            'assessment_year': '2024-25',
            'name': 'Rahul Sharma',
        }

    elif category == 'travel_history':
        return {
            'countries': ['Singapore', 'Thailand', 'UAE'],
        }

    else:
        return {
            'document_type': category,
            'extracted_on': datetime.now().strftime('%Y-%m-%d'),
        }


# Kept for backward compatibility with existing views
def generate_mock_data(doc_type: str, file_name: str = "") -> dict:
    """Legacy shim — routes to generate_mock_extracted."""
    category = resolve_category(doc_type)
    return generate_mock_extracted(category, file_name)


def _normalize_date(date_str: str) -> str:
    """Normalize a date string to YYYY-MM-DD."""
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return date_str
