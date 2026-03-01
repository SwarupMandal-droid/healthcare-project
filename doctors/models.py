from django.db import models
from accounts.models import User

class Specialization(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True)
    icon        = models.CharField(max_length=100, default='fas fa-stethoscope')
    bg_color    = models.CharField(max_length=20, default='#EFF6FF')
    text_color  = models.CharField(max_length=20, default='#2563EB')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def doctor_count(self):
        return DoctorProfile.objects.filter(
            specialization=self, is_available=True
        ).count()


class DoctorProfile(models.Model):
    user             = models.OneToOneField(
                           User, on_delete=models.CASCADE,
                           related_name='doctor_profile')
    specialization   = models.ForeignKey(
                           Specialization, on_delete=models.SET_NULL,
                           null=True, related_name='doctors')
    license_number   = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(
                           max_digits=8, decimal_places=2, default=500)
    bio              = models.TextField(blank=True)
    clinic_name      = models.CharField(max_length=200, blank=True)
    clinic_address   = models.TextField(blank=True)
    is_verified      = models.BooleanField(default=False)
    is_available     = models.BooleanField(default=True)
    rating           = models.DecimalField(
                           max_digits=3, decimal_places=1, default=0.0)
    total_reviews    = models.PositiveIntegerField(default=0)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    def average_rating(self):
        from appointments.models import Review
        reviews = Review.objects.filter(doctor=self)
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            return round(total / reviews.count(), 1)
        return 0.0


class DoctorAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),    (1, 'Tuesday'),
        (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'),    (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    doctor     = models.ForeignKey(
                     DoctorProfile, on_delete=models.CASCADE,
                     related_name='availability')
    day        = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time   = models.TimeField()
    is_active  = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day')
        ordering        = ['day']

    def __str__(self):
        return (f"{self.doctor} — "
                f"{self.get_day_display()} "
                f"{self.start_time}–{self.end_time}")


class TimeSlot(models.Model):
    doctor     = models.ForeignKey(
                     DoctorProfile, on_delete=models.CASCADE,
                     related_name='time_slots')
    date       = models.DateField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    is_booked  = models.BooleanField(default=False)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time')
        ordering        = ['date', 'start_time']

    def __str__(self):
        return (f"{self.doctor} | "
                f"{self.date} "
                f"{self.start_time}–{self.end_time}")


class PatientDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('prescription', 'Prescription'),
        ('lab_report',   'Lab Report'),
        ('diet_chart',   'Diet Chart'),
        ('medical_notes','Medical Notes'),
        ('xray',         'X-Ray'),
        ('other',        'Other'),
    ]

    doctor      = models.ForeignKey(
                      DoctorProfile, on_delete=models.CASCADE,
                      related_name='uploaded_documents')
    patient     = models.ForeignKey(
                      User, on_delete=models.CASCADE,
                      related_name='documents')
    appointment = models.ForeignKey(
                      'appointments.Appointment',
                      on_delete=models.SET_NULL,
                      null=True, blank=True,
                      related_name='documents')
    doc_type    = models.CharField(
                      max_length=20, choices=DOC_TYPE_CHOICES)
    title       = models.CharField(max_length=200)
    file        = models.FileField(upload_to='documents/%Y/%m/')
    notes       = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return (f"{self.get_doc_type_display()} — "
                f"{self.patient.get_full_name()}")

    def filename(self):
        import os
        return os.path.basename(self.file.name)

    def extension(self):
        import os
        return os.path.splitext(self.file.name)[1].upper().replace('.', '')