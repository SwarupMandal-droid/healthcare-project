from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor',  'Doctor'),
        ('admin',   'Admin'),
    ]

    role            = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone           = models.CharField(max_length=15, blank=True)
    profile_photo   = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def is_doctor(self):
        return self.role == 'doctor'

    def is_patient(self):
        return self.role == 'patient'

    def is_admin_user(self):
        return self.role == 'admin'