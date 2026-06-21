"""
Risk Assessment Engine
========================
Detects risk factors across all uploaded documents and assigns severity levels.

Risk Factors Detected:
    HIGH:   Expired passport, name mismatch across docs, suspicious financial activity
    MEDIUM: Insufficient bank balance, low employment tenure, missing key docs
    LOW:    Weak travel history, low OCR confidence, short cover letter

Risk Levels:
    HIGH   = Any HIGH-severity factor present
    MEDIUM = 2+ MEDIUM factors or 1 MEDIUM + any other
    LOW    = Only LOW-severity or minor issues
"""

import logging

logger = logging.getLogger(__name__)


def assess_risk(
    doc_map: dict,
    cross_validation: dict,
    validation_report,
    final_score: int
) -> dict:
    """
    Run full risk assessment and return risk level + factor list.

    Args:
        doc_map: Category slug → AI analysis dict
        cross_validation: Cross-document validation results
        validation_report: ValidationReport model instance (or None)
        final_score: Computed eligibility score (0–100)

    Returns:
        dict: {risk_level, risk_factors}
    """
    risk_factors = []

    # -----------------------------------------------------------------------
    # HIGH SEVERITY checks
    # -----------------------------------------------------------------------

    # 1. Expired passport
    passport = doc_map.get('passport', {})
    if passport.get('is_expired'):
        risk_factors.append({
            "factor": "Expired Passport",
            "severity": "HIGH",
            "detail": f"Passport expired on {passport.get('expiry_date', 'unknown date')}. Immediate renewal required.",
            "category": "passport",
        })
    elif passport.get('expiring_soon') or (passport.get('months_remaining_validity') or 12) < 6:
        months = passport.get('months_remaining_validity', 0)
        risk_factors.append({
            "factor": "Passport Expiring Soon",
            "severity": "HIGH",
            "detail": f"Passport expires in {months:.1f} months — most countries require 6+ months validity.",
            "category": "passport",
        })

    # 2. Name mismatch (from cross-validation)
    for check in cross_validation.get('checks', []):
        if check.get('check') == 'Name Consistency' and check.get('result') == 'FAIL':
            risk_factors.append({
                "factor": "Name Mismatch Across Documents",
                "severity": "HIGH",
                "detail": check.get('detail', 'Applicant name does not match across submitted documents.'),
                "category": "cross_validation",
            })

    # 3. Employer mismatch
    for check in cross_validation.get('checks', []):
        if check.get('check') == 'Employer Consistency' and check.get('result') == 'FAIL':
            risk_factors.append({
                "factor": "Employer Mismatch",
                "severity": "HIGH",
                "detail": check.get('detail', 'Employer name differs between employment letter and salary slip.'),
                "category": "cross_validation",
            })

    # 4. Suspicious financial activity (large unexplained deposits)
    bank = doc_map.get('bank_statement', {})
    if bank.get('large_deposits_count', 0) >= 3:
        risk_factors.append({
            "factor": "Suspicious Financial Activity",
            "severity": "HIGH",
            "detail": f"Multiple large deposits detected ({bank['large_deposits_count']}). May indicate fund parking — embassy may request source of funds explanation.",
            "category": "bank_statement",
        })

    # 5. Financial inconsistency (salary vs bank)
    for check in cross_validation.get('checks', []):
        if check.get('check') == 'Financial Consistency' and check.get('result') == 'FAIL':
            risk_factors.append({
                "factor": "Income-Bank Inconsistency",
                "severity": "HIGH",
                "detail": check.get('detail', 'Significant gap between declared salary and bank statement deposits.'),
                "category": "cross_validation",
            })

    # -----------------------------------------------------------------------
    # MEDIUM SEVERITY checks
    # -----------------------------------------------------------------------

    # 6. Insufficient bank balance
    if validation_report:
        issues = getattr(validation_report, 'issues', [])
        for issue in issues:
            if 'bank balance' in issue.lower() and 'below' in issue.lower():
                risk_factors.append({
                    "factor": "Insufficient Bank Balance",
                    "severity": "MEDIUM",
                    "detail": issue,
                    "category": "bank_statement",
                })

    # 7. Missing required documents
    if validation_report:
        missing = getattr(validation_report, 'missing_documents', [])
        if missing:
            risk_factors.append({
                "factor": "Missing Required Documents",
                "severity": "MEDIUM",
                "detail": f"Required documents not uploaded: {', '.join(missing)}",
                "category": "documents",
            })

    # 8. Short employment tenure
    emp = doc_map.get('employment_letter', {})
    tenure = emp.get('tenure_years') or 0
    if emp and 0 < tenure < 0.5:
        risk_factors.append({
            "factor": "Short Employment Tenure",
            "severity": "MEDIUM",
            "detail": f"Employment tenure of {tenure:.1f} years may be insufficient. Most consulates expect 1+ years.",
            "category": "employment_letter",
        })

    # 9. No return ticket
    flight = doc_map.get('flight_booking', {})
    if flight and not flight.get('is_return_ticket', True):
        risk_factors.append({
            "factor": "No Return Ticket",
            "severity": "MEDIUM",
            "detail": "Only one-way flight booking detected. Return ticket is typically required for tourist visas.",
            "category": "flight_booking",
        })

    # -----------------------------------------------------------------------
    # LOW SEVERITY checks
    # -----------------------------------------------------------------------

    # 10. No travel history
    travel = doc_map.get('travel_history', {})
    if travel and travel.get('total_countries_count', 0) == 0:
        risk_factors.append({
            "factor": "No International Travel History",
            "severity": "LOW",
            "detail": "Applicant has no prior international travel history. First-time applicants may face additional scrutiny.",
            "category": "travel_history",
        })
    elif not travel and 'travel_history' not in doc_map:
        risk_factors.append({
            "factor": "Travel History Not Provided",
            "severity": "LOW",
            "detail": "No travel history document uploaded. Providing travel history can strengthen the application.",
            "category": "travel_history",
        })

    # 11. Low overall score
    if final_score < 50:
        risk_factors.append({
            "factor": "Low Eligibility Score",
            "severity": "MEDIUM",
            "detail": f"Overall eligibility score of {final_score}/100 is below the recommended 70+ threshold.",
            "category": "overall",
        })

    # -----------------------------------------------------------------------
    # Determine Overall Risk Level
    # -----------------------------------------------------------------------
    high_count = sum(1 for r in risk_factors if r['severity'] == 'HIGH')
    medium_count = sum(1 for r in risk_factors if r['severity'] == 'MEDIUM')

    if high_count >= 1:
        risk_level = 'HIGH'
    elif medium_count >= 2:
        risk_level = 'HIGH'
    elif medium_count == 1:
        risk_level = 'MEDIUM'
    elif risk_factors:
        risk_level = 'LOW'
    else:
        risk_level = 'LOW'

    return {
        "risk_level": risk_level,
        "risk_factors": risk_factors,
    }
