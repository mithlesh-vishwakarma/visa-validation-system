"""Salary Slip Analyzer — extracts employment and compensation details."""

import re
from services.document_analyzers.base import BaseAnalyzer


class SalarySlipAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''

        employee_name = extracted_data.get('name') or self._extract_name(text)
        company_name = extracted_data.get('company_name') or self._extract_company(text)
        designation = extracted_data.get('designation') or self._extract_designation(text)

        gross_salary = (
            extracted_data.get('salary')
            or self.extract_amount(text, ['gross salary', 'gross pay', 'gross total', 'ctc', 'gross earnings'], 0.0)
        )
        net_salary = self.extract_amount(text, ['net salary', 'net pay', 'take home', 'net amount'], gross_salary * 0.85)
        basic_salary = self.extract_amount(text, ['basic salary', 'basic pay', 'basic'], gross_salary * 0.5)

        pay_period = self._extract_pay_period(text)
        pf_deducted = self.extract_amount(text, ['pf', 'provident fund', 'epf'], 0.0) > 0
        tax_deducted = self.extract_amount(text, ['tds', 'income tax', 'tax deducted'], 0.0) > 0

        # Employment tier classification
        employment_tier = self._classify_employment(gross_salary)

        anomalies = self.detect_anomalies([
            (gross_salary == 0, "Could not extract salary amount from document"),
            (gross_salary < 20000, f"Low salary detected: ₹{gross_salary:,.0f}/month — may not meet financial requirements"),
            (not company_name or company_name == 'N/A', "Employer name could not be extracted"),
            (net_salary > gross_salary, "Net salary exceeds gross salary — data inconsistency"),
        ])

        return {
            "document_type": "salary_slip",
            "employee_name": employee_name,
            "company_name": company_name,
            "designation": designation,
            "pay_period": pay_period,
            "gross_salary": round(gross_salary, 2),
            "net_salary": round(net_salary, 2),
            "basic_salary": round(basic_salary, 2),
            "annual_ctc_estimate": round(gross_salary * 12, 2),
            "pf_deducted": pf_deducted,
            "tds_deducted": tax_deducted,
            "employment_tier": employment_tier,
            "anomalies": anomalies,
            "confidence": 0.85 if gross_salary > 0 else 0.40,
        }

    def _extract_name(self, text: str) -> str:
        for pattern in [
            r'employee\s+name\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,40})',
            r'name\s+of\s+employee\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,40})',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return 'N/A'

    def _extract_company(self, text: str) -> str:
        for pattern in [
            r'(?:company|employer|organization|firm|establishment)\s+name\s*[:\-]?\s*([A-Z][a-zA-Z\s&\.]{2,60})',
            r'^([A-Z][A-Z\s&\.]{5,60})(?:\s+(?:Pvt|Ltd|Private|Limited|Inc|Corp))',
        ]:
            m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return 'N/A'

    def _extract_designation(self, text: str) -> str:
        m = re.search(
            r'(?:designation|position|title|post|role)\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,50})',
            text, re.IGNORECASE
        )
        return m.group(1).strip() if m else 'N/A'

    def _extract_pay_period(self, text: str) -> str:
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        for month in months:
            if month.lower() in text.lower():
                year_m = re.search(rf'{month}\s+(\d{{4}})', text, re.IGNORECASE)
                return f"{month} {year_m.group(1)}" if year_m else month
        return 'N/A'

    def _classify_employment(self, gross_salary: float) -> str:
        if gross_salary >= 150000:
            return 'Senior / Executive'
        elif gross_salary >= 75000:
            return 'Mid-level Professional'
        elif gross_salary >= 30000:
            return 'Junior Professional'
        elif gross_salary > 0:
            return 'Entry Level'
        return 'Unknown'
