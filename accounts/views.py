from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from patients.models import PatientProfile
from doctors.models import DoctorProfile, Specialization


# ─── Auth Page (Role Selection) ───────────────────────────────────────────────
def auth_page(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    # Capture 'next' from query string for login/signup forms
    next_url = request.GET.get('next', '')
    return render(request, 'accounts/auth.html', {'next': next_url})


# ─── Login ────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.method != 'POST':
        return redirect('accounts:auth')

    email    = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    role     = request.POST.get('role', '')
    next_url = request.POST.get('next', '').strip()

    # Find user by email
    try:
        user_obj = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'No account found with this email address.')
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    # Check role matches
    if user_obj.role != role:
        messages.error(
            request,
            f'This account is registered as a {user_obj.role}, not a {role}.'
        )
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    # Authenticate
    user = authenticate(request, username=user_obj.username, password=password)
    if user is None:
        messages.error(request, 'Incorrect password. Please try again.')
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    if not user.is_active:
        messages.error(request, 'Your account has been deactivated.')
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    login(request, user)
    messages.success(request, f'Welcome back, {user.first_name}!')
    return redirect_by_role(user, fallback_url=next_url)


# ─── Signup ───────────────────────────────────────────────────────────────────
def signup_view(request):
    if request.method != 'POST':
        return redirect('accounts:auth')

    # Common fields
    role     = request.POST.get('role', '')
    name     = request.POST.get('name', '').strip()
    email    = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    confirm  = request.POST.get('confirm_password', '')
    next_url = request.POST.get('next', '').strip()

    # ── Validations ──
    if not all([role, name, email, password]):
        messages.error(request, 'All fields are required.')
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    if password != confirm:
        messages.error(request, 'Passwords do not match.')
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    if len(password) < 8:
        messages.error(request, 'Password must be at least 8 characters.')
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    if User.objects.filter(email=email).exists():
        messages.error(request, 'An account with this email already exists.')
        return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

    # ── Split name ──
    parts      = name.split(' ', 1)
    first_name = parts[0]
    last_name  = parts[1] if len(parts) > 1 else ''

    # ── Create username from email ──
    base_username = email.split('@')[0]
    username      = base_username
    counter       = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    # ── Create User ──
    user = User.objects.create_user(
        username   = username,
        email      = email,
        password   = password,
        first_name = first_name,
        last_name  = last_name,
        role       = role,
        phone      = request.POST.get('phone', ''),
    )

    # ── Create Role Profile ──
    if role == 'patient':
        PatientProfile.objects.create(
            user        = user,
            blood_group = request.POST.get('blood_group', ''),
        )

    elif role == 'doctor':
        specialization_name = request.POST.get('specialization', '')
        license_number      = request.POST.get('license', '')

        if not license_number:
            user.delete()
            messages.error(request, 'License number is required for doctors.')
            return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

        if DoctorProfile.objects.filter(license_number=license_number).exists():
            user.delete()
            messages.error(request, 'A doctor with this license number already exists.')
            return redirect(f"{reverse('accounts:auth')}?next={next_url}" if next_url else 'accounts:auth')

        spec, _ = Specialization.objects.get_or_create(
            name = specialization_name,
            defaults = {
                'slug': specialization_name.lower().replace(' ', '-'),
            }
        )

        DoctorProfile.objects.create(
            user           = user,
            specialization = spec,
            license_number = license_number,
        )

    # ── Log in immediately ──
    login(request, user)
    messages.success(
        request,
        f'Welcome to Lifeline Care, {first_name}! Your account has been created.'
    )
    return redirect_by_role(user, fallback_url=next_url)


# ─── Logout ───────────────────────────────────────────────────────────────────
def logout_view(request):
    """Accepts GET (sidebar anchor link) or POST. Clears session and redirects."""
    if request.user.is_authenticated:
        name = request.user.first_name
        logout(request)
        messages.success(request, f'Goodbye, {name}! You have been logged out.')
    return redirect('accounts:auth')


# ─── Helper: Redirect by role ─────────────────────────────────────────────────
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

def redirect_by_role(user, fallback_url=None):
    # If a safe next_url is provided, use it
    if fallback_url and url_has_allowed_host_and_scheme(fallback_url, allowed_hosts={None}):
        return redirect(fallback_url)

    if user.role == 'patient':
        return redirect('patients:dashboard')
    elif user.role == 'doctor':
        return redirect('doctors:dashboard')
    elif user.role == 'admin':
        return redirect('admin:index')
    return redirect('patients:home')
