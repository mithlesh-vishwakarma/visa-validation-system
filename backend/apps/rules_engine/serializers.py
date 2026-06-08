from rest_framework import serializers
from rules_engine.models import CountryRule

class CountryRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryRule
        fields = ['id', 'country', 'visa_type', 'required_documents', 'rules', 'created_at', 'updated_at']
