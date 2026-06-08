import logging
from datetime import datetime
from submissions.models import Submission, Document, ValidationReport, ActivityLog
from rules_engine.models import CountryRule

logger = logging.getLogger(__name__)

def run_submission_validation(submission_id):
    """
    Retrieves the submission, applies the rules matching its country and visa type,
    calculates validation score, identifies issues/missing documents,
    creates/updates the ValidationReport, and updates DB objects.
    """
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found.")
        return None

    # Get country rule
    try:
        country_rule = CountryRule.objects.get(country=submission.country, visa_type=submission.visa_type)
    except CountryRule.DoesNotExist:
        # Create a default generic rule if not found
        country_rule = CountryRule(
            country=submission.country,
            visa_type=submission.visa_type,
            required_documents=['Passport', 'Bank Statement'],
            rules={'passport_min_validity_months': 6, 'min_bank_balance': 300000}
        )
        country_rule.save()

    required_docs = country_rule.required_documents
    rules_config = country_rule.rules

    # Get uploaded documents
    uploaded_docs = submission.documents.all()
    uploaded_dict = {doc.name.lower().strip(): doc for doc in uploaded_docs}

    correct_documents = []
    missing_documents = []
    issues = []
    recommendations_list = []
    
    score = 100
    
    # 1. Check Missing Documents
    for req_doc in required_docs:
        req_doc_clean = req_doc.lower().strip()
        if req_doc_clean not in uploaded_dict:
            missing_documents.append(req_doc)
            issues.append(f"Missing required document: {req_doc}")
            score -= 20
            recommendations_list.append(f"Please upload a valid {req_doc}.")
        else:
            # Document is present
            doc = uploaded_dict[req_doc_clean]
            
            # Check file size validation (max 5MB for MVP)
            if doc.file_size and doc.file_size > 5 * 1024 * 1024:
                doc.status = 'Invalid'
                doc.validation_result = {"error": "File size exceeds 5MB limit"}
                doc.save()
                issues.append(f"Document {doc.name} exceeds maximum file size (5MB).")
                score -= 10
                recommendations_list.append(f"Please re-upload {doc.name} under 5MB.")
                continue

            # Standard validations on extracted data
            doc_is_valid = True
            doc_errors = []

            extracted = doc.extracted_data or {}
            
            # Specific Rules: Passport
            if 'passport' in req_doc_clean:
                expiry_str = extracted.get('expiry_date')
                if expiry_str:
                    try:
                        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
                        months_left = (expiry_date - datetime.now()).days / 30.0
                        min_months = rules_config.get('passport_min_validity_months', 6)
                        
                        if expiry_date < datetime.now():
                            doc_is_valid = False
                            doc_errors.append("Passport is expired")
                            issues.append(f"Passport is expired (Expired on: {expiry_str})")
                            score -= 40
                            recommendations_list.append("Your passport is expired. Please renew your passport before applying.")
                        elif months_left < min_months:
                            doc_is_valid = False
                            doc_errors.append(f"Passport validity is less than {min_months} months")
                            issues.append(f"Passport validity is less than {min_months} months (Expires: {expiry_str})")
                            score -= 30
                            recommendations_list.append(f"Your passport must be valid for at least {min_months} months.")
                    except ValueError:
                        doc_is_valid = False
                        doc_errors.append("Passport expiry date format invalid")
                        issues.append(f"Could not parse expiry date '{expiry_str}' in Passport")
                        score -= 15
                else:
                    doc_is_valid = False
                    doc_errors.append("Passport expiry date missing in OCR data")
                    issues.append("OCR could not extract expiry date from Passport")
                    score -= 15

            # Specific Rules: Bank Statement
            elif 'bank statement' in req_doc_clean:
                balance = extracted.get('bank_balance')
                min_balance = rules_config.get('min_bank_balance', 300000)
                if balance is not None:
                    if balance < min_balance:
                        doc_is_valid = False
                        doc_errors.append("Bank balance is below minimum requirement")
                        issues.append(f"Bank balance (₹{int(balance):,}) is below the minimum requirement of ₹{min_balance:,} for {submission.country}")
                        score -= 30
                        recommendations_list.append(f"Please deposit funds or provide an alternative statement showing a balance of at least ₹{min_balance:,}.")
                else:
                    doc_is_valid = False
                    doc_errors.append("Bank balance missing in statement text")
                    issues.append("OCR could not extract closing balance from Bank Statement")
                    score -= 15
                    recommendations_list.append("Please upload a bank statement that clearly displays the closing balance.")

            # Update document status based on validation
            if doc_is_valid:
                doc.status = 'Valid'
                doc.validation_result = {"status": "Passed", "details": "All checks passed successfully."}
                correct_documents.append(doc.name)
            else:
                doc.status = 'Invalid'
                doc.validation_result = {"status": "Failed", "errors": doc_errors}
                
            doc.save()

    # Double check other documents not required but uploaded, default to Valid
    for key, doc in uploaded_dict.items():
        if doc.name not in correct_documents and doc.status == 'Pending':
            doc.status = 'Valid'
            doc.validation_result = {"status": "Passed", "details": "Uploaded document accepted."}
            doc.save()
            correct_documents.append(doc.name)

    # Clean score bounds
    score = max(0, min(100, score))

    # Calculate status
    if score >= 90 and len(missing_documents) == 0:
        status = 'Passed'
        submission.status = 'Under Review'
    elif score >= 60 and 'Passport' not in missing_documents and not any("expired" in issue.lower() for issue in issues):
        status = 'Warning'
        submission.status = 'Under Review'
    else:
        status = 'Failed'
        submission.status = 'Rejected'

    submission.save()

    # Build Recommendations
    if status == 'Passed':
        recommendations = "Your documentation is highly compliant. Ready for submission to the embassy."
    else:
        recommendations = " ".join(recommendations_list) if recommendations_list else "Please review document requirements and re-upload invalid items."

    # Update or create validation report
    report, created = ValidationReport.objects.update_or_create(
        submission=submission,
        defaults={
            'score': score,
            'status': status,
            'correct_documents': correct_documents,
            'missing_documents': missing_documents,
            'issues': issues,
            'recommendations': recommendations
        }
    )

    # Audit log
    ActivityLog.objects.create(
        user=submission.created_by,
        organization=submission.client.organization,
        action="Document Validation",
        details={
            "submission_id": str(submission.id),
            "client_name": submission.client.name,
            "country": submission.country,
            "visa_type": submission.visa_type,
            "score": score,
            "status": status,
            "issues_count": len(issues)
        }
    )

    return report
