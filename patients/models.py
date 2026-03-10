from django.db import models
from accounts.models import User

class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('male',   'Male'),
        ('female', 'Female'),
        ('other',  'Other'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+','AB+'),('AB-','AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user                = models.OneToOneField(
                              User, on_delete=models.CASCADE,
                              related_name='patient_profile')
    date_of_birth       = models.DateField(null=True, blank=True)
    gender              = models.CharField(
                              max_length=10,
                              choices=GENDER_CHOICES, blank=True)
    blood_group         = models.CharField(
                              max_length=5,
                              choices=BLOOD_GROUP_CHOICES, blank=True)
    address             = models.TextField(blank=True)
    allergies           = models.TextField(blank=True)
    chronic_conditions  = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    height_cm           = models.PositiveIntegerField(null=True, blank=True)
    weight_kg           = models.DecimalField(
                              max_digits=5, decimal_places=1,
                              null=True, blank=True)

    # Emergency contact
    emergency_name         = models.CharField(max_length=100, blank=True)
    emergency_phone        = models.CharField(max_length=15,  blank=True)
    emergency_relationship = models.CharField(max_length=50,  blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} (Patient)"

    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return (today.year - self.date_of_birth.year
                    - ((today.month, today.day)
                       < (self.date_of_birth.month, self.date_of_birth.day)))
        return None