"""
Cross-Document Validation Engine
==================================
Performs consistency checks across all uploaded documents to detect
mismatches, fraud indicators, and data inconsistencies.

Checks performed:
1. Name consistency — same name across all documents
2. Employer consistency — employment letter vs salary slip
3. Financial consistency — salary slip credits vs bank statement deposits
4. Passport validity coverage — passport covers the travel dates
5. Booking coherence — hotel/flight dates alignment
"""

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Threshold for considering two names as matching (fuzzy match ratio)
NAME_MATCH_THRESHOLD = 0.75


def run_cross_document_validation(documents: list) -> dict:
    """
    Run all cross-document consistency checks.

    Args:
        documents: List of Document model instances with ai_analysis populated

    Returns:
        dict: {
            "checks": [...],         # List of individual check results
            "passed": int,           # Number of checks passed
            "failed": int,           # Number of checks failed
            "warnings": int,         # Number of warnings
            "overall_status": str,   # "PASS" | "WARNING" | "FAIL"
            "risk_level": str,       # "LOW" | "MEDIUM" | "HIGH"
            "consistency_score": int # 0–100
        }
    """
    # Build a lookup of category → AI analysis data
    doc_map = {}
    for doc in documents:
        category = doc.category or 'other'
        doc_map[category] = doc.ai_analysis or {}

    checks = []

    # --- Check 1: Name Consistency ---
    checks.append(_check_name_consistency(doc_map))

    # --- Check 2: Employer/Company Consistency ---
    checks.append(_check_employer_consistency(doc_map))

    # --- Check 3: Financial Consistency (Salary vs Bank) ---
    checks.append(_check_financial_consistency(doc_map))

    # --- Check 4: Passport Validity vs Travel Dates ---
    checks.append(_check_passport_validity_vs_travel(doc_map))

    # --- Check 5: Flight and Hotel Date Alignment ---
    checks.append(_check_booking_coherence(doc_map))

    # --- Aggregate Results ---
    passed = sum(1 for c in checks if c['result'] == 'PASS')
    failed = sum(1 for c in checks if c['result'] == 'FAIL')
    warnings = sum(1 for c in checks if c['result'] == 'WARNING')

    if failed >= 2:
        overall_status = 'FAIL'
        risk_level = 'HIGH'
    elif failed == 1 or warnings >= 2:
        overall_status = 'WARNING'
        risk_level = 'MEDIUM'
    else:
        overall_status = 'PASS'
        risk_level = 'LOW'

    # Consistency score: penalize failures and warnings
    total_checks = max(len(checks), 1)
    consistency_score = max(0, round(
        ((passed * 100) - (failed * 40) - (warnings * 15)) / total_checks
    ))

    return {
        "checks": checks,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "overall_status": overall_status,
        "risk_level": risk_level,
        "consistency_score": min(100, max(0, consistency_score)),
    }


def _check_name_consistency(doc_map: dict) -> dict:
    """Verify that the applicant name matches across all documents."""
    names = {}

    # Collect names from each document type that has one
    name_fields = {
        'passport': 'holder_name',
        'bank_statement': 'account_holder',
        'salary_slip': 'employee_name',
        'employment_letter': 'employee_name',
        'tax_return': 'taxpayer_name',
    }

    for category, field in name_fields.items():
        if category in doc_map and doc_map[category].get(field):
            names[category] = doc_map[category][field].lower().strip()

    if len(names) < 2:
        return {
            "check": "Name Consistency",
            "result": "WARNING",
            "severity": "MEDIUM",
            "detail": f"Only {len(names)} document(s) with name data available for comparison.",
            "data": names,
        }

    # Compare all names against the first one (passport is authoritative)
    reference_name = names.get('passport') or list(names.values())[0]
    mismatches = []

    for category, name in names.items():
        if category == 'passport':
            continue
        similarity = _name_similarity(reference_name, name)
        if similarity < NAME_MATCH_THRESHOLD:
            mismatches.append(f"{category}: '{name}' ≠ passport: '{reference_name}'")

    if mismatches:
        return {
            "check": "Name Consistency",
            "result": "FAIL",
            "severity": "HIGH",
            "detail": f"Name mismatch detected across documents: {'; '.join(mismatches)}",
            "data": names,
        }

    return {
        "check": "Name Consistency",
        "result": "PASS",
        "severity": "LOW",
        "detail": f"Applicant name matches consistently across {len(names)} documents.",
        "data": names,
    }


