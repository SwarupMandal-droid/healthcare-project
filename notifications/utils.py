from notifications.models import Notification


# ── Patient Notifications ─────────────────────────────────────────────────────

def notify_appt_confirmed(appointment):
    """Patient: Appointment booking confirmed."""
    Notification.objects.create(
        user     = appointment.patient,
        type     = 'appt_confirmed',
        category = 'appointment',
        title    = 'Appointment Confirmed ✅',
        message  = (
            f"Your appointment with Dr. "
            f"{appointment.doctor.user.get_full_name()} is confirmed for "
            f"{appointment.appointment_date.strftime('%d %B')} at "
            f"{appointment.start_time.strftime('%I:%M %p')}."
        ),
        link     = '/patients/appointments/',
    )


def notify_appt_completed(appointment):
    """Patient: Appointment completed."""
    Notification.objects.create(
        user     = appointment.patient,
        type     = 'appt_completed',
        category = 'appointment',
        title    = 'Consultation Completed',
        message  = (
            f"Your consultation with Dr. "
            f"{appointment.doctor.user.get_full_name()} is completed. "
            f"Please leave a review!"
        ),
        link     = '/patients/appointments/',
    )


def notify_appt_cancelled_by_doctor(appointment):
    """Patient: Doctor cancelled appointment."""
    Notification.objects.create(
        user     = appointment.patient,
        type     = 'appt_cancelled_doc',
        category = 'appointment',
        title    = 'Appointment Cancelled',
        message  = (
            f"Your appointment with Dr. "
            f"{appointment.doctor.user.get_full_name()} has been cancelled. "
            f"Please rebook at your convenience."
        ),
        link     = '/patients/find-doctors/',
    )


def notify_payment_success(payment):
    """Patient: Payment successful."""
    Notification.objects.create(
        user     = payment.patient,
        type     = 'payment_success',
        category = 'payment',
        title    = 'Payment Successful 💳',
        message  = (
            f"Your payment of ₹{payment.amount} for the appointment with "
            f"Dr. {payment.appointment.doctor.user.get_full_name()} "
            f"is successful."
        ),
        link     = '/patients/payment-history/',
    )


def notify_payment_failed(patient, amount):
    """Patient: Payment failed."""
    Notification.objects.create(
        user     = patient,
        type     = 'payment_failed',
        category = 'payment',
        title    = 'Payment Failed ❌',
        message  = (
            f"Your payment of ₹{amount} failed. "
            f"Please try again to confirm your appointment."
        ),
        link     = '/patients/find-doctors/',
    )


def notify_refund_processed(payment):
    """Patient: Refund processed."""
    Notification.objects.create(
        user     = payment.patient,
        type     = 'payment_refund',
        category = 'payment',
        title    = 'Refund Processed 💰',
        message  = (
            f"Your refund of ₹{payment.amount} for the cancelled "
            f"appointment has been processed."
        ),
        link     = '/patients/payment-history/',
    )


def notify_prescription_uploaded(document):
    """Patient: Doctor uploaded a prescription."""
    Notification.objects.create(
        user     = document.patient,
        type     = 'prescription_uploaded',
        category = 'health',
        title    = 'Prescription Uploaded 📋',
        message  = (
            f"Dr. {document.doctor.user.get_full_name()} has uploaded "
            f"a {document.get_doc_type_display().lower()} for you."
        ),
        link     = '/patients/documents/',
    )


def notify_profile_reminder(patient):
    """Patient: Reminder to update medical history."""
    Notification.objects.create(
        user     = patient,
        type     = 'profile_reminder',
        category = 'system',
        title    = 'Complete Your Profile 📝',
        message  = (
            "Please update your medical history, allergies, and "
            "emergency contact for better care."
        ),
        link     = '/patients/profile/',
    )


def notify_appt_reminder(appointment):
    """Patient: Appointment reminder (e.g. 24h before)."""
    Notification.objects.create(
        user     = appointment.patient,
        type     = 'appt_reminder',
        category = 'appointment',
        title    = 'Upcoming Appointment ⏰',
        message  = (
            f"Reminder: You have an appointment with Dr. "
            f"{appointment.doctor.user.get_full_name()} "
            f"on {appointment.appointment_date.strftime('%d %B')} "
            f"at {appointment.start_time.strftime('%I:%M %p')}."
        ),
        link     = '/patients/appointments/',
    )


