import uuid
from django.db import models
from authentication.models import Organization

class Client(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=255)
    passport_number = models.CharField(max_length=50)
    country = models.CharField(max_length=100)
    visa_type = models.CharField(max_length=100)
    mobile = models.CharField(max_length=50)
    email = models.EmailField()
    notes = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')

    def __str__(self):
        return f"{self.name} - {self.passport_number}"
