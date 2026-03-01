from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def dashboard(request):
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('accounts:auth')

    try:
        doctor = request.user.doctor_profile
    except Exception:
        messages.error(request, 'Doctor profile not found.')
        return redirect('accounts:auth')

    from appointments.models import Appointment
    import datetime
    today = datetime.date.today()

    today_appts = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).order_by('start_time')

    upcoming = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gt=today,
        status__in=['pending','confirmed']
    ).count()

    completed = Appointment.objects.filter(
        doctor=doctor, status='completed'
    ).count()

    recent_patients = Appointment.objects.filter(
        doctor=doctor
    ).order_by('-created_at').select_related('patient')[:4]

    context = {
        'doctor':          doctor,
        'today_appts':     today_appts,
        'upcoming':        upcoming,
        'completed':       completed,
        'recent_patients': recent_patients,
        'today':           today,
    }
    return render(request, 'doctors/dashboard.html', context)


@login_required
def my_appointments(request):
    if request.user.role != 'doctor':
        return redirect('accounts:auth')

    from appointments.models import Appointment
    import datetime
    today = datetime.date.today()

    doctor = request.user.doctor_profile

    today_appts = Appointment.objects.filter(
        doctor=doctor, appointment_date=today
    ).order_by('start_time')

    upcoming = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gt=today,
        status__in=['pending','confirmed']
    ).order_by('appointment_date','start_time')

    completed = Appointment.objects.filter(
        doctor=doctor, status='completed'
    ).order_by('-appointment_date')

    cancelled = Appointment.objects.filter(
        doctor=doctor, status='cancelled'
    ).order_by('-appointment_date')

    context = {
        'today_appts': today_appts,
        'upcoming':    upcoming,
        'completed':   completed,
        'cancelled':   cancelled,
    }
    return render(request, 'doctors/appointments.html', context)


@login_required
def patient_documents(request):
    if request.user.role != 'doctor':
        return redirect('accounts:auth')

    from doctors.models import PatientDocument
    doctor    = request.user.doctor_profile
    documents = PatientDocument.objects.filter(
        doctor=doctor
    ).select_related('patient')

    doc_type = request.GET.get('type', '')
    if doc_type:
        documents = documents.filter(doc_type=doc_type)

    context = {'documents': documents}
    return render(request, 'doctors/documents.html', context)


@login_required
def upload_documents(request):
    if request.user.role != 'doctor':
        return redirect('accounts:auth')

    from doctors.models import PatientDocument
    from accounts.models import User

    doctor = request.user.doctor_profile

    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        doc_type   = request.POST.get('doc_type', 'other')
        title      = request.POST.get('title', '')
        notes      = request.POST.get('notes', '')
        file       = request.FILES.get('file')

        if not all([patient_id, file]):
            messages.error(request, 'Patient and file are required.')
            return redirect('doctors:upload')

        try:
            patient = User.objects.get(id=patient_id, role='patient')
        except User.DoesNotExist:
            messages.error(request, 'Patient not found.')
            return redirect('doctors:upload')

        PatientDocument.objects.create(
            doctor   = doctor,
            patient  = patient,
            doc_type = doc_type,
            title    = title or f"{doc_type.title()} — {patient.get_full_name()}",
            file     = file,
            notes    = notes,
        )
        messages.success(request, 'Document uploaded successfully!')
        return redirect('doctors:upload')

    # GET — load recent uploads and patients
    recent_docs = PatientDocument.objects.filter(
        doctor=doctor
    ).order_by('-uploaded_at')[:10]

    # All patients who have appointments with this doctor
    from appointments.models import Appointment
    my_patients = User.objects.filter(
        appointments__doctor=doctor
    ).distinct()

    context = {
        'recent_docs': recent_docs,
        'my_patients': my_patients,
    }
    return render(request, 'doctors/upload.html', context)


@login_required
def profile(request):
    if request.user.role != 'doctor':
        return redirect('accounts:auth')

    doctor = request.user.doctor_profile

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name',  user.last_name)
        user.email      = request.POST.get('email',      user.email)
        user.phone      = request.POST.get('phone',      user.phone)

        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
        user.save()

        doctor.experience_years  = request.POST.get('experience_years', 0)
        doctor.consultation_fee  = request.POST.get('consultation_fee', 500)
        doctor.bio               = request.POST.get('bio', '')
        doctor.clinic_name       = request.POST.get('clinic_name', '')
        doctor.clinic_address    = request.POST.get('clinic_address', '')
        doctor.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('doctors:profile')

    from appointments.models import Review
    reviews = Review.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-created_at')[:5]

    context = {
        'doctor':  doctor,
        'reviews': reviews,
    }
    return render(request, 'doctors/profile.html', context)