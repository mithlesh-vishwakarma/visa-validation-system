import os
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
    ActivityLogSerializer
)
from clients.models import Client
from authentication.models import User

from utils.storage import upload_file
from services.ocr_service import extract_document_data
from services.rules_service import run_submission_validation
from services.report_service import generate_report_pdf

class SubmissionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return Submission.objects.all().order_by('-created_at')
        if user.organization:
            return Submission.objects.filter(client__organization=user.organization).order_by('-created_at')
        return Submission.objects.none()

    def perform_create(self, serializer):
        client_id = self.request.data.get('client')
        try:
            client = Client.objects.get(id=client_id)
            if client.organization != self.request.user.organization and self.request.user.role != User.ROLE_SUPER_ADMIN:
                raise permissions.exceptions.PermissionDenied("Client does not belong to your organization.")
        except Client.DoesNotExist:
            raise Http404("Client not found.")

        submission = serializer.save(created_by=self.request.user)
        
        # Log action
        ActivityLog.objects.create(
            user=self.request.user,
            organization=self.request.user.organization,
            action="Create Submission",
            details={
                "submission_id": str(submission.id),
                "client_name": client.name,
                "country": submission.country,
                "visa_type": submission.visa_type
            }
        )

    @action(detail=True, methods=['post'])
    def validate_rules(self, request, pk=None):
        submission = self.get_object()
        # Trigger rules validation
        report = run_submission_validation(submission.id)
        if report:
            return Response(ValidationReportSerializer(report).data)
        return Response({"detail": "Validation engine failed to run."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def download_report(self, request, pk=None):
        submission = self.get_object()
        try:
            report = submission.validation_report
        except ValidationReport.DoesNotExist:
            return Response({"detail": "Validation report does not exist. Run validation first."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate report to a file
        filename = f"report_{submission.id}.pdf"
        output_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        generate_report_pdf(report, output_path)

        if os.path.exists(output_path):
            return FileResponse(open(output_path, 'rb'), as_attachment=True, filename=filename)
        return Response({"detail": "Failed to generate PDF report."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return Document.objects.all()
        if user.organization:
            return Document.objects.filter(submission__client__organization=user.organization)
        return Document.objects.none()

    def create(self, request, *args, **kwargs):
        submission_id = request.data.get('submission')
        name = request.data.get('name')
        file_obj = request.FILES.get('file')

        if not submission_id or not name or not file_obj:
            return Response({"detail": "Submission ID, name, and file are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            submission = Submission.objects.get(id=submission_id)
            if submission.client.organization != request.user.organization and request.user.role != User.ROLE_SUPER_ADMIN:
                return Response({"detail": "Submission does not belong to your organization."}, status=status.HTTP_403_FORBIDDEN)
        except Submission.DoesNotExist:
            return Response({"detail": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)

        # Upload file using our helper service
        file_url = upload_file(file_obj, folder=f"documents/{submission_id}")

        # Save file locally first to read for OCR parsing
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, file_obj.name)
        
        # Write to temp path
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # Process OCR immediately
        extracted_data = {}
        try:
            extracted_data = extract_document_data(temp_file_path, name, file_obj.name)
        except Exception as e:
            # Fallback mock data
            from services.ocr_service import generate_mock_data
            extracted_data = generate_mock_data(name, file_obj.name)
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # Create Document instance
        document = Document.objects.create(
            submission=submission,
            name=name,
            file_url=file_url,
            file_size=file_obj.size,
            file_type=file_obj.content_type,
            status='Pending',
            extracted_data=extracted_data
        )

        # Update submission status to Pending when a document is uploaded
        submission.status = 'Pending'
        submission.save()

        # Log Activity
        ActivityLog.objects.create(
            user=request.user,
            organization=request.user.organization,
            action="Upload Document",
            details={
                "submission_id": str(submission.id),
                "document_id": str(document.id),
                "document_name": name,
                "file_name": file_obj.name
            }
        )

        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return ActivityLog.objects.all().order_by('-timestamp')
        if user.organization:
            return ActivityLog.objects.filter(organization=user.organization).order_by('-timestamp')
        return ActivityLog.objects.none()


class DashboardAnalyticsAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        org = user.organization

        if not org and user.role != User.ROLE_SUPER_ADMIN:
            return Response({"detail": "User has no active organization."}, status=status.HTTP_400_BAD_REQUEST)

        # Scope querysets
        if user.role == User.ROLE_SUPER_ADMIN:
            submissions = Submission.objects.all()
            clients = Client.objects.all()
            reports = ValidationReport.objects.all()
        else:
            submissions = Submission.objects.filter(client__organization=org)
            clients = Client.objects.filter(organization=org)
            reports = ValidationReport.objects.filter(submission__client__organization=org)

        # 1. Key Metrics Cards
        total_clients = clients.count()
        total_submissions = submissions.count()
        
        approved_count = submissions.filter(status='Approved').count()
        rejected_count = submissions.filter(status='Rejected').count()
        pending_count = submissions.filter(status='Pending').count()
        under_review_count = submissions.filter(status='Under Review').count()

        approval_rate = 0
        if total_submissions > 0:
            # Count Approved + Under Review as successful/active validations or strictly Approved
            approval_rate = round((approved_count / total_submissions) * 100, 1)

        avg_score = reports.aggregate(Avg('score'))['score__avg'] or 0
        avg_score = round(avg_score, 1)

        # 2. Submission Trends (grouped by month/status)
        # For simplicity in Django SQLite, we group by month
        trends = []
        # Query submissions by month
        for i in range(1, 13):
            month_subs = submissions.filter(created_at__month=i)
            if month_subs.exists() or i <= datetime.now().month:
                trends.append({
                    "month": datetime(2026, i, 1).strftime('%b'),
                    "submissions": month_subs.count(),
                    "approved": month_subs.filter(status='Approved').count(),
                    "rejected": month_subs.filter(status='Rejected').count(),
                })

        # 3. Country-wise Applications
        country_data = submissions.values('country').annotate(count=Count('id')).order_by('-count')
        country_stats = [{"country": item['country'], "value": item['count']} for item in country_data]

        # 4. Score Distribution
        score_ranges = {
            "0-59 (Fail)": reports.filter(score__lt=60).count(),
            "60-89 (Warning)": reports.filter(score__gte=60, score__lt=90).count(),
            "90-100 (Pass)": reports.filter(score__gte=90).count()
        }
        score_distribution = [{"range": k, "count": v} for k, v in score_ranges.items()]

        # 5. Recent Activity Logs
        if user.role == User.ROLE_SUPER_ADMIN:
            recent_logs = ActivityLog.objects.all().order_by('-timestamp')[:5]
        else:
            recent_logs = ActivityLog.objects.filter(organization=org).order_by('-timestamp')[:5]
            
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
                "avg_score": avg_score
            },
            "trends": trends,
            "countries": country_stats,
            "score_distribution": score_distribution,
            "recent_activity": recent_activity
        })
