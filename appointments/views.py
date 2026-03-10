from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from doctors.models import DoctorProfile, TimeSlot
from appointments.models import Appointment
from payments.models import Payment
import datetime
import json
import razorpay
from notifications.utils import (
    notify_appt_confirmed,
    notify_doctor_new_booking,
    notify_payment_success,
    notify_doctor_payment_received,
    notify_appt_completed,
    notify_doctor_appt_cancelled,
    notify_doctor_new_patient,
)

# ── Razorpay Client ───────────────────────────────────────────────────────────
def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID,
              settings.RAZORPAY_KEY_SECRET)
    )


# ── Helper: generate time slots ───────────────────────────────────────────────
def generate_slots(doctor, date):
    """
    Generate 30-minute slots based on doctor availability
    for a given date, excluding already booked ones.
    """
    from doctors.models import DoctorAvailability

    day_of_week = date.weekday()  # 0=Monday … 6=Sunday

    try:
        availability = DoctorAvailability.objects.get(
            doctor=doctor, day=day_of_week, is_active=True
        )
    except DoctorAvailability.DoesNotExist:
        return []

    # Build 30-min slot list
    slots      = []
    start      = datetime.datetime.combine(date, availability.start_time)
    end        = datetime.datetime.combine(date, availability.end_time)
    slot_delta = datetime.timedelta(minutes=30)

    # Already booked slots for this doctor/date
    booked = set(
        Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status__in=['pending', 'confirmed']
        ).values_list('start_time', flat=True)
    )

    now = datetime.datetime.now()

    while start + slot_delta <= end:
        slot_dt   = start
        slot_time = slot_dt.time()
        is_booked = slot_time in booked
        is_past   = (date == datetime.date.today()
                     and slot_dt <= now)

        slots.append({
            'time':      slot_time.strftime('%H:%M'),
            'label':     slot_time.strftime('%I:%M %p'),
            'available': not is_booked and not is_past,
        })
        start += slot_delta

    return slots


# ── Book Appointment (multi-step) ─────────────────────────────────────────────
@login_required
def book_appointment(request, doctor_id):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    doctor = get_object_or_404(
        DoctorProfile, id=doctor_id, is_available=True
    )

    # Next 14 days for date picker
    today     = datetime.date.today()
    date_list = []
    for i in range(1, 15):
        d           = today + datetime.timedelta(days=i)
        day_of_week = d.weekday()
        from doctors.models import DoctorAvailability
        is_working  = DoctorAvailability.objects.filter(
            doctor=doctor, day=day_of_week, is_active=True
        ).exists()
        date_list.append({
            'date':       d,
            'label':      d.strftime('%a'),
            'day':        d.strftime('%d'),
            'month':      d.strftime('%b'),
            'is_working': is_working,
            'value':      d.isoformat(),
        })

    context = {
        'doctor':    doctor,
        'date_list': date_list,
        'today':     today,
    }
    return render(request, 'appointments/book.html', context)


# ── AJAX: Get slots for selected date ─────────────────────────────────────────
def get_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date_str  = request.GET.get('date')

    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
        date   = datetime.date.fromisoformat(date_str)
        slots  = generate_slots(doctor, date)
        return JsonResponse({'slots': slots})
    except Exception as e:
        return JsonResponse({'slots': [], 'error': str(e)})


# ── Confirm Appointment ────────────────────────────────────────────────────────
@login_required
def confirm_appointment(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        date_str  = request.POST.get('date')
        time_str  = request.POST.get('time')
        symptoms  = request.POST.get('symptoms', '')
        notes     = request.POST.get('notes', '')

        doctor = get_object_or_404(DoctorProfile, id=doctor_id)

        try:
            appt_date  = datetime.date.fromisoformat(date_str)
            start_time = datetime.time.fromisoformat(time_str)
            end_time   = (
                datetime.datetime.combine(appt_date, start_time)
                + datetime.timedelta(minutes=30)
            ).time()
        except ValueError:
            messages.error(request, 'Invalid date or time.')
            return redirect('appointments:book', doctor_id=doctor_id)

        # Check slot availability
        if Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appt_date,
            start_time=start_time,
            status__in=['pending', 'confirmed']
        ).exists():
            messages.error(
                request,
                'This slot was just booked. Please choose another.'
            )
            return redirect('appointments:book', doctor_id=doctor_id)

        # Create Razorpay Order
        try:
            client = get_razorpay_client()
            amount_paise = int(float(doctor.consultation_fee) * 100)

            order = client.order.create({
                'amount':   amount_paise,
                'currency': 'INR',
                'payment_capture': 1,
                'notes': {
                    'doctor':  doctor.user.get_full_name(),
                    'patient': request.user.get_full_name(),
                    'date':    date_str,
                    'time':    time_str,
                }
            })

            razorpay_order_id = order['id']

        except Exception as e:
            print(f"Razorpay Error: {e}")
            razorpay_order_id = None

        # Save to session
        request.session['booking'] = {
            'doctor_id':        doctor.id,
            'date':             date_str,
            'time':             time_str,
            'end_time':         end_time.strftime('%H:%M'),
            'symptoms':         symptoms,
            'notes':            notes,
            'fee':              str(doctor.consultation_fee),
            'razorpay_order_id': razorpay_order_id,
        }

        context = {
            'doctor':             doctor,
            'date':               appt_date,
            'time':               start_time.strftime('%I:%M %p'),
            'symptoms':           symptoms,
            'notes':              notes,
            'razorpay_order_id':  razorpay_order_id,
            'razorpay_key_id':    settings.RAZORPAY_KEY_ID,
            'amount':             int(float(doctor.consultation_fee) * 100),
            'patient_name':       request.user.get_full_name(),
            'patient_email':      request.user.email,
            'patient_phone':      request.user.phone or '9999999999',
        }
        return render(request, 'appointments/confirm.html', context)

    return redirect('patients:find_doctors')


