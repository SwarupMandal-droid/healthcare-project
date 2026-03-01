from django.db import models
from accounts.models import User

class ChatSession(models.Model):
    patient    = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='chat_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    is_active  = models.BooleanField(default=True)

    def __str__(self):
        return (f"Chat — {self.patient.get_full_name()} "
                f"@ {self.started_at:%Y-%m-%d %H:%M}")


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai',   'AI'),
    ]

    session    = models.ForeignKey(
                     ChatSession, on_delete=models.CASCADE,
                     related_name='messages')
    sender     = models.CharField(max_length=5, choices=SENDER_CHOICES)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.message[:50]}"