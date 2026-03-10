import datetime
from doctors.models import DoctorProfile, Specialization, DoctorAvailability
from appointments.models import Appointment
from doctors.models import PatientDocument
from payments.models import Payment


# ── Doctor Queries ────────────────────────────────────────────────────────────

def get_doctors_by_specialization(spec_name: str) -> list:
    """Get available doctors for a specialization."""
    doctors = DoctorProfile.objects.filter(
        specialization__name__icontains=spec_name,
        is_available=True,
        is_verified=True,
    ).select_related('user', 'specialization').order_by('-rating')[:6]

    return [
        {
            'id':          d.id,
            'name':        f"Dr. {d.user.get_full_name()}",
            'spec':        d.specialization.name,
            'experience':  d.experience_years,
            'fee':         str(d.consultation_fee),
            'rating':      str(d.rating),
        }
        for d in doctors
    ]


def get_all_specializations() -> list:
    """Get all specializations that have available doctors."""
    specs = Specialization.objects.filter(
        doctors__is_available=True
    ).distinct().order_by('name')
    return [s.name for s in specs]


def get_available_slots(doctor_id: int, date_str: str) -> list:
    """Get available time slots for a doctor on a date."""
    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
        date   = datetime.date.fromisoformat(date_str)
    except (DoctorProfile.DoesNotExist, ValueError):
        return []

    day_of_week = date.weekday()

    try:
        avail = DoctorAvailability.objects.get(
            doctor=doctor, day=day_of_week, is_active=True
        )
    except DoctorAvailability.DoesNotExist:
        return []

    # Generate 30-min slots
    slots      = []
    start      = datetime.datetime.combine(date, avail.start_time)
    end        = datetime.datetime.combine(date, avail.end_time)
    slot_delta = datetime.timedelta(minutes=30)

    booked = set(
        Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status__in=['pending', 'confirmed']
        ).values_list('start_time', flat=True)
    )

    now = datetime.datetime.now()

    while start + slot_delta <= end:
        slot_time = start.time()
        is_past   = (date == datetime.date.today() and start <= now)
        if slot_time not in booked and not is_past:
            slots.append(slot_time.strftime('%I:%M %p'))
        start += slot_delta

    return slots


def get_next_available_dates(doctor_id: int, days_ahead: int = 7) -> list:
    """Get next N days that doctor is available."""
    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
    except DoctorProfile.DoesNotExist:
        return []

    today       = datetime.date.today()
    avail_days  = set(
        DoctorAvailability.objects.filter(
            doctor=doctor, is_active=True
        ).values_list('day', flat=True)
    )

    dates = []
    for i in range(1, 15):
        d = today + datetime.timedelta(days=i)
        if d.weekday() in avail_days:
            dates.append({
                'value': d.isoformat(),
                'label': d.strftime('%A, %d %B'),
            })
        if len(dates) >= days_ahead:
            break

    return dates


# ── Appointment Actions ───────────────────────────────────────────────────────

def get_patient_appointments(patient, status_filter=None) -> list:
    """Get patient's appointments."""
    appts = Appointment.objects.filter(
        patient=patient
    ).select_related(
        'doctor__user', 'doctor__specialization'
    ).order_by('-appointment_date', '-start_time')

    if status_filter:
        appts = appts.filter(status=status_filter)
    else:
        appts = appts.filter(
            status__in=['pending', 'confirmed']
        )

    return [
        {
            'id':     a.id,
            'appt_id': a.appointment_id,
            'doctor': f"Dr. {a.doctor.user.get_full_name()}",
            'spec':   a.doctor.specialization.name,
            'date':   a.appointment_date.strftime('%d %B %Y'),
            'time':   a.start_time.strftime('%I:%M %p'),
            'status': a.get_status_display(),
        }
        for a in appts[:5]
    ]


def create_appointment(patient, doctor_id: int,
                        date_str: str, time_str: str,
                        symptoms: str = '') -> dict:
    """Create a new appointment."""
    try:
        doctor     = DoctorProfile.objects.get(id=doctor_id)
        appt_date  = datetime.date.fromisoformat(date_str)
        start_time = datetime.datetime.strptime(
            time_str, '%I:%M %p'
        ).time()
        end_time   = (
            datetime.datetime.combine(appt_date, start_time)
            + datetime.timedelta(minutes=30)
        ).time()
    except Exception as e:
        return {'success': False, 'error': str(e)}

    # Check slot not taken
    if Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appt_date,
        start_time=start_time,
        status__in=['pending', 'confirmed']
    ).exists():
        return {
            'success': False,
            'error':   'This slot is no longer available.'
        }

    appt = Appointment.objects.create(
        patient          = patient,
        doctor           = doctor,
        appointment_date = appt_date,
        start_time       = start_time,
        end_time         = end_time,
        symptoms         = symptoms,
        status           = 'confirmed',
    )

    return {
        'success':  True,
        'appt_id':  appt.appointment_id,
        'doctor':   f"Dr. {doctor.user.get_full_name()}",
        'date':     appt_date.strftime('%d %B %Y'),
        'time':     start_time.strftime('%I:%M %p'),
        'fee':      str(doctor.consultation_fee),
    }


