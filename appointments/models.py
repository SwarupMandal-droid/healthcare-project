from django.db import models
from accounts.models import User
from doctors.models import DoctorProfile, TimeSlot

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    patient         = models.ForeignKey(
                          User, on_delete=models.CASCADE,
                          related_name='appointments')
    doctor          = models.ForeignKey(
                          DoctorProfile, on_delete=models.CASCADE,
                          related_name='appointments')
    time_slot       = models.OneToOneField(
                          TimeSlot, on_delete=models.SET_NULL,
                          null=True, related_name='appointment')
    appointment_date = models.DateField()
    start_time      = models.TimeField()
    end_time        = models.TimeField()
    symptoms        = models.TextField(blank=True)
    notes           = models.TextField(blank=True)
    status          = models.CharField(
                          max_length=15,
                          choices=STATUS_CHOICES,
                          default='pending')
    appointment_id  = models.CharField(
                          max_length=20, unique=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-start_time']

    def __str__(self):
        return (f"Appt #{self.appointment_id} — "
                f"{self.patient.get_full_name()} "
                f"with {self.doctor}")

    def save(self, *args, **kwargs):
        # Auto-generate appointment ID
        if not self.appointment_id:
            import random, string
            chars = string.ascii_uppercase + string.digits
            self.appointment_id = 'LC-' + ''.join(
                random.choices(chars, k=8))
        super().save(*args, **kwargs)


class Review(models.Model):
    appointment = models.OneToOneField(
                      Appointment, on_delete=models.CASCADE,
                      related_name='review')
    patient     = models.ForeignKey(
                      User, on_delete=models.CASCADE,
                      related_name='reviews')
    doctor      = models.ForeignKey(
                      DoctorProfile, on_delete=models.CASCADE,
                      related_name='reviews')
    rating      = models.PositiveIntegerField(
                      choices=[(i, i) for i in range(1, 6)])
    comment     = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"{self.patient.get_full_name()} → "
                f"{self.doctor} : {self.rating}★")