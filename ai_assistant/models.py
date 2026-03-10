from django.db import models
from accounts.models import User


class ChatSession(models.Model):

    STATE_CHOICES = [
        ('idle',                    'Idle'),
        ('booking_select_spec',     'Booking - Select Specialization'),
        ('booking_select_doctor',   'Booking - Select Doctor'),
        ('booking_select_date',     'Booking - Select Date'),
        ('booking_select_slot',     'Booking - Select Time Slot'),
        ('booking_confirm',         'Booking - Confirm'),
        ('reschedule_select_appt',  'Reschedule - Select Appointment'),
        ('reschedule_select_date',  'Reschedule - Select New Date'),
        ('reschedule_select_slot',  'Reschedule - Select New Slot'),
        ('cancel_select_appt',      'Cancel - Select Appointment'),
        ('cancel_confirm',          'Cancel - Confirm'),
        ('symptom_check',           'Symptom Check'),
        ('registration',            'Registration'),
        ('awaiting_input',          'Awaiting Input'),
    ]

    patient    = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='chat_sessions')
    state      = models.CharField(
                     max_length=30,
                     choices=STATE_CHOICES,
                     default='idle')
    context    = models.JSONField(default=dict, blank=True)
    is_active  = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return (f"{self.patient.get_full_name()} "
                f"[{self.state}] @ {self.started_at:%Y-%m-%d %H:%M}")

    def set_state(self, new_state, context_update=None):
        self.state = new_state
        if context_update:
            self.context.update(context_update)
        self.save()

    def clear_context(self):
        self.context = {}
        self.state   = 'idle'
        self.save()


class ChatMessage(models.Model):

    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot',  'Bot'),
    ]

    session    = models.ForeignKey(
                     ChatSession, on_delete=models.CASCADE,
                     related_name='messages')
    sender     = models.CharField(
                     max_length=5, choices=SENDER_CHOICES)
    message    = models.TextField()
    intent     = models.CharField(
                     max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.message[:60]}"