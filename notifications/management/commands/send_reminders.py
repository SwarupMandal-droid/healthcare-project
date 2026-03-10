from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from notifications.utils import notify_appt_reminder

class Command(BaseCommand):
    help = 'Sends reminders for appointments scheduled for tomorrow'

    def handle(self, *args, **options):
        # Find appointments for tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        appts = Appointment.objects.filter(
            appointment_date=tomorrow,
            status='confirmed'
        )

        count = 0
        for appt in appts:
            notify_appt_reminder(appt)
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {count} reminders for {tomorrow}'))
