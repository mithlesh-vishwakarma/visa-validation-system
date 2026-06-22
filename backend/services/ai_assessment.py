"""
AI Assessment Pipeline
========================
Orchestrates the complete AI eligibility assessment for a submission:

1. Run OCR (if not already done) on all documents
2. Run per-document AI analysis
3. Run cross-document validation
4. Run eligibility scoring engine
5. Save EligibilityScore to database
6. Update submission processing_status
7. Log all events

This is the main entry point called from the `ai_assess` API endpoint.
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def run_ai_assessment(submission_id: str) -> dict:
    """
    Execute the full AI assessment pipeline for a submission.

    Args:
        submission_id: UUID string of the Submission

    Returns:
        dict: Complete assessment result including eligibility score
    """
    from submissions.models import Submission, Document
    from rules_engine.models import CountryRule
    from services.cross_validation import run_cross_document_validation
    from services.eligibility_engine import compute_eligibility
    from eligibility.models import EligibilityScore

    try:
        submission = Submission.objects.select_related('client', 'created_by').get(id=submission_id)
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        return {"error": "Submission not found"}

    # Mark as processing
    submission.processing_status = 'processing'
    submission.save(update_fields=['processing_status', 'updated_at'])
    submission.add_processing_log("AI Assessment Started", {"submission_id": str(submission_id)})

    try:
        # --- Step 1: Ensure all documents have AI analysis ---
        documents = list(submission.documents.all())
        submission.add_processing_log("Document Analysis", {"doc_count": len(documents)})

        for doc in documents:
            if not doc.ai_analysis:
                _run_document_ai_analysis(doc)

        # --- Step 2: Cross-document validation ---
        submission.add_processing_log("Cross-Document Validation", {})
        cross_val_result = run_cross_document_validation(documents)

        # --- Step 3: Get country rules ---
        country_rules = {}
        try:
            rule = CountryRule.objects.get(
                country__iexact=submission.country,
                visa_type__iexact=submission.visa_type
            )
            country_rules = rule.rules
        except CountryRule.DoesNotExist:
            logger.warning(f"No country rules found for {submission.country} / {submission.visa_type}")

        # --- Step 4: Get existing validation report ---
        validation_report = None
        try:
            validation_report = submission.validation_report
        except Exception:
            pass

        # --- Step 5: Compute eligibility score ---
        submission.add_processing_log("Eligibility Scoring", {})
        assessment = compute_eligibility({
            "documents": documents,
            "country_rules": country_rules,
            "cross_validation": cross_val_result,
            "validation_report": validation_report,
        })

        # --- Step 6: Save EligibilityScore to DB ---
        eligibility_obj, created = EligibilityScore.objects.update_or_create(
            submission=submission,
            defaults={
                "financial_score": assessment["financial_score"],
                "employment_score": assessment["employment_score"],
                "travel_history_score": assessment["travel_history_score"],
                "documentation_score": assessment["documentation_score"],
                "compliance_score": assessment["compliance_score"],
                "final_score": assessment["final_score"],
                "weighted_breakdown": assessment["weighted_breakdown"],
                "risk_level": assessment["risk_level"],
                "risk_factors": assessment["risk_factors"],
                "cross_validation_results": cross_val_result,
                "recommendations": assessment["recommendations"],
                "strengths": assessment["strengths"],
                "is_eligible": assessment["is_eligible"],
                "eligibility_summary": assessment["eligibility_summary"],
            }
        )

        # --- Step 7: Update submission status ---
        submission.processing_status = 'completed'
        submission.save(update_fields=['processing_status', 'updated_at'])
        submission.add_processing_log("Assessment Complete", {
            "final_score": assessment["final_score"],
            "risk_level": assessment["risk_level"],
            "is_eligible": assessment["is_eligible"],
        })

        logger.info(
            f"AI assessment complete for {submission.application_id}: "
            f"score={assessment['final_score']}, risk={assessment['risk_level']}"
        )

        return assessment

    except Exception as e:
        logger.error(f"AI assessment failed for {submission_id}: {e}", exc_info=True)
        submission.processing_status = 'failed'
        submission.save(update_fields=['processing_status', 'updated_at'])
        submission.add_processing_log("Assessment Failed", {"error": str(e)})
        return {"error": str(e)}


def _run_document_ai_analysis(doc) -> None:
    """
    Run AI analysis on a single document that hasn't been analyzed yet.
    Updates the document's ai_analysis and confidence_score fields.
    """
    from services.ai_provider import get_ai_provider

    try:
        raw_text = doc.raw_text or ""
        extracted_data = doc.extracted_data or {}
        category = doc.category or 'other'

        ai_provider = get_ai_provider()
        ai_analysis = ai_provider.analyze_document(category, raw_text, extracted_data)

        doc.ai_analysis = ai_analysis
        doc.confidence_score = ai_analysis.get('confidence', 0.5)
        doc.save(update_fields=['ai_analysis', 'confidence_score'])

        logger.info(f"AI analysis complete for document {doc.id} ({category})")
    except Exception as e:
        logger.error(f"Document AI analysis failed for {doc.id}: {e}")
