from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
import datetime


def admin_required(view_func):
    """Decorator: only allow admin role users."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admins only.')
            return redirect('accounts:auth')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Dashboard Overview ────────────────────────────────────────────────────────
@admin_required
def dashboard(request):
    from accounts.models import User
    from doctors.models import DoctorProfile
    from patients.models import PatientProfile
    from appointments.models import Appointment
    from payments.models import Payment

    today = datetime.date.today()
    month_start = today.replace(day=1)

    # Core stats
    total_doctors   = DoctorProfile.objects.count()
    total_patients  = PatientProfile.objects.count()
    total_appts     = Appointment.objects.count()
    total_revenue   = Payment.objects.filter(
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # This month
    month_appts   = Appointment.objects.filter(
        appointment_date__gte=month_start
    ).count()
    month_revenue = Payment.objects.filter(
        status='success',
        created_at__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Today
    today_appts = Appointment.objects.filter(
        appointment_date=today
    ).count()

    # Pending verifications
    pending_doctors = DoctorProfile.objects.filter(
        is_verified=False
    ).count()

    # Recent appointments
    recent_appts = Appointment.objects.order_by(
        '-created_at'
    ).select_related(
        'patient', 'doctor__user', 'doctor__specialization'
    )[:8]

    # Recent payments
    recent_payments = Payment.objects.order_by(
        '-created_at'
    ).select_related('patient', 'appointment__doctor__user')[:6]

    # Appointments by status
    appt_stats = {
        'confirmed': Appointment.objects.filter(status='confirmed').count(),
        'completed': Appointment.objects.filter(status='completed').count(),
        'pending':   Appointment.objects.filter(status='pending').count(),
        'cancelled': Appointment.objects.filter(status='cancelled').count(),
    }

    # Top specializations
    from doctors.models import Specialization
    top_specs = Specialization.objects.annotate(
        appt_count=Count('doctors__appointments')
    ).order_by('-appt_count')[:5]

    context = {
        'total_doctors':   total_doctors,
        'total_patients':  total_patients,
        'total_appts':     total_appts,
        'total_revenue':   total_revenue,
        'month_appts':     month_appts,
        'month_revenue':   month_revenue,
        'today_appts':     today_appts,
        'pending_doctors': pending_doctors,
        'recent_appts':    recent_appts,
        'recent_payments': recent_payments,
        'appt_stats':      appt_stats,
        'top_specs':       top_specs,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ── Manage Doctors ────────────────────────────────────────────────────────────
@admin_required
def manage_doctors(request):
    from doctors.models import DoctorProfile

    search = request.GET.get('search', '')
    filter_verified = request.GET.get('verified', '')
    filter_spec     = request.GET.get('spec', '')

    doctors = DoctorProfile.objects.select_related(
        'user', 'specialization'
    ).order_by('-user__date_joined')

    if search:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)  |
            Q(user__email__icontains=search)       |
            Q(license_number__icontains=search)
        )

    if filter_verified == 'verified':
        doctors = doctors.filter(is_verified=True)
    elif filter_verified == 'pending':
        doctors = doctors.filter(is_verified=False)

    if filter_spec:
        doctors = doctors.filter(specialization__name=filter_spec)

    from doctors.models import Specialization
    specializations = Specialization.objects.all()

    context = {
        'doctors':         doctors,
        'specializations': specializations,
        'search':          search,
        'filter_verified': filter_verified,
        'filter_spec':     filter_spec,
    }
    return render(request, 'admin_panel/doctors.html', context)


@admin_required
def verify_doctor(request, doctor_id):
    from doctors.models import DoctorProfile
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    doctor.is_verified = not doctor.is_verified
    doctor.save()
    status = 'verified' if doctor.is_verified else 'unverified'
    
    from notifications.utils import notify_doctor_profile_verified
    if doctor.is_verified:
        notify_doctor_profile_verified(doctor)

    messages.success(
        request,
        f'Dr. {doctor.user.get_full_name()} has been {status}.'
    )
    return redirect('admin_panel:doctors')


@admin_required
def toggle_doctor(request, doctor_id):
    from doctors.models import DoctorProfile
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    doctor.is_available = not doctor.is_available
    doctor.save()
    status = 'activated' if doctor.is_available else 'deactivated'
    messages.success(
        request,
        f'Dr. {doctor.user.get_full_name()} has been {status}.'
    )
    return redirect('admin_panel:doctors')


# ── Manage Patients ───────────────────────────────────────────────────────────
@admin_required
def manage_patients(request):
    from accounts.models import User

    search = request.GET.get('search', '')

    patients = User.objects.filter(
        role='patient'
    ).order_by('-date_joined')

    if search:
        patients = patients.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)
        )

    # Annotate appointment count
    from appointments.models import Appointment
    for patient in patients:
        patient.appt_count = Appointment.objects.filter(
            patient=patient
        ).count()

    context = {
        'patients': patients,
        'search':   search,
    }
    return render(request, 'admin_panel/patients.html', context)


# ── Manage Appointments ───────────────────────────────────────────────────────
@admin_required
def manage_appointments(request):
    from appointments.models import Appointment

    search      = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    filter_date   = request.GET.get('date', '')

    appointments = Appointment.objects.select_related(
        'patient', 'doctor__user', 'doctor__specialization'
    ).order_by('-appointment_date', '-start_time')

    if search:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=search)    |
            Q(patient__last_name__icontains=search)     |
            Q(doctor__user__first_name__icontains=search)|
            Q(appointment_id__icontains=search)
        )

    if filter_status:
        appointments = appointments.filter(status=filter_status)

    if filter_date:
        appointments = appointments.filter(appointment_date=filter_date)

    context = {
        'appointments':  appointments,
        'search':        search,
        'filter_status': filter_status,
        'filter_date':   filter_date,
    }
    return render(request, 'admin_panel/appointments.html', context)


# ── Manage Payments ───────────────────────────────────────────────────────────
@admin_required
def manage_payments(request):
    from payments.models import Payment

    search        = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    filter_method = request.GET.get('method', '')

    payments = Payment.objects.select_related(
        'patient', 'appointment__doctor__user'
    ).order_by('-created_at')

    if search:
        payments = payments.filter(
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search)  |
            Q(transaction_id__icontains=search)
        )

    if filter_status:
        payments = payments.filter(status=filter_status)

    if filter_method:
        payments = payments.filter(method=filter_method)

    total_revenue = payments.filter(
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'payments':      payments,
        'total_revenue': total_revenue,
        'search':        search,
        'filter_status': filter_status,
        'filter_method': filter_method,
    }
    return render(request, 'admin_panel/payments.html', context)