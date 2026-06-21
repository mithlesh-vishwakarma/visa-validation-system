from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from eligibility.models import EligibilityScore
from eligibility.serializers import EligibilityScoreSerializer
from submissions.models import Submission
from authentication.models import User


class EligibilityScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for accessing AI eligibility assessment results.
    Scoped by organization — each user only sees their org's assessments.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EligibilityScoreSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return EligibilityScore.objects.all().order_by('-created_at')
        if user.organization:
            return EligibilityScore.objects.filter(
                submission__client__organization=user.organization
            ).order_by('-created_at')
        return EligibilityScore.objects.none()

    @action(detail=False, methods=['get'], url_path='by-submission/(?P<submission_id>[^/.]+)')
    def by_submission(self, request, submission_id=None):
        """Get the eligibility score for a specific submission."""
        try:
            submission = Submission.objects.get(id=submission_id)
            score = EligibilityScore.objects.get(submission=submission)
            return Response(EligibilityScoreSerializer(score).data)
        except Submission.DoesNotExist:
            return Response({"detail": "Submission not found."}, status=404)
        except EligibilityScore.DoesNotExist:
            return Response({"detail": "AI assessment has not been run yet. Use the ai_assess endpoint."}, status=404)