# ── Razorpay Payment Verification & Appointment Creation ──────────────────────
@login_required
def process_payment(request):
    if request.method != 'POST':
        return redirect('patients:find_doctors')

    booking = request.session.get('booking')
    if not booking:
        messages.error(request, 'Booking session expired. Please try again.')
        return redirect('patients:find_doctors')

    doctor     = get_object_or_404(DoctorProfile, id=booking['doctor_id'])
    appt_date  = datetime.date.fromisoformat(booking['date'])
    start_time = datetime.time.fromisoformat(booking['time'])
    end_time   = datetime.time.fromisoformat(booking['end_time'])

    # Get Razorpay payment details from POST
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id   = request.POST.get('razorpay_order_id', '')
    razorpay_signature  = request.POST.get('razorpay_signature', '')

    pay_method = 'card'  # Razorpay handles method internally

    # Verify payment signature
    payment_verified = False
    if razorpay_payment_id and razorpay_order_id and razorpay_signature:
        try:
            client = get_razorpay_client()
            client.utility.verify_payment_signature({
                'razorpay_order_id':   razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature':  razorpay_signature,
            })
            payment_verified = True
        except razorpay.errors.SignatureVerificationError:
            payment_verified = False

    # Double check slot
    if Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appt_date,
        start_time=start_time,
        status__in=['pending', 'confirmed']
    ).exists():
        messages.error(request, 'Slot no longer available.')
        del request.session['booking']
        return redirect('appointments:book', doctor_id=doctor.id)

    # Create Appointment
    appt = Appointment.objects.create(
        patient          = request.user,
        doctor           = doctor,
        appointment_date = appt_date,
        start_time       = start_time,
        end_time         = end_time,
        symptoms         = booking.get('symptoms', ''),
        notes            = booking.get('notes', ''),
        status           = 'confirmed' if payment_verified else 'pending',
    )

    # Create Payment record
    from django.utils import timezone
    payment_obj = Payment.objects.create(
        appointment         = appt,
        patient             = request.user,
        amount              = booking['fee'],
        method              = pay_method,
        status              = 'success' if payment_verified else 'pending',
        razorpay_order_id   = razorpay_order_id,
        razorpay_payment_id = razorpay_payment_id,
        paid_at             = timezone.now() if payment_verified else None,
    )

    del request.session['booking']

    # Fire notifications
    notify_appt_confirmed(appt)
    notify_doctor_new_booking(appt)

    if payment_verified:
        notify_payment_success(payment_obj)
        notify_doctor_payment_received(payment_obj)

    # Check if this is a new patient for this doctor
    from appointments.models import Appointment as Appt
    previous = Appt.objects.filter(
        doctor=doctor,
        patient=request.user
    ).exclude(id=appt.id).exists()
    if not previous:
        notify_doctor_new_patient(appt)

    messages.success(
        request,
        f'Appointment booked! ID: {appt.appointment_id}'
    )
    return redirect('appointments:success', appt_id=appt.appointment_id)


# ── Success Page ──────────────────────────────────────────────────────────────
@login_required
def appointment_success(request, appt_id):
    appt = get_object_or_404(
        Appointment,
        appointment_id=appt_id,
        patient=request.user
    )
    return render(request, 'appointments/success.html', {'appt': appt})


# ── Cancel Appointment ────────────────────────────────────────────────────────
@login_required
def cancel_appointment(request, appt_id):
    appt = get_object_or_404(
        Appointment, id=appt_id, patient=request.user
    )
    if appt.status in ['pending', 'confirmed']:
        appt.status = 'cancelled'
        appt.save()
        
        from notifications.utils import notify_doctor_appt_cancelled
        notify_doctor_appt_cancelled(appt)

        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'This appointment cannot be cancelled.')
    return redirect('patients:appointments')


@login_required
def complete_appointment(request, appt_id):
    if request.user.role != 'doctor':
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    appt = get_object_or_404(
        Appointment, id=appt_id, doctor=request.user.doctor_profile
    )
    
    if appt.status == 'confirmed':
        appt.status = 'completed'
        appt.save()
        
        from notifications.utils import notify_appt_completed
        notify_appt_completed(appt)
        
        return JsonResponse({'status': 'success', 'message': 'Appointment marked as completed'})
    
    return JsonResponse({'status': 'error', 'message': 'This appointment cannot be completed'}, status=400)