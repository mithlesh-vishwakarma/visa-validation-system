import uuid
import random
import string
from django.db import models
from django.conf import settings
from authentication.models import Organization
from clients.models import Client


def generate_application_id():
    """Generate a human-readable application ID like APP-A3K9X."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"APP-{suffix}"


class Submission(models.Model):
    """
    Represents a visa application submission for a client.
    Each submission ties together all documents, OCR results, AI analysis,
    eligibility scores, and reports for a single visa application attempt.
    """
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Human-readable application ID (e.g., APP-A3K9X) for easy reference
    application_id = models.CharField(
        max_length=20, unique=True, default=generate_application_id,
        help_text="Human-readable application reference ID"
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='submissions')
    country = models.CharField(max_length=100)
    visa_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    # Tracks where the AI pipeline currently stands for this submission
    processing_status = models.CharField(
        max_length=20, choices=PROCESSING_STATUS_CHOICES, default='pending',
        help_text="Current AI processing pipeline status"
    )
    # Processing logs store a timeline of events for audit/debug purposes
    processing_logs = models.JSONField(
        default=list, blank=True,
        help_text="Ordered list of processing events: [{timestamp, event, details}]"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_submissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.application_id} — {self.client.name} ({self.country})"

    def add_processing_log(self, event: str, details: dict = None):
        """Append a timestamped event to the processing_logs JSON field."""
        from django.utils import timezone
        entry = {
            "timestamp": timezone.now().isoformat(),
            "event": event,
            "details": details or {}
        }
        logs = self.processing_logs or []
        logs.append(entry)
        self.processing_logs = logs
        self.save(update_fields=['processing_logs', 'updated_at'])


class Document(models.Model):
    """
    Represents a single uploaded document within a visa submission.
    Stores the file reference, OCR extracted text, structured AI analysis,
    and validation results from the rules engine.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Valid', 'Valid'),
        ('Invalid', 'Invalid'),
    ]

    # Standardized document category slugs used by OCR and AI analyzers
    CATEGORY_CHOICES = [
        ('passport', 'Passport'),
        ('bank_statement', 'Bank Statement'),
        ('salary_slip', 'Salary Slip'),
        ('employment_letter', 'Employment Letter'),
        ('tax_return', 'Tax Return / ITR'),
        ('travel_history', 'Travel History'),
        ('invitation_letter', 'Invitation Letter'),
        ('hotel_booking', 'Hotel Booking'),
        ('flight_booking', 'Flight Booking / Reservation'),
        ('cover_letter', 'Cover Letter'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255, help_text="Display name, e.g. 'Passport'")
    # Slug category for routing to the correct AI analyzer
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default='other',
        help_text="Document category slug used for AI routing"
    )
    file_url = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    file_size = models.IntegerField(help_text="File size in bytes", null=True, blank=True)
    file_type = models.CharField(max_length=100, help_text="MIME type e.g. application/pdf", null=True, blank=True)

    # Raw text from OCR extraction (pdfplumber / image OCR)
    raw_text = models.TextField(blank=True, default='', help_text="Full raw OCR text extracted from document")
    # OCR confidence score 0.0–1.0 (1.0 = perfect extraction)
    confidence_score = models.FloatField(default=0.0, help_text="OCR extraction confidence score 0.0–1.0")

    # Structured data extracted via regex/heuristics from the raw OCR text
    extracted_data = models.JSONField(default=dict, blank=True, help_text="OCR structured JSON output")
    # Detailed AI analysis output (entity extraction, anomalies, flags)
    ai_analysis = models.JSONField(
        default=dict, blank=True,
        help_text="AI-powered structured analysis result for this document"
    )
    validation_result = models.JSONField(default=dict, blank=True, help_text="Rules engine validation details")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} [{self.category}] for Submission {self.submission.id}"


class ValidationReport(models.Model):
    """
    Rules-engine compliance report for a submission.
    Stores document-level pass/fail results and overall score.
    Enhanced by the AI eligibility engine for deeper analysis.
    """
    STATUS_CHOICES = [
        ('Passed', 'Passed'),
        ('Warning', 'Warning'),
        ('Failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='validation_report')
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Failed')
    correct_documents = models.JSONField(default=list, blank=True)
    missing_documents = models.JSONField(default=list, blank=True)
    issues = models.JSONField(default=list, blank=True)
    recommendations = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.submission.application_id} (Score: {self.score})"


class ActivityLog(models.Model):
    """Audit log entry for all user and system actions within an organization."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='activities'
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user.email if self.user else 'System'} at {self.timestamp}"