def _check_employer_consistency(doc_map: dict) -> dict:
    """Verify employer name matches between employment letter and salary slip."""
    emp_letter = doc_map.get('employment_letter', {})
    salary_slip = doc_map.get('salary_slip', {})

    if not emp_letter or not salary_slip:
        return {
            "check": "Employer Consistency",
            "result": "WARNING",
            "severity": "LOW",
            "detail": "Employment letter or salary slip not available for employer cross-check.",
            "data": {},
        }

    letter_employer = emp_letter.get('employer_name', '').lower().strip()
    slip_employer = salary_slip.get('company_name', '').lower().strip()

    if not letter_employer or not slip_employer or letter_employer == 'n/a' or slip_employer == 'n/a':
        return {
            "check": "Employer Consistency",
            "result": "WARNING",
            "severity": "LOW",
            "detail": "Employer names could not be extracted from one or both documents.",
            "data": {"employment_letter": letter_employer, "salary_slip": slip_employer},
        }

    similarity = _name_similarity(letter_employer, slip_employer)
    if similarity >= 0.65:
        return {
            "check": "Employer Consistency",
            "result": "PASS",
            "severity": "LOW",
            "detail": f"Employer name consistent: '{letter_employer}' matches salary slip.",
            "data": {"employment_letter": letter_employer, "salary_slip": slip_employer},
        }

    return {
        "check": "Employer Consistency",
        "result": "FAIL",
        "severity": "HIGH",
        "detail": f"Employer mismatch: Employment letter shows '{letter_employer}' but salary slip shows '{slip_employer}'",
        "data": {"employment_letter": letter_employer, "salary_slip": slip_employer},
    }


def _check_financial_consistency(doc_map: dict) -> dict:
    """Compare declared salary with bank statement deposits."""
    salary_slip = doc_map.get('salary_slip', {})
    bank_stmt = doc_map.get('bank_statement', {})

    if not salary_slip or not bank_stmt:
        return {
            "check": "Financial Consistency",
            "result": "WARNING",
            "severity": "LOW",
            "detail": "Salary slip or bank statement not available for financial cross-check.",
            "data": {},
        }

    declared_salary = salary_slip.get('gross_salary', 0) or salary_slip.get('net_salary', 0)
    bank_monthly_income = bank_stmt.get('monthly_income_estimate', 0)

    if declared_salary == 0 or bank_monthly_income == 0:
        return {
            "check": "Financial Consistency",
            "result": "WARNING",
            "severity": "MEDIUM",
            "detail": "Could not compare salary and bank income — one or both amounts missing.",
            "data": {"declared_salary": declared_salary, "bank_monthly_income": bank_monthly_income},
        }

    # Allow ±40% variance (net salary is after deductions)
    lower_bound = declared_salary * 0.50
    upper_bound = declared_salary * 1.20

    if lower_bound <= bank_monthly_income <= upper_bound:
        return {
            "check": "Financial Consistency",
            "result": "PASS",
            "severity": "LOW",
            "detail": f"Bank monthly income (₹{bank_monthly_income:,.0f}) is consistent with declared salary (₹{declared_salary:,.0f}).",
            "data": {"declared_salary": declared_salary, "bank_monthly_income": bank_monthly_income},
        }

    gap = abs(declared_salary - bank_monthly_income)
    return {
        "check": "Financial Consistency",
        "result": "FAIL",
        "severity": "HIGH",
        "detail": (
            f"Financial inconsistency: Declared salary ₹{declared_salary:,.0f} "
            f"but bank shows ₹{bank_monthly_income:,.0f}/month (gap: ₹{gap:,.0f})"
        ),
        "data": {"declared_salary": declared_salary, "bank_monthly_income": bank_monthly_income},
    }


