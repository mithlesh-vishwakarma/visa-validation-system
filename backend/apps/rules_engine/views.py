from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rules_engine.models import CountryRule
from rules_engine.serializers import CountryRuleSerializer
from authentication.models import User

class CountryRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CountryRuleSerializer
    queryset = CountryRule.objects.all().order_by('country', 'visa_type')

    def get_permissions(self):
        # Allow listing and viewing rules to any authenticated staff, but edit only to admins
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.user.role not in [User.ROLE_SUPER_ADMIN, User.ROLE_AGENCY_ADMIN]:
            self.permission_denied(request, message="Only admins can manage country rules.")
            
    def create(self, request, *args, **kwargs):
        if request.user.role not in [User.ROLE_SUPER_ADMIN, User.ROLE_AGENCY_ADMIN]:
            return Response({"detail": "Only admins can manage country rules."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.role not in [User.ROLE_SUPER_ADMIN, User.ROLE_AGENCY_ADMIN]:
            return Response({"detail": "Only admins can manage country rules."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role not in [User.ROLE_SUPER_ADMIN, User.ROLE_AGENCY_ADMIN]:
            return Response({"detail": "Only admins can manage country rules."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
