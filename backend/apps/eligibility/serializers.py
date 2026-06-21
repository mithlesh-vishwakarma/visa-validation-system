from rest_framework import serializers
from eligibility.models import EligibilityScore


class EligibilityScoreSerializer(serializers.ModelSerializer):
    """Serializer for the full AI eligibility assessment result."""

    class Meta:
        model = EligibilityScore
        fields = [
            'id',
            'submission',
            'financial_score',
            'employment_score',
            'travel_history_score',
            'documentation_score',
            'compliance_score',
            'final_score',
            'weighted_breakdown',
            'risk_level',
            'risk_factors',
            'cross_validation_results',
            'recommendations',
            'strengths',
            'is_eligible',
            'eligibility_summary',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
