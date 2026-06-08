from rest_framework import serializers
from submissions.models import Submission, Document, ValidationReport, ActivityLog
from clients.serializers import ClientSerializer

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 
            'submission', 
            'name', 
            'file_url', 
            'status', 
            'file_size', 
            'file_type', 
            'extracted_data', 
            'validation_result', 
            'created_at'
        ]
        read_only_fields = ['id', 'status', 'extracted_data', 'validation_result', 'created_at']

class ValidationReportSerializer(serializers.ModelSerializer):
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
            'created_at'
        ]
        read_only_fields = ['id', 'score', 'status', 'correct_documents', 'missing_documents', 'issues', 'recommendations', 'created_at']

class SubmissionSerializer(serializers.ModelSerializer):
    client_detail = ClientSerializer(source='client', read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    validation_report = ValidationReportSerializer(read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 
            'client', 
            'client_detail', 
            'country', 
            'visa_type', 
            'status', 
            'created_by', 
            'created_by_email', 
            'created_at', 
            'updated_at', 
            'documents', 
            'validation_report'
        ]
        read_only_fields = ['id', 'status', 'created_by', 'created_at', 'updated_at', 'documents', 'validation_report']

class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'user_email', 'organization', 'action', 'details', 'timestamp']
        read_only_fields = ['id', 'user', 'user_email', 'organization', 'timestamp']
