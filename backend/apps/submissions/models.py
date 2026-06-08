import uuid
from django.db import models
from django.conf import settings
from authentication.models import Organization
from clients.models import Client

class Submission(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='submissions')
    country = models.CharField(max_length=100)
    visa_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_submissions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Submission {self.id} for {self.client.name} ({self.country})"

class Document(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Valid', 'Valid'),
        ('Invalid', 'Invalid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255, help_text="e.g., Passport, Bank Statement, Photo, ITR")
    file_url = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    file_size = models.IntegerField(help_text="File size in bytes", null=True, blank=True)
    file_type = models.CharField(max_length=100, help_text="e.g. application/pdf, image/png", null=True, blank=True)
    extracted_data = models.JSONField(default=dict, blank=True, help_text="OCR structured JSON output")
    validation_result = models.JSONField(default=dict, blank=True, help_text="Validation details from Rules Engine")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} for Submission {self.submission.id}"

class ValidationReport(models.Model):
    STATUS_CHOICES = [
        ('Passed', 'Passed'),
        ('Warning', 'Warning'),
        ('Failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='validation_report')
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Failed')
    correct_documents = models.JSONField(default=list, blank=True, help_text="List of successfully validated documents")
    missing_documents = models.JSONField(default=list, blank=True, help_text="List of missing required documents")
    issues = models.JSONField(default=list, blank=True, help_text="List of warning/error messages")
    recommendations = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for Submission {self.submission.id} (Score: {self.score})"

class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activities')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user.email if self.user else 'System'} at {self.timestamp}"
