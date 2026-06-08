from rest_framework import viewsets, permissions
from clients.models import Client
from clients.serializers import ClientSerializer
from authentication.models import User

class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClientSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return Client.objects.all().order_by('-created_date')
        if user.organization:
            return Client.objects.filter(organization=user.organization).order_by('-created_date')
        return Client.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
