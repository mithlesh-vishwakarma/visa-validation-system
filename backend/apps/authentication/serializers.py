from rest_framework import serializers
from django.contrib.auth import get_user_model
from authentication.models import Organization

User = get_user_model()

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'organization', 'organization_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']

class UserRegistrationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'organization_name']

    def create(self, validated_data):
        org_name = validated_data.pop('organization_name')
        password = validated_data.pop('password')
        
        # Create Organization
        org = Organization.objects.create(name=org_name)
        
        # Create User with role Agency Admin
        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=User.ROLE_AGENCY_ADMIN,
            organization=org
        )
        return user

class StaffInviteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role']

    def validate_role(self, value):
        if value == User.ROLE_SUPER_ADMIN:
            raise serializers.ValidationError("Cannot invite Super Admin.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        request = self.context.get('request')
        current_user = request.user if request else None
        
        if not current_user or not current_user.organization:
            raise serializers.ValidationError("Inviting user must belong to an organization.")

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', User.ROLE_STAFF),
            organization=current_user.organization
        )
        return user
