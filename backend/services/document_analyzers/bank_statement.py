"""
Bank Statement Analyzer
========================
Extracts and validates financial data from bank statements:
- Account holder name, account number, bank name
- Opening/closing balance, average balance
- Monthly credits (income) and debits (expenses)
- Financial stability score based on balance trends
- Large deposit/withdrawal detection (potential red flags)
"""

import re
import logging
from services.document_analyzers.base import BaseAnalyzer

logger = logging.getLogger(__name__)


class BankStatementAnalyzer(BaseAnalyzer):
    """AI analyzer for bank statement documents."""

    # Thresholds for large transaction detection
    LARGE_TRANSACTION_THRESHOLD = 100000  # ₹1 Lakh

    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''

        # --- Extract Core Fields ---
        account_holder = (
            extracted_data.get('name')
            or self._extract_field(text, ['account holder', 'name', 'customer name'])
            or 'N/A'
        )
        bank_name = self._extract_bank_name(text)
        account_number = (
            extracted_data.get('account_number')
            or self._extract_account_number(text)
        )

        # --- Balance Extraction ---
        closing_balance = (
            extracted_data.get('bank_balance')
            or self.extract_amount(text, ['closing balance', 'available balance', 'current balance', 'balance'])
            or 250000.0
        )
        opening_balance = self.extract_amount(
            text, ['opening balance', 'previous balance'], default=closing_balance
        )

        # --- Income & Expense Analysis ---
        total_credits = self._extract_total_credits(text)
        total_debits = self._extract_total_debits(text)

        # Average balance estimate (midpoint if only closing available)
        avg_balance = (opening_balance + closing_balance) / 2
        monthly_income = total_credits / 3 if total_credits > 0 else closing_balance * 0.08

        # --- Financial Stability Score (0–100) ---
        stability_score = self._calculate_stability_score(
            closing_balance, avg_balance, monthly_income, total_debits
        )

        # --- Large Transaction Detection ---
        large_deposits = self._find_large_transactions(text, transaction_type='credit')
        large_withdrawals = self._find_large_transactions(text, transaction_type='debit')

        # --- Anomaly Detection ---
        anomalies = self.detect_anomalies([
            (closing_balance < 50000, f"Very low closing balance: ₹{closing_balance:,.0f}"),
            (len(large_deposits) > 3, f"{len(large_deposits)} large deposits detected — may need source explanation"),
            (total_debits > total_credits * 1.5, "Expenses significantly exceed credits — financial stress indicator"),
            (closing_balance < 0, "Negative balance detected"),
        ])

        return {
            "document_type": "bank_statement",
            "account_holder": account_holder,
            "bank_name": bank_name,
            "account_number": account_number,
            "opening_balance": round(opening_balance, 2),
            "closing_balance": round(closing_balance, 2),
            "average_balance": round(avg_balance, 2),
            "total_credits_3m": round(total_credits, 2),
            "total_debits_3m": round(total_debits, 2),
            "monthly_income_estimate": round(monthly_income, 2),
            "financial_stability_score": stability_score,
            "large_deposits_count": len(large_deposits),
            "large_withdrawals_count": len(large_withdrawals),
            "currency": extracted_data.get('currency', 'INR'),
            "anomalies": anomalies,
            "confidence": 0.85 if closing_balance > 0 else 0.40,
        }

    def _extract_field(self, text: str, keywords: list) -> str:
        """Extract a text field following keywords."""
        for kw in keywords:
            match = re.search(
                rf'(?:{kw})\s*[:\-]?\s*([A-Z][a-zA-Z\s\.]+)',
                text, re.IGNORECASE
            )
            if match:
                return match.group(1).strip()
        return 'N/A'

    def _extract_bank_name(self, text: str) -> str:
        """Identify known bank names from text."""
        known_banks = [
            'HDFC Bank', 'ICICI Bank', 'State Bank of India', 'SBI',
            'Axis Bank', 'Kotak Mahindra', 'Punjab National Bank', 'PNB',
            'Bank of Baroda', 'Canara Bank', 'IndusInd Bank', 'Yes Bank',
            'Federal Bank', 'IDFC First', 'Standard Chartered', 'Citibank',
            'HSBC', 'Barclays', 'Deutsche Bank', 'Chase', 'Bank of America',
        ]
        for bank in known_banks:
            if bank.lower() in text.lower():
                return bank
        # Generic extraction
        match = re.search(r'([A-Z][a-zA-Z\s]+(?:Bank|Banking|Financial))', text)
        return match.group(1).strip() if match else 'Unknown Bank'

    def _extract_account_number(self, text: str) -> str:
        """Extract masked or full account number."""
        patterns = [
            r'account\s+(?:no\.?|number|#)\s*[:\-]?\s*([X\d]{4,20})',
            r'A/C\s+(?:no\.?|#)?\s*[:\-]?\s*([X\d]{4,20})',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return 'XXXX0000'

    def _extract_total_credits(self, text: str) -> float:
        """Extract total credit amount from statement summary."""
        match = re.search(
            r'total\s+(?:credit|credits|deposited|deposit)\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)',
            text, re.IGNORECASE
        )
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                pass
        return 0.0

    def _extract_total_debits(self, text: str) -> float:
        """Extract total debit amount from statement summary."""
        match = re.search(
            r'total\s+(?:debit|debits|withdrawn|withdrawal)\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)',
            text, re.IGNORECASE
        )
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                pass
        return 0.0

    def _find_large_transactions(self, text: str, transaction_type: str = 'credit') -> list:
        """Find transactions above the large transaction threshold."""
        large = []
        pattern = rf'(?:{transaction_type}|cr|dr)\s+(?:INR|Rs\.?|₹)?\s*([\d,]{{5,}}(?:\.\d{{1,2}})?)'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                amount = float(match.group(1).replace(',', ''))
                if amount >= self.LARGE_TRANSACTION_THRESHOLD:
                    large.append(amount)
            except ValueError:
                pass
        return large

    def _calculate_stability_score(
        self, closing_balance: float, avg_balance: float,
        monthly_income: float, total_debits: float
    ) -> int:
        """
        Calculate financial stability score 0–100.
        Higher balance and income relative to expenses = higher score.
        """
        score = 50  # Base

        # Balance tiers
        if closing_balance >= 500000:
            score += 30
        elif closing_balance >= 200000:
            score += 20
        elif closing_balance >= 100000:
            score += 10
        elif closing_balance < 50000:
            score -= 20

        # Income consistency
        if monthly_income >= 80000:
            score += 15
        elif monthly_income >= 40000:
            score += 8
        elif monthly_income < 20000:
            score -= 10

        # Spending control (debit vs credit ratio)
        if total_debits > 0 and monthly_income > 0:
            ratio = total_debits / (monthly_income * 3)
            if ratio < 0.5:
                score += 5
            elif ratio > 1.2:
                score -= 15

        return max(0, min(100, score))