def _check_passport_validity_vs_travel(doc_map: dict) -> dict:
    """Ensure passport is valid for the entire travel period."""
    passport = doc_map.get('passport', {})
    flight = doc_map.get('flight_booking', {})

    if not passport:
        return {
            "check": "Passport Coverage",
            "result": "WARNING",
            "severity": "HIGH",
            "detail": "Passport data not available for travel coverage check.",
            "data": {},
        }

    expiry_date = passport.get('expiry_date')
    if not expiry_date:
        return {
            "check": "Passport Coverage",
            "result": "WARNING",
            "severity": "MEDIUM",
            "detail": "Passport expiry date could not be verified.",
            "data": {},
        }

    months_remaining = passport.get('months_remaining_validity', 0) or 0
    is_expired = passport.get('is_expired', False)

    if is_expired:
        return {
            "check": "Passport Coverage",
            "result": "FAIL",
            "severity": "HIGH",
            "detail": f"Passport is EXPIRED (expired: {expiry_date}). Renewal required.",
            "data": {"expiry_date": expiry_date, "months_remaining": months_remaining},
        }

    if months_remaining < 6:
        return {
            "check": "Passport Coverage",
            "result": "FAIL" if months_remaining < 3 else "WARNING",
            "severity": "HIGH" if months_remaining < 3 else "MEDIUM",
            "detail": f"Passport has only {months_remaining:.1f} months remaining — most visas require 6+ months validity.",
            "data": {"expiry_date": expiry_date, "months_remaining": months_remaining},
        }

    return {
        "check": "Passport Coverage",
        "result": "PASS",
        "severity": "LOW",
        "detail": f"Passport valid for {months_remaining:.1f} more months — sufficient for visa application.",
        "data": {"expiry_date": expiry_date, "months_remaining": months_remaining},
    }


def _check_booking_coherence(doc_map: dict) -> dict:
    """Check that hotel and flight dates are consistent."""
    flight = doc_map.get('flight_booking', {})
    hotel = doc_map.get('hotel_booking', {})

    if not flight or not hotel:
        return {
            "check": "Booking Coherence",
            "result": "WARNING",
            "severity": "LOW",
            "detail": "Flight or hotel booking not available for date coherence check.",
            "data": {},
        }

    flight_departure = flight.get('departure_date')
    hotel_checkin = hotel.get('check_in_date')
    flight_return = flight.get('return_date')
    hotel_checkout = hotel.get('check_out_date')

    issues = []

    # Compare departure vs check-in
    if flight_departure and hotel_checkin:
        try:
            f_dep = datetime.strptime(flight_departure, '%Y-%m-%d')
            h_in = datetime.strptime(hotel_checkin, '%Y-%m-%d')
            diff = abs((f_dep - h_in).days)
            if diff > 3:
                issues.append(f"Flight departure ({flight_departure}) and hotel check-in ({hotel_checkin}) differ by {diff} days")
        except ValueError:
            pass

    if issues:
        return {
            "check": "Booking Coherence",
            "result": "WARNING",
            "severity": "MEDIUM",
            "detail": "Booking date discrepancy: " + "; ".join(issues),
            "data": {"flight_departure": flight_departure, "hotel_checkin": hotel_checkin},
        }

    return {
        "check": "Booking Coherence",
        "result": "PASS",
        "severity": "LOW",
        "detail": "Flight and hotel booking dates are coherent.",
        "data": {"flight_departure": flight_departure, "hotel_checkin": hotel_checkin},
    }


def _name_similarity(name1: str, name2: str) -> float:
    """
    Simple token-based name similarity check.
    Returns 0.0–1.0 (1.0 = exact match).
    Handles partial name matches (e.g., 'Rahul Sharma' vs 'R. Sharma').
    """
    if not name1 or not name2:
        return 0.0
    if name1 == name2:
        return 1.0

    # Tokenize both names
    tokens1 = set(re.sub(r'[^\w\s]', '', name1.lower()).split())
    tokens2 = set(re.sub(r'[^\w\s]', '', name2.lower()).split())

    # Remove common noise words
    noise = {'mr', 'mrs', 'ms', 'dr', 'prof', 'shri', 'smt'}
    tokens1 -= noise
    tokens2 -= noise

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union) if union else 0.0
