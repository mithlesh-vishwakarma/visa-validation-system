from rest_framework import serializers
from submissions.models import Submission, Document, ValidationReport, ActivityLog
from clients.serializers import ClientSerializer
from eligibility.serializers import EligibilityScoreSerializer


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for uploaded visa documents including AI analysis fields."""

    class Meta:
        model = Document
        fields = [
            'id',
            'submission',
            'name',
            'category',         # New: document category slug
            'file_url',
            'status',
            'file_size',
            'file_type',
            'confidence_score', # New: OCR extraction confidence
            'extracted_data',
            'ai_analysis',      # New: deep AI structured analysis
            'validation_result',
            'created_at',
        ]
        read_only_fields = [
            'id', 'status', 'confidence_score', 'extracted_data',
            'ai_analysis', 'validation_result', 'created_at',
        ]


class ValidationReportSerializer(serializers.ModelSerializer):
    """Serializer for the rules-engine compliance report."""

    class Meta:
        model = ValidationReport
        fields = [
            'id',
            'submission',
            'score',
            'status',
            'correct_documents',
            'missing_documents',
            'issues',
            'recommendations',
            'created_at',
        ]
        read_only_fields = [
            'id', 'score', 'status', 'correct_documents',
            'missing_documents', 'issues', 'recommendations', 'created_at',
        ]


class SubmissionSerializer(serializers.ModelSerializer):
    """Full submission serializer including nested documents, reports, and AI scores."""
    client_detail = ClientSerializer(source='client', read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    validation_report = ValidationReportSerializer(read_only=True)
    eligibility_score = EligibilityScoreSerializer(read_only=True)  # New: AI eligibility
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id',
            'application_id',       # New: human-readable ID (APP-XXXXX)
            'client',
            'client_detail',
            'country',
            'visa_type',
            'status',
            'processing_status',    # New: AI pipeline status
            'processing_logs',      # New: timeline of events
            'created_by',
            'created_by_email',
            'created_at',
            'updated_at',
            'documents',
            'validation_report',
            'eligibility_score',    # New: AI eligibility assessment
        ]
        read_only_fields = [
            'id', 'application_id', 'status', 'processing_status',
            'processing_logs', 'created_by', 'created_at', 'updated_at',
            'documents', 'validation_report', 'eligibility_score',
        ]


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log entries."""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'user_email', 'organization', 'action', 'details', 'timestamp']
        read_only_fields = ['id', 'user', 'user_email', 'organization', 'timestamp']
