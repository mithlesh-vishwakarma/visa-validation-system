from rest_framework import serializers
from clients.models import Client

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'id', 
            'organization', 
            'name', 
            'passport_number', 
            'country', 
            'visa_type', 
            'mobile', 
            'email', 
            'notes', 
            'created_date', 
            'status'
        ]
        read_only_fields = ['id', 'organization', 'created_date', 'status']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.organization:
            validated_data['organization'] = request.user.organization
        return super().create(validated_data)
