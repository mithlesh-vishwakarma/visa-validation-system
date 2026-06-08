import uuid
from django.db import models

class CountryRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.CharField(max_length=100)
    visa_type = models.CharField(max_length=100)
    required_documents = models.JSONField(help_text="List of document names e.g., ['Passport', 'Bank Statement']")
    rules = models.JSONField(help_text="Key-value pairs for rules, e.g., {'passport_min_validity_months': 6, 'min_bank_balance': 300000}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('country', 'visa_type')

    def __str__(self):
        return f"{self.country} - {self.visa_type}"
