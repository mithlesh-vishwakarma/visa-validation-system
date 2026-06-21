"""
Base Document Analyzer
=======================
Abstract base class that all document analyzers inherit from.
Provides shared utility methods and the common analyze() interface.
"""

import re
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Base class for all document analyzers.
    Subclasses implement analyze() to extract document-specific fields.
    """

    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        """
        Perform analysis on document text and pre-extracted data.
        Default implementation returns a generic result.
        Override in subclasses for document-specific extraction.
        """
        return {
            "document_type": "generic",
            "analysis_status": "completed",
            "extracted_fields": extracted_data,
            "anomalies": [],
            "confidence": 0.5,
        }

    # -----------------------------------------------------------------------
    # Shared utility methods available to all analyzers
    # -----------------------------------------------------------------------

    def extract_name(self, text: str, default: str = "N/A") -> str:
        """Extract a person's name from document text."""
        patterns = [
            r'(?:name|full\s+name|applicant\s+name|holder|customer|account\s+holder)\s*[:\-]?\s*([A-Z][a-zA-Z ]{2,40})',
            r'(?:mr\.|mrs\.|ms\.|dr\.)\s+([A-Z][a-zA-Z ]{2,40})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if not any(kw in name.lower() for kw in ['republic', 'india', 'passport', 'ministry']):
                    return name
        return extracted_data_get(extracted_data=None, key='name', default=default)

    def extract_amount(self, text: str, keywords: list, default: float = 0.0) -> float:
        """Extract a monetary amount following given keywords."""
        keyword_pattern = '|'.join(keywords)
        pattern = rf'(?:{keyword_pattern})\s*[:\-]?\s*(?:INR|Rs\.?|₹|\$|USD|EUR|GBP)?\s*([\d,]+(?:\.\d{{1,2}})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                pass
        return default

    def extract_date(self, text: str, keywords: list) -> str | None:
        """Extract a date near specific keywords."""
        keyword_pattern = '|'.join(keywords)
        # Support formats: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD Mon YYYY
        date_patterns = [
            rf'(?:{keyword_pattern})\s*[:\-]?\s*(\d{{2}}[/\-\.]\d{{2}}[/\-\.]\d{{4}})',
            rf'(?:{keyword_pattern})\s*[:\-]?\s*(\d{{4}}[/\-\.]\d{{2}}[/\-\.]\d{{2}})',
            rf'(?:{keyword_pattern})\s*[:\-]?\s*(\d{{1,2}}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{{4}})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.normalize_date(match.group(1))
        return None

    def normalize_date(self, date_str: str) -> str:
        """Normalize any date string to YYYY-MM-DD format."""
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%d %b %Y', '%d %B %Y',
            '%b %d, %Y', '%B %d, %Y',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return date_str

    def detect_anomalies(self, checks: list) -> list:
        """
        Run a list of check lambdas and collect anomalies.
        checks: list of (condition_bool, message_str) tuples
        """
        anomalies = []
        for condition, message in checks:
            if condition:
                anomalies.append(message)
        return anomalies

    def months_until(self, date_str: str) -> float | None:
        """Return number of months from now until a given YYYY-MM-DD date."""
        try:
            target = datetime.strptime(date_str, '%Y-%m-%d')
            delta_days = (target - datetime.now()).days
            return round(delta_days / 30.44, 1)
        except (ValueError, TypeError):
            return None


def extracted_data_get(extracted_data, key, default=None):
    """Safe getter for extracted_data dict."""
    if not extracted_data:
        return default
    return extracted_data.get(key, default)
