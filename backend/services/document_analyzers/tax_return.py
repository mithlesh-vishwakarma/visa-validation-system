"""Tax Return (ITR) Analyzer — extracts income, assessment year, and tax details."""

import re
from services.document_analyzers.base import BaseAnalyzer


class TaxReturnAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''

        taxpayer_name = extracted_data.get('name') or self._extract_name(text)
        pan_number = self._extract_pan(text)
        assessment_year = extracted_data.get('assessment_year') or self._extract_assessment_year(text)

        total_income = (
            extracted_data.get('total_income')
            or self.extract_amount(text, ['gross total income', 'total income', 'taxable income', 'net income'], 0.0)
        )
        tax_payable = self.extract_amount(text, ['tax payable', 'total tax', 'tax liability'], 0.0)
        tds_amount = self.extract_amount(text, ['tds', 'tax deducted at source', 'tds credit'], 0.0)
        refund_amount = self.extract_amount(text, ['refund', 'refund due'], 0.0)

        itr_form = self._extract_itr_form(text)
        filing_status = 'Filed' if any(kw in text.lower() for kw in ['acknowledgment', 'e-filed', 'filed on']) else 'Unknown'
        acknowledgment_number = self._extract_acknowledgment(text)

        income_tier = self._classify_income(total_income)

        anomalies = self.detect_anomalies([
            (total_income == 0, "Total income could not be extracted from ITR"),
            (total_income < 250000, f"Income below basic exemption limit: ₹{total_income:,.0f}"),
            (not pan_number, "PAN number not found in ITR document"),
            (not assessment_year, "Assessment year not identified"),
        ])

        return {
            "document_type": "tax_return",
            "taxpayer_name": taxpayer_name,
            "pan_number": pan_number,
            "assessment_year": assessment_year,
            "itr_form_type": itr_form,
            "filing_status": filing_status,
            "acknowledgment_number": acknowledgment_number,
            "gross_total_income": round(total_income, 2),
            "tax_payable": round(tax_payable, 2),
            "tds_credit": round(tds_amount, 2),
            "refund_due": round(refund_amount, 2),
            "income_tier": income_tier,
            "anomalies": anomalies,
            "confidence": 0.80 if total_income > 0 else 0.45,
        }

    def _extract_name(self, text: str) -> str:
        m = re.search(r'(?:name|taxpayer|assessee)\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,40})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_pan(self, text: str) -> str:
        m = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text)
        return m.group(1) if m else None

    def _extract_assessment_year(self, text: str) -> str:
        m = re.search(r'assessment\s+year\s*[:\-]?\s*(\d{4}[-\s]\d{2,4})', text, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_itr_form(self, text: str) -> str:
        m = re.search(r'(ITR[-\s]?[1-7])', text, re.IGNORECASE)
        return m.group(1).upper() if m else 'Unknown'

    def _extract_acknowledgment(self, text: str) -> str:
        m = re.search(r'acknowledgment\s+(?:no\.?|number)?\s*[:\-]?\s*(\d{10,15})', text, re.IGNORECASE)
        return m.group(1) if m else None

    def _classify_income(self, income: float) -> str:
        if income >= 1500000:
            return 'High Income (>15L)'
        elif income >= 700000:
            return 'Upper Middle (7-15L)'
        elif income >= 250000:
            return 'Middle Income (2.5-7L)'
        return 'Below Threshold (<2.5L)'