# ── Doctor Notifications ──────────────────────────────────────────────────────

def notify_doctor_new_booking(appointment):
    """Doctor: New appointment booked."""
    Notification.objects.create(
        user     = appointment.doctor.user,
        type     = 'new_booking',
        category = 'appointment',
        title    = 'New Appointment Booked 📅',
        message  = (
            f"New appointment booked by "
            f"{appointment.patient.get_full_name()} on "
            f"{appointment.appointment_date.strftime('%d %B')} "
            f"at {appointment.start_time.strftime('%I:%M %p')}."
        ),
        link     = '/doctors/appointments/',
    )


def notify_doctor_appt_cancelled(appointment):
    """Doctor: Patient cancelled appointment."""
    Notification.objects.create(
        user     = appointment.doctor.user,
        type     = 'appt_cancelled_pat',
        category = 'appointment',
        title    = 'Appointment Cancelled',
        message  = (
            f"Patient {appointment.patient.get_full_name()} has cancelled "
            f"their appointment scheduled for "
            f"{appointment.appointment_date.strftime('%d %B')} at "
            f"{appointment.start_time.strftime('%I:%M %p')}."
        ),
        link     = '/doctors/appointments/',
    )


def notify_doctor_payment_received(payment):
    """Doctor: Payment received for consultation."""
    Notification.objects.create(
        user     = payment.appointment.doctor.user,
        type     = 'payment_received',
        category = 'payment',
        title    = 'Payment Received 💰',
        message  = (
            f"You received ₹{payment.amount} for your consultation "
            f"with {payment.patient.get_full_name()}."
        ),
        link     = '/doctors/dashboard/',
    )


def notify_doctor_review_received(review):
    """Doctor: New patient review."""
    stars = '⭐' * review.rating
    Notification.objects.create(
        user     = review.doctor.user,
        type     = 'review_received',
        category = 'system',
        title    = f'New Review Received {stars}',
        message  = (
            f"{review.patient.get_full_name()} left you a "
            f"{review.rating}-star review."
            + (f' "{review.comment[:60]}..."'
               if review.comment else '')
        ),
        link     = '/doctors/profile/',
    )


def notify_doctor_profile_verified(doctor):
    """Doctor: Profile verified by admin."""
    Notification.objects.create(
        user     = doctor.user,
        type     = 'profile_verified',
        category = 'system',
        title    = 'Profile Verified ✅',
        message  = (
            "Congratulations! Your medical license has been verified. "
            "Patients can now book appointments with you."
        ),
        link     = '/doctors/profile/',
    )


def notify_doctor_new_patient(appointment):
    """Doctor: New patient registered and booked."""
    Notification.objects.create(
        user     = appointment.doctor.user,
        type     = 'new_patient',
        category = 'system',
        title    = 'New Patient 👤',
        message  = (
            f"New patient {appointment.patient.get_full_name()} "
            f"has registered and booked an appointment with you."
        ),
        link     = '/doctors/appointments/',
    )


# ── Admin Notifications ───────────────────────────────────────────────────────

def notify_admin_new_doctor(doctor):
    """Admin: New doctor registered."""
    from accounts.models import User
    admins = User.objects.filter(role='admin')
    for admin in admins:
        Notification.objects.create(
            user     = admin,
            type     = 'new_doctor_reg',
            category = 'system',
            title    = 'New Doctor Registration 🩺',
            message  = (
                f"Dr. {doctor.user.get_full_name()} has registered as a "
                f"{doctor.specialization.name} and is pending verification."
            ),
            link     = '/admin-panel/doctors/',
        )


def notify_admin_payment_issue(payment):
    """Admin: Payment failed alert."""
    from accounts.models import User
    admins = User.objects.filter(role='admin')
    for admin in admins:
        Notification.objects.create(
            user     = admin,
            type     = 'payment_issue',
            category = 'payment',
            title    = 'Payment Issue ⚠️',
            message  = (
                f"Payment of ₹{payment.amount} by "
                f"{payment.patient.get_full_name()} failed."
            ),
            link     = '/admin-panel/payments/',
        )