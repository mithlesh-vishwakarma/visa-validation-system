"""
Submissions Views
==================
Handles visa application (submission) CRUD, document uploads,
AI assessment triggering, report generation, and dashboard analytics.
"""

import os
from datetime import datetime

from django.conf import settings
from django.http import FileResponse, Http404
from django.db.models import Avg, Count
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from submissions.models import Submission, Document, ValidationReport, ActivityLog
from submissions.serializers import (
    SubmissionSerializer,
    DocumentSerializer,
    ValidationReportSerializer,
    ActivityLogSerializer,
)
from clients.models import Client
from authentication.models import User

from utils.storage import upload_file
from services.ocr_service import extract_document_data, resolve_category
from services.rules_service import run_submission_validation
from services.report_service import generate_report_pdf


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    CRUD viewset for Visa Applications (Submissions).
    Scoped by organization — SUPER_ADMIN sees all, staff sees their org only.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return Submission.objects.all().order_by('-created_at')
        if user.organization:
            return Submission.objects.filter(
                client__organization=user.organization
            ).order_by('-created_at')
        return Submission.objects.none()

    def perform_create(self, serializer):
        client_id = self.request.data.get('client')
        try:
            client = Client.objects.get(id=client_id)
            if (client.organization != self.request.user.organization
                    and self.request.user.role != User.ROLE_SUPER_ADMIN):
                raise permissions.exceptions.PermissionDenied(
                    "Client does not belong to your organization."
                )
        except Client.DoesNotExist:
            raise Http404("Client not found.")

        submission = serializer.save(created_by=self.request.user)

        # Audit log: submission created
        ActivityLog.objects.create(
            user=self.request.user,
            organization=self.request.user.organization,
            action="Create Application",
            details={
                "submission_id": str(submission.id),
                "application_id": submission.application_id,
                "client_name": client.name,
                "country": submission.country,
                "visa_type": submission.visa_type,
            }
        )

    @action(detail=True, methods=['post'])
    def validate_rules(self, request, pk=None):
        """Run the rules engine validation on a submission."""
        submission = self.get_object()
        report = run_submission_validation(submission.id)
        if report:
            return Response(ValidationReportSerializer(report).data)
        return Response(
            {"detail": "Validation engine failed to run."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @action(detail=True, methods=['post'])
    def ai_assess(self, request, pk=None):
        """
        Trigger the full AI assessment pipeline for a submission.

        Steps:
        1. Run/refresh OCR + AI analysis on all documents
        2. Run cross-document validation
        3. Compute eligibility score (5 categories)
        4. Assess risk level
        5. Generate recommendations
        6. Save EligibilityScore to DB

        Returns the complete eligibility assessment JSON.
        """
        submission = self.get_object()

        # Guard: ensure at least one document exists
        if not submission.documents.exists():
            return Response(
                {"detail": "No documents uploaded. Please upload at least one document before running AI assessment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from services.ai_assessment import run_ai_assessment
        result = run_ai_assessment(str(submission.id))

        if 'error' in result:
            return Response(
                {"detail": result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Also run the rules engine to update ValidationReport
        run_submission_validation(submission.id)

        # Audit log
        ActivityLog.objects.create(
            user=request.user,
            organization=request.user.organization,
            action="AI Assessment",
            details={
                "submission_id": str(submission.id),
                "application_id": submission.application_id,
                "client_name": submission.client.name,
                "country": submission.country,
                "visa_type": submission.visa_type,
                "final_score": result.get('final_score', 0),
                "risk_level": result.get('risk_level', 'UNKNOWN'),
                "is_eligible": result.get('is_eligible', False),
            }
        )

        # Return updated submission with eligibility score
        submission.refresh_from_db()
        return Response(SubmissionSerializer(submission).data)

    @action(detail=True, methods=['get'])
    def processing_logs(self, request, pk=None):
        """Return the processing log timeline for a submission."""
        submission = self.get_object()
        return Response({
            "application_id": submission.application_id,
            "processing_status": submission.processing_status,
            "logs": submission.processing_logs or [],
        })

    @action(detail=True, methods=['get'])
    def download_report(self, request, pk=None):
        """Generate and download the enhanced PDF compliance + eligibility report."""
        submission = self.get_object()

        try:
            report = submission.validation_report
        except ValidationReport.DoesNotExist:
            return Response(
                {"detail": "Validation report not found. Run rules validation first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get eligibility score for enhanced report
        eligibility_score = None
        try:
            eligibility_score = submission.eligibility_score
        except Exception:
            pass

        filename = f"VisaFlow_Report_{submission.application_id}.pdf"
        output_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        generate_report_pdf(report, output_path, eligibility_score=eligibility_score)

        if os.path.exists(output_path):
            return FileResponse(
                open(output_path, 'rb'),
                as_attachment=True,
                filename=filename
            )
        return Response(
            {"detail": "Failed to generate PDF report."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DocumentViewSet(viewsets.ModelViewSet):
    """
    Handles document upload, OCR processing, and AI analysis.
    Supports PDF, PNG, JPG, JPEG, DOCX file types up to 10MB.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return Document.objects.all()
        if user.organization:
            return Document.objects.filter(
                submission__client__organization=user.organization
            )
        return Document.objects.none()

    def create(self, request, *args, **kwargs):
        """
        Upload a document to a submission with automatic OCR and AI analysis.

        Required fields:
            - submission: UUID of the target submission
            - name: Document type name (e.g., "Passport", "Bank Statement")
            - category: Category slug (optional, derived from name if not provided)
            - file: The file to upload
        """
        submission_id = request.data.get('submission')
        name = request.data.get('name')
        # Support explicit category from frontend or derive from name
        category = request.data.get('category') or resolve_category(name or '')
        file_obj = request.FILES.get('file')

        if not submission_id or not name or not file_obj:
            return Response(
                {"detail": "Submission ID, name, and file are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify submission belongs to user's organization
        try:
            submission = Submission.objects.get(id=submission_id)
            if (submission.client.organization != request.user.organization
                    and request.user.role != User.ROLE_SUPER_ADMIN):
                return Response(
                    {"detail": "Submission does not belong to your organization."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Submission.DoesNotExist:
            return Response(
                {"detail": "Submission not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Upload file to Supabase or local storage
        file_url = upload_file(file_obj, folder=f"documents/{submission_id}")

        # Save temp copy for OCR processing
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, file_obj.name)

        with open(temp_file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # Run OCR + AI analysis pipeline
        ocr_result = {}
        try:
            ocr_result = extract_document_data(
                temp_file_path, name, file_obj.name,
                existing_category=category
            )
        except Exception as e:
            from services.ocr_service import _build_mock_result
            ocr_result = _build_mock_result(category, name, file_obj.name)
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # Create Document record with all extracted data
        document = Document.objects.create(
            submission=submission,
            name=name,
            category=ocr_result.get('category', category),
            file_url=file_url,
            file_size=file_obj.size,
            file_type=file_obj.content_type,
            status='Pending',
            raw_text=ocr_result.get('raw_text', ''),
            confidence_score=ocr_result.get('confidence_score', 0.0),
            extracted_data=ocr_result.get('extracted_data', {}),
            ai_analysis=ocr_result.get('ai_analysis', {}),
        )

        # Update submission status to Pending
        submission.status = 'Pending'
        submission.save(update_fields=['status', 'updated_at'])

        # Audit log
        ActivityLog.objects.create(
            user=request.user,
            organization=request.user.organization,
            action="Upload Document",
            details={
                "submission_id": str(submission.id),
                "application_id": submission.application_id,
                "document_id": str(document.id),
                "document_name": name,
                "category": category,
                "file_name": file_obj.name,
                "confidence_score": ocr_result.get('confidence_score', 0.0),
            }
        )

        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for audit/activity logs."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return ActivityLog.objects.all().order_by('-timestamp')
        if user.organization:
            return ActivityLog.objects.filter(
                organization=user.organization
            ).order_by('-timestamp')
        return ActivityLog.objects.none()


class DashboardAnalyticsAPI(APIView):
    """
    Returns comprehensive dashboard analytics including AI assessment metrics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        org = user.organization

        if not org and user.role != User.ROLE_SUPER_ADMIN:
            return Response(
                {"detail": "User has no active organization."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Scope querysets by organization
        if user.role == User.ROLE_SUPER_ADMIN:
            submissions = Submission.objects.all()
            clients = Client.objects.all()
            reports = ValidationReport.objects.all()
        else:
            submissions = Submission.objects.filter(client__organization=org)
            clients = Client.objects.filter(organization=org)
            reports = ValidationReport.objects.filter(submission__client__organization=org)

        # --- Key Metrics ---
        total_clients = clients.count()
        total_submissions = submissions.count()
        approved_count = submissions.filter(status='Approved').count()
        rejected_count = submissions.filter(status='Rejected').count()
        pending_count = submissions.filter(status='Pending').count()
        under_review_count = submissions.filter(status='Under Review').count()

        approval_rate = 0
        if total_submissions > 0:
            approval_rate = round((approved_count / total_submissions) * 100, 1)

        avg_score = reports.aggregate(Avg('score'))['score__avg'] or 0
        avg_score = round(avg_score, 1)

        # --- AI Assessment Metrics ---
        from eligibility.models import EligibilityScore
        if user.role == User.ROLE_SUPER_ADMIN:
            eligibility_scores = EligibilityScore.objects.all()
        else:
            eligibility_scores = EligibilityScore.objects.filter(
                submission__client__organization=org
            )

        total_assessed = eligibility_scores.count()
        avg_eligibility = eligibility_scores.aggregate(Avg('final_score'))['final_score__avg'] or 0
        avg_eligibility = round(avg_eligibility, 1)

        risk_distribution = {
            'LOW': eligibility_scores.filter(risk_level='LOW').count(),
            'MEDIUM': eligibility_scores.filter(risk_level='MEDIUM').count(),
            'HIGH': eligibility_scores.filter(risk_level='HIGH').count(),
        }

        # --- Submission Trends (monthly) ---
        trends = []
        current_month = datetime.now().month
        for i in range(1, 13):
            month_subs = submissions.filter(created_at__month=i)
            if month_subs.exists() or i <= current_month:
                trends.append({
                    "month": datetime(2026, i, 1).strftime('%b'),
                    "submissions": month_subs.count(),
                    "approved": month_subs.filter(status='Approved').count(),
                    "rejected": month_subs.filter(status='Rejected').count(),
                })

        # --- Country Distribution ---
        country_data = submissions.values('country').annotate(
            count=Count('id')
        ).order_by('-count')
        country_stats = [{"country": item['country'], "value": item['count']} for item in country_data]

        # --- Score Distribution ---
        score_ranges = {
            "0-59 (Fail)": reports.filter(score__lt=60).count(),
            "60-89 (Warning)": reports.filter(score__gte=60, score__lt=90).count(),
            "90-100 (Pass)": reports.filter(score__gte=90).count(),
        }
        score_distribution = [{"range": k, "count": v} for k, v in score_ranges.items()]

        # --- Recent Activity ---
        if user.role == User.ROLE_SUPER_ADMIN:
            recent_logs = ActivityLog.objects.all().order_by('-timestamp')[:10]
        else:
            recent_logs = ActivityLog.objects.filter(
                organization=org
            ).order_by('-timestamp')[:10]
        recent_activity = ActivityLogSerializer(recent_logs, many=True).data

        return Response({
            "metrics": {
                "total_clients": total_clients,
                "total_submissions": total_submissions,
                "approved": approved_count,
                "rejected": rejected_count,
                "pending": pending_count,
                "under_review": under_review_count,
                "approval_rate": approval_rate,
                "avg_score": avg_score,
                # New AI metrics
                "total_ai_assessed": total_assessed,
                "avg_eligibility_score": avg_eligibility,
                "risk_distribution": risk_distribution,
            },
            "trends": trends,
            "countries": country_stats,
            "score_distribution": score_distribution,
            "recent_activity": recent_activity,
        })
