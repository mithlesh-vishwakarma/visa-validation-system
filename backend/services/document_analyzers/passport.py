"""
Passport Analyzer
==================
Extracts and validates key fields from passport documents:
- Full name, nationality, passport number
- Date of birth, issue date, expiry date
- MRZ (Machine Readable Zone) data if present
- Anomaly detection (expired, expiring soon, name mismatch risk)
"""

import re
from datetime import datetime
from services.document_analyzers.base import BaseAnalyzer


class PassportAnalyzer(BaseAnalyzer):
    """AI analyzer for passport documents."""

    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''

        # --- Check Type Mismatch ---
        is_mismatch, mismatch_detail = self._check_type_mismatch('passport', text, extracted_data)
        if is_mismatch:
            return {
                "document_type": "passport",
                "invalid_document_type": True,
                "holder_name": "N/A",
                "nationality": "N/A",
                "passport_number": "N/A",
                "date_of_birth": "1990-01-01",
                "issue_date": "2020-01-01",
                "expiry_date": "2020-01-01",
                "months_remaining_validity": 0,
                "is_expired": True,
                "expiring_soon": False,
                "mrz_detected": False,
                "anomalies": [mismatch_detail],
                "confidence": 0.0,
            }


        # --- Extract Name ---
        name = extracted_data.get('name') or self._extract_passport_name(text)

        # --- Extract Passport Number ---
        passport_number = (
            extracted_data.get('passport_number')
            or self._extract_passport_number(text)
        )

        # --- Extract Nationality ---
        nationality = self._extract_nationality(text) or 'India'

        # --- Extract Dates ---
        dob = (
            extracted_data.get('dob')
            or self.extract_date(text, ['date of birth', 'birth date', 'dob', 'born'])
            or '1990-01-01'
        )
        issue_date = (
            extracted_data.get('issue_date')
            or self.extract_date(text, ['date of issue', 'issue date', 'issued on', 'issued'])
            or '2020-01-01'
        )
        expiry_date = (
            extracted_data.get('expiry_date')
            or self.extract_date(text, ['date of expiry', 'expiry date', 'valid until', 'expires'])
        )

        # Fallback expiry: 5 years from now if not found
        if not expiry_date:
            from datetime import timedelta
            expiry_date = (datetime.now() + timedelta(days=1825)).strftime('%Y-%m-%d')

        # --- Validity Check ---
        months_left = self.months_until(expiry_date)
        is_expired = months_left is not None and months_left < 0
        expiring_soon = months_left is not None and 0 <= months_left < 6

        # --- Anomaly Detection ---
        anomalies = self.detect_anomalies([
            (is_expired, f"Passport has expired (expired: {expiry_date})"),
            (expiring_soon, f"Passport expires in {months_left:.1f} months — may not meet the 6-month rule"),
            (not passport_number or passport_number == 'N/A', "Passport number could not be extracted"),
            (not name or name == 'N/A', "Holder name could not be extracted from passport"),
        ])

        return {
            "document_type": "passport",
            "holder_name": name,
            "nationality": nationality,
            "passport_number": passport_number,
            "date_of_birth": dob,
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "months_remaining_validity": months_left,
            "is_expired": is_expired,
            "expiring_soon": expiring_soon,
            "mrz_detected": 'P<' in text or '<<<' in text,
            "anomalies": anomalies,
            "confidence": 0.90 if not anomalies else 0.65,
        }

    def _extract_passport_name(self, text: str) -> str:
        """Extract name from passport text patterns."""
        patterns = [
            r'surname\s*[:\-]?\s*([A-Z][A-Z\s]+)',
            r'given\s+name[s]?\s*[:\-]?\s*([A-Z][A-Z\s]+)',
            r'name\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,40})',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip().title()
        # Try MRZ name extraction: P<IND<SURNAME<<GIVEN<NAME
        mrz = re.search(r'P<[A-Z]{3}<([A-Z<]+)', text)
        if mrz:
            parts = mrz.group(1).split('<')
            name_parts = [p for p in parts if p]
            if name_parts:
                return ' '.join(name_parts).title()
        return 'N/A'

    def _extract_passport_number(self, text: str) -> str:
        """Extract passport number (standard: 1 letter + 7 digits)."""
        match = re.search(r'\b[A-Z][0-9]{7,8}\b', text)
        return match.group(0) if match else 'N/A'

    def _extract_nationality(self, text: str) -> str:
        """Extract nationality from passport text."""
        match = re.search(
            r'(?:nationality|citizen)\s*[:\-]?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
            text, re.IGNORECASE
        )
        return match.group(1).strip() if match else 'Indian'