def cancel_appointment(patient, appointment_id: int) -> dict:
    """Cancel an appointment."""
    try:
        appt = Appointment.objects.get(
            id=appointment_id,
            patient=patient,
            status__in=['pending', 'confirmed']
        )
    except Appointment.DoesNotExist:
        return {
            'success': False,
            'error':   'Appointment not found or already cancelled.'
        }

    appt.status = 'cancelled'
    appt.save()

    # Fire notification
    try:
        from notifications.utils import notify_doctor_appt_cancelled
        notify_doctor_appt_cancelled(appt)
    except Exception:
        pass

    return {
        'success': True,
        'doctor':  f"Dr. {appt.doctor.user.get_full_name()}",
        'date':    appt.appointment_date.strftime('%d %B %Y'),
        'time':    appt.start_time.strftime('%I:%M %p'),
    }


def reschedule_appointment(patient, appointment_id: int,
                             new_date_str: str,
                             new_time_str: str) -> dict:
    """Reschedule an existing appointment."""
    try:
        appt       = Appointment.objects.get(
            id=appointment_id,
            patient=patient,
            status__in=['pending', 'confirmed']
        )
        new_date   = datetime.date.fromisoformat(new_date_str)
        new_time   = datetime.datetime.strptime(
            new_time_str, '%I:%M %p'
        ).time()
        new_end    = (
            datetime.datetime.combine(new_date, new_time)
            + datetime.timedelta(minutes=30)
        ).time()
    except Exception as e:
        return {'success': False, 'error': str(e)}

    # Check new slot availability
    if Appointment.objects.filter(
        doctor=appt.doctor,
        appointment_date=new_date,
        start_time=new_time,
        status__in=['pending', 'confirmed']
    ).exclude(id=appt.id).exists():
        return {
            'success': False,
            'error':   'That slot is already taken. Please choose another.'
        }

    appt.appointment_date = new_date
    appt.start_time       = new_time
    appt.end_time         = new_end
    appt.save()

    return {
        'success': True,
        'doctor':  f"Dr. {appt.doctor.user.get_full_name()}",
        'date':    new_date.strftime('%d %B %Y'),
        'time':    new_time.strftime('%I:%M %p'),
    }


# ── Records ───────────────────────────────────────────────────────────────────

def get_patient_documents(patient) -> list:
    """Get patient's medical documents."""
    docs = PatientDocument.objects.filter(
        patient=patient
    ).order_by('-uploaded_at')[:5]

    return [
        {
            'title':    d.title,
            'type':     d.get_doc_type_display(),
            'doctor':   f"Dr. {d.doctor.user.get_full_name()}",
            'date':     d.uploaded_at.strftime('%d %B %Y'),
        }
        for d in docs
    ]


def get_payment_status(patient) -> list:
    """Get patient's recent payments."""
    payments = Payment.objects.filter(
        patient=patient
    ).order_by('-created_at')[:5]

    return [
        {
            'amount': str(p.amount),
            'status': p.get_status_display(),
            'method': p.get_method_display(),
            'date':   p.created_at.strftime('%d %B %Y'),
            'doctor': f"Dr. {p.appointment.doctor.user.get_full_name()}",
        }
        for p in payments
    ]


# ── Symptom → Specialization ──────────────────────────────────────────────────

SYMPTOM_SPEC_MAP = {
    'Neurology':    ['headache', 'migraine', 'seizure', 'memory',
                     'numbness', 'dizziness', 'brain', 'nerve',
                     'stroke', 'paralysis', 'unconscious'],
    'Cardiology':   ['chest pain', 'heart', 'palpitation', 'breathless',
                     'shortness of breath', 'cardiac', 'blood pressure',
                     'hypertension', 'irregular heartbeat'],
    'Dermatology':  ['skin', 'rash', 'acne', 'eczema', 'psoriasis',
                     'itching', 'allergy', 'hives', 'hair loss',
                     'nail', 'fungal'],
    'Orthopedics':  ['bone', 'joint', 'fracture', 'back pain',
                     'knee', 'shoulder', 'spine', 'arthritis',
                     'muscle pain', 'sports injury'],
    'Pediatrics':   ['child', 'baby', 'infant', 'kid', 'toddler',
                     'vaccination', 'growth', 'fever child'],
    'Ophthalmology':['eye', 'vision', 'blurry', 'glasses',
                     'cataract', 'glaucoma', 'eye pain', 'redness eye'],
    'Dentistry':    ['tooth', 'teeth', 'dental', 'gum', 'cavity',
                     'toothache', 'braces', 'root canal'],
    'Pulmonology':  ['cough', 'lung', 'breathing', 'asthma',
                     'bronchitis', 'pneumonia', 'tb', 'tuberculosis',
                     'wheezing', 'chest tightness'],
    'Psychiatry':   ['anxiety', 'depression', 'stress', 'mental',
                     'sleep', 'insomnia', 'mood', 'panic', 'phobia',
                     'ocd', 'bipolar'],
    'Gynecology':   ['period', 'menstrual', 'pregnancy', 'women',
                     'ovary', 'uterus', 'gynec', 'pcos', 'fertility'],
    'General Medicine': ['fever', 'cold', 'flu', 'weakness', 'fatigue',
                         'weight loss', 'diabetes', 'thyroid', 'infection'],
}


def recommend_specialization(symptoms_text: str) -> str | None:
    """Recommend specialization based on symptom text."""
    text_lower = symptoms_text.lower()
    scores     = {}

    for spec, keywords in SYMPTOM_SPEC_MAP.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[spec] = score

    if not scores:
        return None

    return max(scores, key=scores.get)