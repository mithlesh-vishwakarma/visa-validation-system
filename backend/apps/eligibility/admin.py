from django.contrib import admin
from eligibility.models import EligibilityScore


@admin.register(EligibilityScore)
class EligibilityScoreAdmin(admin.ModelAdmin):
    list_display = ['submission', 'final_score', 'risk_level', 'is_eligible', 'created_at']
    list_filter = ['risk_level', 'is_eligible']
    search_fields = ['submission__application_id', 'submission__client__name']
    readonly_fields = ['created_at', 'updated_at']
