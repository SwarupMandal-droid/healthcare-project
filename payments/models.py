from django.db import models
from accounts.models import User
from appointments.models import Appointment

class Payment(models.Model):
    METHOD_CHOICES = [
        ('upi',  'UPI'),
        ('card', 'Card'),
    ]

    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('refunded', 'Refunded'),
    ]

    appointment      = models.OneToOneField(
                           Appointment, on_delete=models.CASCADE,
                           related_name='payment')
    patient          = models.ForeignKey(
                           User, on_delete=models.CASCADE,
                           related_name='payments')
    amount           = models.DecimalField(
                           max_digits=10, decimal_places=2)
    method           = models.CharField(
                           max_length=10, choices=METHOD_CHOICES)
    status           = models.CharField(
                           max_length=15,
                           choices=STATUS_CHOICES,
                           default='pending')
    transaction_id   = models.CharField(
                           max_length=100, unique=True, blank=True)
    razorpay_order_id   = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    upi_id           = models.CharField(max_length=100, blank=True)
    paid_at          = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"Payment #{self.transaction_id} — "
                f"₹{self.amount} — {self.status}")

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import random, string
            chars = string.ascii_uppercase + string.digits
            self.transaction_id = 'TXN-' + ''.join(
                random.choices(chars, k=10))
        super().save(*args, **kwargs)