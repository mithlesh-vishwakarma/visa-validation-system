"""
Eligibility Scoring Engine
============================
Computes a 5-category weighted eligibility score for a visa application.

Categories & Weights:
    financial_strength     (30%): bank balance, income, financial stability
    employment_stability   (25%): employment proof, salary consistency, tenure
    travel_history         (15%): countries visited, visa history, rejection-free
    documentation_quality  (15%): OCR confidence, completeness, anomaly count
    rule_compliance        (15%): country-specific rule pass rate

Final score = weighted sum (0–100).
Applicants scoring >= 70 with no HIGH-severity issues are considered eligible.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Scoring weights — must sum to 1.0
WEIGHTS = {
    "financial": 0.30,
    "employment": 0.25,
    "travel_history": 0.15,
    "documentation": 0.15,
    "compliance": 0.15,
}

# Minimum score threshold for eligibility determination
ELIGIBILITY_THRESHOLD = 70


def compute_eligibility(submission_data: dict) -> dict:
    """
    Compute the full eligibility assessment from submission data.

    Args:
        submission_data: {
            "documents": [...],          # Document model instances
            "country_rules": {...},       # CountryRule rules JSON
            "cross_validation": {...},    # Cross-validation results
            "validation_report": {...},   # Rules engine report
        }

    Returns:
        dict: Full eligibility assessment result
    """
    documents = submission_data.get('documents', [])
    country_rules = submission_data.get('country_rules', {})
    cross_val = submission_data.get('cross_validation', {})
    validation_report = submission_data.get('validation_report')

    # Build document AI analysis map
    doc_map = {}
    for doc in documents:
        if doc.category and doc.ai_analysis:
            doc_map[doc.category] = doc.ai_analysis

    # -----------------------------------------------------------------------
    # 1. Financial Strength Score (0–100)
    # -----------------------------------------------------------------------
    financial_score, financial_detail = _score_financial(doc_map, country_rules)

    # -----------------------------------------------------------------------
    # 2. Employment Stability Score (0–100)
    # -----------------------------------------------------------------------
    employment_score, employment_detail = _score_employment(doc_map)

    # -----------------------------------------------------------------------
    # 3. Travel History Score (0–100)
    # -----------------------------------------------------------------------
    travel_score, travel_detail = _score_travel_history(doc_map)

    # -----------------------------------------------------------------------
    # 4. Documentation Quality Score (0–100)
    # -----------------------------------------------------------------------
    documentation_score, documentation_detail = _score_documentation(documents)

    # -----------------------------------------------------------------------
    # 5. Rule Compliance Score (0–100)
    # -----------------------------------------------------------------------
    compliance_score, compliance_detail = _score_compliance(validation_report, cross_val)

    # -----------------------------------------------------------------------
    # Weighted Final Score
    # -----------------------------------------------------------------------
    weighted_scores = {
        "financial": financial_score * WEIGHTS["financial"],
        "employment": employment_score * WEIGHTS["employment"],
        "travel_history": travel_score * WEIGHTS["travel_history"],
        "documentation": documentation_score * WEIGHTS["documentation"],
        "compliance": compliance_score * WEIGHTS["compliance"],
    }
    final_score = round(sum(weighted_scores.values()))

    # -----------------------------------------------------------------------
    # Weighted Breakdown (detailed)
    # -----------------------------------------------------------------------
    weighted_breakdown = {
        "financial": {
            "score": financial_score,
            "weight": WEIGHTS["financial"],
            "contribution": round(weighted_scores["financial"], 1),
            "detail": financial_detail,
        },
        "employment": {
            "score": employment_score,
            "weight": WEIGHTS["employment"],
            "contribution": round(weighted_scores["employment"], 1),
            "detail": employment_detail,
        },
        "travel_history": {
            "score": travel_score,
            "weight": WEIGHTS["travel_history"],
            "contribution": round(weighted_scores["travel_history"], 1),
            "detail": travel_detail,
        },
        "documentation": {
            "score": documentation_score,
            "weight": WEIGHTS["documentation"],
            "contribution": round(weighted_scores["documentation"], 1),
            "detail": documentation_detail,
        },
        "compliance": {
            "score": compliance_score,
            "weight": WEIGHTS["compliance"],
            "contribution": round(weighted_scores["compliance"], 1),
            "detail": compliance_detail,
        },
    }

    # -----------------------------------------------------------------------
    # Risk Assessment
    # -----------------------------------------------------------------------
    from services.risk_engine import assess_risk
    risk_result = assess_risk(doc_map, cross_val, validation_report, final_score)

    # -----------------------------------------------------------------------
    # Strengths & Recommendations
    # -----------------------------------------------------------------------
    strengths = _identify_strengths(
        financial_score, employment_score, travel_score,
        documentation_score, compliance_score, doc_map
    )
    recommendations = _generate_recommendations(
        financial_score, employment_score, travel_score,
        documentation_score, compliance_score, doc_map, country_rules,
        risk_result.get('risk_factors', [])
    )

    # -----------------------------------------------------------------------
    # Eligibility Determination
    # -----------------------------------------------------------------------
    has_high_risk = any(
        r.get('severity') == 'HIGH'
        for r in risk_result.get('risk_factors', [])
    )
    is_eligible = final_score >= ELIGIBILITY_THRESHOLD and not has_high_risk
    eligibility_summary = _build_summary(final_score, is_eligible, risk_result['risk_level'], len(documents))

    return {
        "financial_score": financial_score,
        "employment_score": employment_score,
        "travel_history_score": travel_score,
        "documentation_score": documentation_score,
        "compliance_score": compliance_score,
        "final_score": final_score,
        "weighted_breakdown": weighted_breakdown,
        "risk_level": risk_result['risk_level'],
        "risk_factors": risk_result['risk_factors'],
        "strengths": strengths,
        "recommendations": recommendations,
        "is_eligible": is_eligible,
        "eligibility_summary": eligibility_summary,
        "cross_validation_results": cross_val,
    }


# ---------------------------------------------------------------------------
# Individual Scoring Functions
# ---------------------------------------------------------------------------

def _score_financial(doc_map: dict, country_rules: dict) -> tuple[int, str]:
    """Score financial strength from bank statement + salary slip data."""
    bank = doc_map.get('bank_statement', {})
    salary = doc_map.get('salary_slip', {})
    itr = doc_map.get('tax_return', {})

    if not bank and not salary:
        return 20, "No financial documents uploaded"

    score = 50  # Base
    details = []

    min_balance = country_rules.get('min_bank_balance', 300000)
    closing_balance = bank.get('closing_balance', 0) if bank else 0

    if closing_balance >= min_balance * 2:
        score += 30
        details.append(f"Strong balance: ₹{closing_balance:,.0f} (2x requirement)")
    elif closing_balance >= min_balance:
        score += 15
        details.append(f"Adequate balance: ₹{closing_balance:,.0f}")
    elif closing_balance > 0:
        score -= 20
        details.append(f"Low balance: ₹{closing_balance:,.0f} < ₹{min_balance:,.0f} required")
    else:
        score -= 30
        details.append("Balance information unavailable")

    # Salary boost
    gross_salary = salary.get('gross_salary', 0) if salary else 0
    if gross_salary >= 100000:
        score += 15
        details.append(f"High salary: ₹{gross_salary:,.0f}/month")
    elif gross_salary >= 50000:
        score += 8
        details.append(f"Good salary: ₹{gross_salary:,.0f}/month")
    elif gross_salary > 0:
        details.append(f"Salary: ₹{gross_salary:,.0f}/month")

    # Stability from bank statement
    stability = bank.get('financial_stability_score', 50) if bank else 50
    score = int(score * 0.7 + stability * 0.3)

    return max(0, min(100, score)), " | ".join(details) or "Financial data analyzed"


def _score_employment(doc_map: dict) -> tuple[int, str]:
    """Score employment stability from employment letter + salary slip."""
    emp = doc_map.get('employment_letter', {})
    salary = doc_map.get('salary_slip', {})

    if not emp and not salary:
        return 30, "No employment documents available"

    score = 50
    details = []

    if emp:
        tenure_years = emp.get('tenure_years') or 0
        is_permanent = emp.get('is_permanent', False)
        if tenure_years >= 3:
            score += 25
            details.append(f"Strong tenure: {tenure_years:.1f} years")
        elif tenure_years >= 1:
            score += 15
            details.append(f"Adequate tenure: {tenure_years:.1f} years")
        elif tenure_years > 0:
            score += 5
            details.append(f"Short tenure: {tenure_years:.1f} years")

        if is_permanent:
            score += 10
            details.append("Permanent employment")
        else:
            score -= 5
            details.append("Non-permanent employment")

    if salary:
        tier = salary.get('employment_tier', '')
        if 'Senior' in tier or 'Executive' in tier:
            score += 15
            details.append("Senior/Executive role")
        elif 'Mid-level' in tier:
            score += 8
            details.append("Mid-level role")
        pf = salary.get('pf_deducted', False)
        if pf:
            score += 5
            details.append("PF deduction confirmed (formal employment)")

    return max(0, min(100, score)), " | ".join(details) or "Employment data analyzed"


def _score_travel_history(doc_map: dict) -> tuple[int, str]:
    """Score travel history from travel history document."""
    travel = doc_map.get('travel_history', {})

    if not travel:
        # No travel history doc — use neutral score
        return 40, "No travel history document provided"

    travel_score = travel.get('travel_history_score', 40)
    countries_count = travel.get('total_countries_count', 0)
    has_rejection = travel.get('has_visa_rejections', False)

    details = []
    if countries_count > 0:
        details.append(f"{countries_count} countries visited")
    if has_rejection:
        details.append("Prior visa rejection noted")
        travel_score = max(0, travel_score - 20)
    schengen = travel.get('schengen_visits', [])
    if schengen:
        details.append(f"Schengen experience: {', '.join(schengen[:3])}")

    return max(0, min(100, travel_score)), " | ".join(details) or "Travel history analyzed"


def _score_documentation(documents: list) -> tuple[int, str]:
    """Score documentation quality based on OCR confidence and completeness."""
    if not documents:
        return 0, "No documents uploaded"

    total_confidence = sum(doc.confidence_score or 0 for doc in documents)
    avg_confidence = total_confidence / len(documents)

    # Count anomalies across all AI analyses
    total_anomalies = sum(
        len(doc.ai_analysis.get('anomalies', []))
        for doc in documents
        if doc.ai_analysis
    )

    score = int(avg_confidence * 80)  # Confidence contributes up to 80 pts
    score -= total_anomalies * 5      # Each anomaly costs 5 pts

    details = [
        f"Avg OCR confidence: {avg_confidence:.0%}",
        f"{len(documents)} documents uploaded",
        f"{total_anomalies} anomalies detected",
    ]

    return max(0, min(100, score)), " | ".join(details)


def _score_compliance(validation_report, cross_val: dict) -> tuple[int, str]:
    """Score compliance from rules engine + cross-validation results."""
    if not validation_report:
        return 50, "Validation not yet run"

    rules_score = getattr(validation_report, 'score', 50)
    cross_consistency = cross_val.get('consistency_score', 50)

    # Blend rules score (70%) + cross-validation (30%)
    blended = int(rules_score * 0.70 + cross_consistency * 0.30)

    status = getattr(validation_report, 'status', 'Unknown')
    missing = getattr(validation_report, 'missing_documents', [])
    details = [
        f"Rules engine: {rules_score}/100 ({status})",
        f"Cross-validation: {cross_consistency}/100",
    ]
    if missing:
        details.append(f"Missing docs: {', '.join(missing)}")

    return max(0, min(100, blended)), " | ".join(details)


# ---------------------------------------------------------------------------
# Strengths & Recommendations
# ---------------------------------------------------------------------------

def _identify_strengths(financial: int, employment: int, travel: int,
                         documentation: int, compliance: int, doc_map: dict) -> list:
    """Identify application strengths for the report."""
    strengths = []

    if financial >= 80:
        balance = doc_map.get('bank_statement', {}).get('closing_balance', 0)
        strengths.append(f"Strong financial profile with ₹{balance:,.0f} bank balance")
    if employment >= 80:
        emp = doc_map.get('employment_letter', {})
        company = emp.get('employer_name', 'N/A')
        tenure = emp.get('tenure_years', 0)
        strengths.append(f"Stable employment at {company} ({tenure:.1f} years)")
    if travel >= 75:
        travel_doc = doc_map.get('travel_history', {})
        count = travel_doc.get('total_countries_count', 0)
        strengths.append(f"Strong travel history with {count} countries visited")
    if documentation >= 80:
        strengths.append("High-quality documentation with strong OCR confidence")
    if compliance >= 80:
        strengths.append("Full compliance with country-specific visa requirements")
    if not strengths:
        strengths.append("Application submitted with required documentation")

    return strengths


def _generate_recommendations(
    financial: int, employment: int, travel: int,
    documentation: int, compliance: int, doc_map: dict,
    country_rules: dict, risk_factors: list
) -> list:
    """Generate actionable improvement recommendations."""
    recs = []

    if financial < 70:
        min_balance = country_rules.get('min_bank_balance', 300000)
        recs.append(f"Increase bank balance to at least ₹{min_balance:,.0f} before applying")
    if employment < 60:
        recs.append("Obtain an updated employment letter with salary details and joining date on company letterhead")
    if travel < 50 and not doc_map.get('travel_history'):
        recs.append("Provide travel history documentation including previous visa stamps or travel records")
    if documentation < 70:
        recs.append("Re-upload clearer, higher-quality scans of documents — ensure all text is legible")
    if compliance < 70:
        recs.append("Review and upload all required documents as per the country's visa requirements")

    # Risk-factor based recommendations
    for risk in risk_factors:
        if risk.get('severity') == 'HIGH':
            factor = risk.get('factor', '')
            if 'passport' in factor.lower():
                recs.append("Renew your passport immediately — expired or soon-expiring passport will cause visa rejection")
            elif 'name mismatch' in factor.lower():
                recs.append("Ensure your name is consistent across all documents (passport, bank, employment)")
            elif 'financial' in factor.lower():
                recs.append("Provide a bank explanation letter for large deposits/withdrawals in your statement")

    if not recs:
        recs.append("Your application looks strong — proceed with submission to the embassy/consulate")

    return recs


def _build_summary(final_score: int, is_eligible: bool, risk_level: str, doc_count: int) -> str:
    """Build a human-readable eligibility summary."""
    status = "ELIGIBLE" if is_eligible else "NOT ELIGIBLE"
    risk_desc = {"LOW": "low risk profile", "MEDIUM": "moderate risk profile", "HIGH": "high risk profile"}
    risk_text = risk_desc.get(risk_level, "unknown risk")

    if is_eligible:
        return (
            f"Based on analysis of {doc_count} document(s), this application scores {final_score}/100 "
            f"with a {risk_text}. The applicant appears {status} for the requested visa. "
            f"All major financial, employment, and documentation criteria have been met. "
            f"Proceed with embassy/consulate submission."
        )
    else:
        return (
            f"Based on analysis of {doc_count} document(s), this application scores {final_score}/100 "
            f"with a {risk_text}. The applicant is assessed as {status} at this time. "
            f"Please review the recommendations below and strengthen the application "
            f"before resubmitting to the embassy/consulate."
        )
