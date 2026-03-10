from django.db import models
from accounts.models import User


class Notification(models.Model):

    TYPE_CHOICES = [
        # Patient - Appointment
        ('appt_confirmed',     'Appointment Confirmed'),
        ('appt_reminder_24h',  'Appointment Reminder 24h'),
        ('appt_reminder_1h',   'Appointment Reminder 1h'),
        ('appt_rescheduled',   'Appointment Rescheduled'),
        ('appt_cancelled_doc', 'Appointment Cancelled by Doctor'),
        ('appt_completed',     'Appointment Completed'),
        # Patient - Payment
        ('payment_success',    'Payment Successful'),
        ('payment_failed',     'Payment Failed'),
        ('payment_refund',     'Refund Processed'),
        # Patient - Doctor
        ('doctor_available',   'Doctor Available Today'),
        ('new_doctor',         'New Doctor Added'),
        # Patient - Health
        ('prescription_uploaded', 'Prescription Uploaded'),
        ('diet_plan_ready',    'Diet Plan Ready'),
        ('profile_reminder',   'Profile Update Reminder'),
        # Doctor - Appointment
        ('new_booking',        'New Appointment Booked'),
        ('appt_cancelled_pat', 'Appointment Cancelled by Patient'),
        ('appt_reminder_30m',  'Appointment Reminder 30min'),
        ('reschedule_request', 'Reschedule Request'),
        # Doctor - Payment
        ('payment_received',   'Payment Received'),
        ('daily_earnings',     'Daily Earnings Summary'),
        # Doctor - System
        ('new_patient',        'New Patient Registered'),
        ('review_received',    'Review Received'),
        ('profile_verified',   'Profile Verified'),
        # Admin
        ('new_doctor_reg',     'New Doctor Registration'),
        ('doctor_verify_req',  'Doctor Verification Request'),
        ('high_traffic',       'High Appointment Traffic'),
        ('payment_issue',      'Payment Issue'),
        ('system_alert',       'System Alert'),
    ]

    CATEGORY_CHOICES = [
        ('appointment', 'Appointment'),
        ('payment',     'Payment'),
        ('health',      'Health'),
        ('system',      'System'),
    ]

    user       = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='notifications')
    type       = models.CharField(max_length=30, choices=TYPE_CHOICES)
    category   = models.CharField(
                     max_length=15, choices=CATEGORY_CHOICES,
                     default='system')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    link       = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.title}"

    @property
    def icon(self):
        icons = {
            'appointment': 'fas fa-calendar-check',
            'payment':     'fas fa-rupee-sign',
            'health':      'fas fa-heartbeat',
            'system':      'fas fa-bell',
        }
        return icons.get(self.category, 'fas fa-bell')

    @property
    def color(self):
        colors = {
            'appointment': '#2563EB',
            'payment':     '#059669',
            'health':      '#DC2626',
            'system':      '#D97706',
        }
        return colors.get(self.category, '#6B7280')

    @property
    def bg_color(self):
        colors = {
            'appointment': '#EFF6FF',
            'payment':     '#D1FAE5',
            'health':      '#FEE2E2',
            'system':      '#FEF3C7',
        }
        return colors.get(self.category, '#F3F4F6')