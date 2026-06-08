from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from authentication.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    StaffInviteSerializer,
    OrganizationSerializer
)
from authentication.models import Organization

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrganizationUsersViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_SUPER_ADMIN:
            return User.objects.all()
        if user.organization:
            return User.objects.filter(organization=user.organization)
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        if self.action == 'create':
            return StaffInviteSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        # Only Agency Admin and Super Admin can invite staff
        if request.user.role not in [User.ROLE_AGENCY_ADMIN, User.ROLE_SUPER_ADMIN]:
            return Response(
                {"detail": "You do not have permission to invite users to this organization."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = StaffInviteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
