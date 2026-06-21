"""Cover Letter Analyzer — intent statement, trip purpose, applicant details."""

import re
from services.document_analyzers.base import BaseAnalyzer


class CoverLetterAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''
        applicant_name = self._extract_applicant(text)
        purpose = self._extract_purpose(text)
        duration = self._extract_duration(text)
        destination = self._extract_destination(text)
        has_financial_self_support = any(kw in text.lower() for kw in ['self-funded', 'self funded', 'bear all expenses', 'funding my own'])
        has_return_commitment = any(kw in text.lower() for kw in ['will return', 'intend to return', 'return to india', 'return to my country'])
        word_count = len(text.split())

        anomalies = self.detect_anomalies([
            (word_count < 100, f"Cover letter is very short ({word_count} words) — may lack required detail"),
            (not has_return_commitment, "No explicit return commitment statement found"),
            (not purpose or purpose == 'N/A', "Purpose of visit not clearly stated"),
        ])

        return {
            "document_type": "cover_letter",
            "applicant_name": applicant_name,
            "visit_purpose": purpose,
            "destination": destination,
            "duration": duration,
            "self_funded_mentioned": has_financial_self_support,
            "return_commitment": has_return_commitment,
            "word_count": word_count,
            "anomalies": anomalies,
            "confidence": 0.65 if word_count > 150 else 0.40,
        }

    def _extract_applicant(self, text: str) -> str:
        m = re.search(r'(?:I,|sincerely,|yours faithfully,|regards,)\s*([A-Z][a-zA-Z\s]{2,40})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_purpose(self, text: str) -> str:
        purposes = ['tourism', 'holiday', 'business', 'medical treatment', 'education', 'conference', 'family visit', 'honeymoon', 'sightseeing']
        for p in purposes:
            if p in text.lower():
                return p.title()
        return 'N/A'

    def _extract_duration(self, text: str) -> str:
        m = re.search(r'(\d+)\s*(days?|weeks?|months?)', text, re.IGNORECASE)
        return f"{m.group(1)} {m.group(2)}" if m else 'N/A'

    def _extract_destination(self, text: str) -> str:
        m = re.search(r'(?:visiting|travel(?:ling)? to|trip to|visit to)\s+([A-Z][a-zA-Z\s]{2,30})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'
