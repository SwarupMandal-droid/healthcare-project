def appointment_badge(request):
    """
    Injects `upcoming_count` into every template context so that
    the sidebar appointment badge is accurate on all patient pages.
    """
    count = 0
    if request.user.is_authenticated and hasattr(request.user, 'role') \
            and request.user.role == 'patient':
        try:
            from appointments.models import Appointment
            count = Appointment.objects.filter(
                patient=request.user,
                status__in=['pending', 'confirmed']
            ).count()
        except Exception:
            count = 0
    return {'upcoming_count': count}
