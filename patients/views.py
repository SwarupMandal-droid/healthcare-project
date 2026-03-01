from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def home(request):
    return render(request, 'patients/home.html')


@login_required
def dashboard(request):
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('accounts:auth')

    try:
        profile = request.user.patient_profile
    except Exception:
        from patients.models import PatientProfile
        profile = PatientProfile.objects.create(user=request.user)

    # Real data from DB
    from appointments.models import Appointment
    upcoming   = Appointment.objects.filter(
        patient=request.user,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'start_time')[:3]

    completed  = Appointment.objects.filter(
        patient=request.user,
        status='completed'
    ).count()

    from doctors.models import PatientDocument
    doc_count  = PatientDocument.objects.filter(
        patient=request.user
    ).count()

    from payments.models import Payment
    total_spent = sum(
        p.amount for p in Payment.objects.filter(
            patient=request.user, status='success'
        )
    )

    context = {
        'profile':     profile,
        'upcoming':    upcoming,
        'completed':   completed,
        'doc_count':   doc_count,
        'total_spent': total_spent,
    }
    return render(request, 'patients/dashboard.html', context)


@login_required
def find_doctors(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    from doctors.models import DoctorProfile, Specialization
    doctors = DoctorProfile.objects.filter(
        is_available=True
    ).select_related('user', 'specialization')

    # Filters
    spec_filter  = request.GET.get('spec', '')
    search_query = request.GET.get('search', '')

    if spec_filter:
        doctors = doctors.filter(specialization__slug=spec_filter)

    if search_query:
        doctors = doctors.filter(
            user__first_name__icontains=search_query
        ) | doctors.filter(
            user__last_name__icontains=search_query
        ) | doctors.filter(
            specialization__name__icontains=search_query
        )

    specializations = Specialization.objects.all()

    context = {
        'doctors':         doctors,
        'specializations': specializations,
        'search_query':    search_query,
        'spec_filter':     spec_filter,
    }
    return render(request, 'patients/find_doctors.html', context)


@login_required
def my_appointments(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    from appointments.models import Appointment
    upcoming  = Appointment.objects.filter(
        patient=request.user,
        status__in=['pending','confirmed']
    ).order_by('appointment_date','start_time')

    completed = Appointment.objects.filter(
        patient=request.user, status='completed'
    ).order_by('-appointment_date')

    cancelled = Appointment.objects.filter(
        patient=request.user, status='cancelled'
    ).order_by('-appointment_date')

    context = {
        'upcoming':  upcoming,
        'completed': completed,
        'cancelled': cancelled,
    }
    return render(request, 'patients/appointments.html', context)


@login_required
def my_documents(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    from doctors.models import PatientDocument
    doc_type = request.GET.get('type', '')
    documents = PatientDocument.objects.filter(patient=request.user)

    if doc_type:
        documents = documents.filter(doc_type=doc_type)

    context = {'documents': documents, 'doc_type': doc_type}
    return render(request, 'patients/documents.html', context)


@login_required
def ai_assistant(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')
    return render(request, 'patients/ai_assistant.html')


@login_required
def payment_history(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    from payments.models import Payment
    payments = Payment.objects.filter(
        patient=request.user
    ).order_by('-created_at')

    total_spent = sum(p.amount for p in payments.filter(status='success'))
    this_month  = sum(
        p.amount for p in payments.filter(
            status='success',
            created_at__month=__import__('datetime').date.today().month
        )
    )
    refunded = sum(p.amount for p in payments.filter(status='refunded'))

    context = {
        'payments':    payments,
        'total_spent': total_spent,
        'this_month':  this_month,
        'refunded':    refunded,
    }
    return render(request, 'patients/payment_history.html', context)


@login_required
def profile(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    try:
        patient_profile = request.user.patient_profile
    except Exception:
        from patients.models import PatientProfile
        patient_profile = PatientProfile.objects.create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name',  user.last_name)
        user.email      = request.POST.get('email',      user.email)
        user.phone      = request.POST.get('phone',      user.phone)

        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
        user.save()

        patient_profile.blood_group        = request.POST.get('blood_group', '')
        patient_profile.gender             = request.POST.get('gender', '')
        patient_profile.address            = request.POST.get('address', '')
        patient_profile.allergies          = request.POST.get('allergies', '')
        patient_profile.chronic_conditions = request.POST.get('chronic_conditions', '')
        patient_profile.current_medications= request.POST.get('current_medications', '')
        patient_profile.emergency_name     = request.POST.get('emergency_name', '')
        patient_profile.emergency_phone    = request.POST.get('emergency_phone', '')
        patient_profile.emergency_relationship = request.POST.get(
            'emergency_relationship', '')

        dob = request.POST.get('date_of_birth', '')
        if dob:
            patient_profile.date_of_birth = dob

        patient_profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('patients:profile')

    context = {'patient_profile': patient_profile}
    return render(request, 'patients/profile.html', context)