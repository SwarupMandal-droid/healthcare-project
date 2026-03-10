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
    from django.db.models import Q
    from django.utils import timezone
    import datetime

    doctor    = request.user.doctor_profile
    documents = PatientDocument.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-uploaded_at')

    doc_type = request.GET.get('type', '')
    if doc_type:
        documents = documents.filter(doc_type=doc_type)
        
    search = request.GET.get('search', '').strip()
    if search:
        documents = documents.filter(
            Q(patient__first_name__icontains=search) | 
            Q(patient__last_name__icontains=search) | 
            Q(title__icontains=search)
        )

    date_range = request.GET.get('date_range', '')
    if date_range == 'today':
        documents = documents.filter(uploaded_at__date=timezone.now().date())
    elif date_range == 'this_week':
        start_week = timezone.now().date() - datetime.timedelta(days=timezone.now().weekday())
        documents = documents.filter(uploaded_at__date__gte=start_week)
    elif date_range == 'this_month':
        documents = documents.filter(
            uploaded_at__year=timezone.now().year, 
            uploaded_at__month=timezone.now().month
        )

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
        title      = request.POST.get('title', '').strip()
        notes      = request.POST.get('notes', '').strip()
        file       = request.FILES.get('file')

        if not patient_id or not file:
            messages.error(request, 'Patient and file are required.')
            return redirect('doctors:upload')

        try:
            patient = User.objects.get(id=patient_id, role='patient')
        except User.DoesNotExist:
            messages.error(request, 'Patient not found.')
            return redirect('doctors:upload')

        doc = PatientDocument.objects.create(
            doctor   = doctor,
            patient  = patient,
            doc_type = doc_type,
            title    = title or f"{doc_type.replace('_',' ').title()} — {patient.get_full_name()}",
            file     = file,
            notes    = notes,
        )

        from notifications.utils import notify_prescription_uploaded
        notify_prescription_uploaded(doc)

        messages.success(request, 'Document uploaded successfully!')
        return redirect('doctors:upload')

    # GET
    recent_docs = PatientDocument.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-uploaded_at')[:10]

    from appointments.models import Appointment
    my_patients = User.objects.filter(
        appointments__doctor=doctor
    ).distinct()

    # Pre-selected patient from query param
    preselected_patient_id = request.GET.get('patient')
    preselected_patient    = None
    if preselected_patient_id:
        try:
            preselected_patient = User.objects.get(
                id=preselected_patient_id, role='patient'
            )
        except User.DoesNotExist:
            pass

    context = {
        'recent_docs':          recent_docs,
        'my_patients':          my_patients,
        'preselected_patient':  preselected_patient,
    }
    return render(request, 'doctors/upload.html', context)


@login_required
def profile(request):
    if request.user.role != 'doctor':
        return redirect('accounts:auth')

    try:
        doctor = request.user.doctor_profile
    except Exception:
        messages.error(request, 'Doctor profile not found.')
        return redirect('accounts:auth')

    if request.method == 'POST':
        user = request.user

        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name  = request.POST.get('last_name',  user.last_name).strip()
        user.email      = request.POST.get('email',      user.email).strip()
        user.phone      = request.POST.get('phone',      user.phone).strip()

        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
        user.save()

        # Update doctor fields
        try:
            doctor.experience_years = int(request.POST.get('experience_years', 0))
        except ValueError:
            doctor.experience_years = 0

        try:
            doctor.consultation_fee = float(request.POST.get('consultation_fee', 500))
        except ValueError:
            doctor.consultation_fee = 500

        doctor.bio           = request.POST.get('bio', '').strip()
        doctor.clinic_name   = request.POST.get('clinic_name', '').strip()
        doctor.clinic_address= request.POST.get('clinic_address', '').strip()

        # Update specialization
        from doctors.models import Specialization
        spec_name = request.POST.get('specialization', '').strip()
        if spec_name:
            spec, _ = Specialization.objects.get_or_create(
                name=spec_name,
                defaults={'slug': spec_name.lower().replace(' ', '-')}
            )
            doctor.specialization = spec

        doctor.save()

        # Update availability
        from doctors.models import DoctorAvailability
        days = ['Monday','Tuesday','Wednesday',
                'Thursday','Friday','Saturday','Sunday']

        for i, day_name in enumerate(days):
            is_active  = request.POST.get(f'day_{i}') == 'on'
            start_time = request.POST.get(f'start_{i}', '09:00')
            end_time   = request.POST.get(f'end_{i}',   '18:00')

            if is_active and start_time and end_time:
                DoctorAvailability.objects.update_or_create(
                    doctor = doctor,
                    day    = i,
                    defaults = {
                        'start_time': start_time,
                        'end_time':   end_time,
                        'is_active':  True,
                    }
                )
            else:
                DoctorAvailability.objects.filter(
                    doctor=doctor, day=i
                ).update(is_active=False)

        messages.success(request, 'Profile updated successfully!')
        return redirect('doctors:profile')

    # GET — load reviews and availability
    from appointments.models import Review
    from doctors.models import DoctorAvailability

    reviews = Review.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-created_at')[:5]

    # Load existing availability for all 7 days
    availability = {}
    for i in range(7):
        try:
            avail = DoctorAvailability.objects.get(doctor=doctor, day=i)
            availability[i] = avail
        except DoctorAvailability.DoesNotExist:
            availability[i] = None

    from doctors.models import Specialization
    specializations = Specialization.objects.all()

    context = {
        'doctor':          doctor,
        'reviews':         reviews,
        'availability':    availability,
        'specializations': specializations,
        'days':            ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
    }
    return render(request, 'doctors/profile.html', context)