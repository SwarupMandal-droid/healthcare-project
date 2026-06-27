import json
import datetime
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
import razorpay

from accounts.models import User
from doctors.models import DoctorProfile
from appointments.models import Appointment
from payments.models import Payment
from notifications.utils import (
    notify_appt_confirmed,
    notify_doctor_new_booking,
    notify_payment_success,
    notify_doctor_payment_received,
    notify_doctor_new_patient,
)

@csrf_exempt
def razorpay_webhook(request):
    """
    Handle Razorpay Webhooks (specifically order.paid or payment.captured)
    Ensures appointment creation even if user closes tab.
    """
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    payload = request.body.decode('utf-8')
    signature = request.headers.get('X-Razorpay-Signature')
    secret = settings.RAZORPAY_WEBHOOK_SECRET

    if not secret:
        # If secret is not set, we can't verify. For safety in production, fail.
        # But for development, we might want to log it.
        return HttpResponse("Webhook secret not configured", status=500)

    # 1. Verify Signature
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_webhook_signature(payload, signature, secret)
    except Exception as e:
        return HttpResponse(f"Signature verification failed: {e}", status=400)

    # 2. Parse Payload
    try:
        data = json.loads(payload)
        event = data.get('event')
        
        # We focus on order.paid to ensure we have the full booking context
        if event != 'order.paid':
            return HttpResponse("Event ignored")

        order_data = data['payload']['order']['entity']
        order_id = order_data['id']
        notes = order_data.get('notes', {})

        # 3. Idempotency Check
        if Payment.objects.filter(razorpay_order_id=order_id, status='success').exists():
            return HttpResponse("Appointment already created")

        # 4. Extract Data from Notes
        try:
            doctor_id = notes.get('doctor_id')
            patient_id = notes.get('patient_id')
            date_str = notes.get('date')
            time_str = notes.get('time')
            symptoms = notes.get('symptoms', '')
            user_notes = notes.get('notes', '')
            fee = notes.get('fee')

            if not all([doctor_id, patient_id, date_str, time_str]):
                return HttpResponse("Missing metadata in notes", status=400)

            doctor = DoctorProfile.objects.get(id=doctor_id)
            patient = User.objects.get(id=patient_id)
            appt_date = datetime.date.fromisoformat(date_str)
            start_time = datetime.time.fromisoformat(time_str)
            end_time = (
                datetime.datetime.combine(appt_date, start_time)
                + datetime.timedelta(minutes=30)
            ).time()

        except (DoctorProfile.DoesNotExist, User.DoesNotExist, ValueError) as e:
            return HttpResponse(f"Metadata resolution failed: {e}", status=400)

        # 5. Atomic Transaction for Creation
        with transaction.atomic():
            # Final check for slot again (could have been booked in parallel)
            if Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appt_date,
                start_time=start_time,
                status__in=['pending', 'confirmed']
            ).exists():
                # This is a collision. We should log this for manual refund/reschedule or handle it.
                # For now, we return 200 so Razorpay stops retrying, but we log the failed confirmation.
                return HttpResponse("Slot already taken, manual intervention required", status=200)

            appt = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appt_date,
                start_time=start_time,
                end_time=end_time,
                symptoms=symptoms,
                notes=user_notes,
                status='confirmed'
            )

            payment_id = data['payload'].get('payment', {}).get('entity', {}).get('id', '')

            payment_obj = Payment.objects.create(
                appointment=appt,
                patient=patient,
                amount=fee,
                method='webhook',
                status='success',
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
                paid_at=timezone.now(),
            )

        # 6. Success Notifications
        notify_appt_confirmed(appt)
        notify_doctor_new_booking(appt)
        notify_payment_success(payment_obj)
        notify_doctor_payment_received(payment_obj)

        if not Appointment.objects.filter(doctor=doctor, patient=patient).exclude(id=appt.id).exists():
            notify_doctor_new_patient(appt)

        return HttpResponse("Webhook processed successfully")

    except Exception as e:
        return HttpResponse(f"Internal Error: {e}", status=500)