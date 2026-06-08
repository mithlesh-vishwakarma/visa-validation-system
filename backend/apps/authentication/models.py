import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Ensure username is populated
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ROLE_SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
    ROLE_AGENCY_ADMIN = 'AGENCY_ADMIN'
    ROLE_STAFF = 'STAFF'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_AGENCY_ADMIN, 'Agency Admin'),
        (ROLE_STAFF, 'Staff'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    email = models.EmailField(unique=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"
