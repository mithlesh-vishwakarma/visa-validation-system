"""Employment Letter Analyzer — extracts employer, position, tenure, and salary details."""

import re
from datetime import datetime
from services.document_analyzers.base import BaseAnalyzer


class EmploymentLetterAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''

        employer = extracted_data.get('company_name') or self._extract_employer(text)
        employee_name = extracted_data.get('name') or self._extract_employee_name(text)
        designation = extracted_data.get('designation') or self._extract_designation(text)

        joining_date = self.extract_date(text, ['joining date', 'date of joining', 'commencement', 'joined on', 'employment from'])
        letter_date = self.extract_date(text, ['date', 'dated'])

        annual_salary = (
            extracted_data.get('salary', 0) * 12
            or self.extract_amount(text, ['annual salary', 'annual ctc', 'annual compensation', 'per annum', 'pa'], 0.0)
        )
        monthly_salary = self.extract_amount(text, ['monthly salary', 'monthly ctc', 'per month', 'pm'], annual_salary / 12 if annual_salary else 0.0)

        # Calculate tenure
        tenure_years = None
        if joining_date:
            try:
                join_dt = datetime.strptime(joining_date, '%Y-%m-%d')
                tenure_years = round((datetime.now() - join_dt).days / 365.25, 1)
            except ValueError:
                pass

        employment_type = self._classify_employment_type(text)
        is_permanent = 'permanent' in text.lower() or 'full-time' in text.lower()
        on_company_letterhead = self._check_letterhead(text)

        anomalies = self.detect_anomalies([
            (not employer or employer == 'N/A', "Employer name not found in letter"),
            (not joining_date, "Joining date not found in employment letter"),
            (not on_company_letterhead, "Letter does not appear to be on official company letterhead"),
            (tenure_years is not None and tenure_years < 0.5, "Employment tenure is less than 6 months — may be insufficient for visa"),
        ])

        return {
            "document_type": "employment_letter",
            "employer_name": employer,
            "employee_name": employee_name,
            "designation": designation,
            "joining_date": joining_date,
            "letter_date": letter_date,
            "tenure_years": tenure_years,
            "annual_salary": round(annual_salary, 2),
            "monthly_salary": round(monthly_salary, 2),
            "employment_type": employment_type,
            "is_permanent": is_permanent,
            "on_letterhead": on_company_letterhead,
            "anomalies": anomalies,
            "confidence": 0.80 if employer != 'N/A' else 0.45,
        }

    def _extract_employer(self, text: str) -> str:
        patterns = [
            r'(?:from|by|issued by|this is to certify that|employed with|working with)\s+([A-Z][a-zA-Z\s&,\.]{3,60}(?:Ltd|Pvt|Inc|Corp|Limited|Private|Solutions|Technologies|Services|Consulting)?)',
            r'^([A-Z][A-Za-z\s&\.]{5,60}(?:Ltd|Pvt|Inc|Corp|Limited))',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip().rstrip(',').rstrip('.')
        return 'N/A'

    def _extract_employee_name(self, text: str) -> str:
        patterns = [
            r'(?:mr\.|mrs\.|ms\.|dr\.)\s+([A-Z][a-zA-Z\s]{2,40})',
            r'certify that\s+(?:mr\.|mrs\.|ms\.)?\s*([A-Z][a-zA-Z\s]{2,40})\s+is',
            r'employee\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,40})',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return 'N/A'

    def _extract_designation(self, text: str) -> str:
        m = re.search(
            r'(?:designation|position|post|role|title|working as)\s*(?:of|is|as)?\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,50})',
            text, re.IGNORECASE
        )
        return m.group(1).strip() if m else 'N/A'

    def _classify_employment_type(self, text: str) -> str:
        if any(kw in text.lower() for kw in ['permanent', 'full-time', 'full time', 'regular']):
            return 'Permanent / Full-Time'
        elif any(kw in text.lower() for kw in ['contract', 'contractual']):
            return 'Contractual'
        elif any(kw in text.lower() for kw in ['part-time', 'part time']):
            return 'Part-Time'
        elif 'probation' in text.lower():
            return 'Probationary'
        return 'Unknown'

    def _check_letterhead(self, text: str) -> bool:
        """Heuristic: check for company name + address at top."""
        first_200 = text[:200].lower()
        return any(kw in first_200 for kw in ['ltd', 'pvt', 'inc', 'corp', 'limited', 'technologies', 'solutions'])
