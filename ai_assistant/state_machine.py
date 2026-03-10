from .intent  import detect_intent, extract_specialization, extract_date_hint
from .actions import (
    get_doctors_by_specialization,
    get_all_specializations,
    get_available_slots,
    get_next_available_dates,
    get_patient_appointments,
    create_appointment,
    cancel_appointment,
    reschedule_appointment,
    get_patient_documents,
    get_payment_status,
    recommend_specialization,
)


class BotResponse:
    """Structured response from the bot."""

    def __init__(self, message: str,
                 buttons: list = None,
                 quick_replies: list = None,
                 card_list: list = None,
                 end_flow: bool = False):
        self.message      = message
        self.buttons      = buttons      or []
        self.quick_replies= quick_replies or []
        self.card_list    = card_list    or []
        self.end_flow     = end_flow

    def to_dict(self) -> dict:
        return {
            'message':       self.message,
            'buttons':       self.buttons,
            'quick_replies': self.quick_replies,
            'card_list':     self.card_list,
            'end_flow':      self.end_flow,
        }


class ChatStateMachine:
    """
    Core state machine for chatbot conversation flow.
    Each state has a handler method named handle_{state}.
    """

    def __init__(self, session, patient):
        self.session = session
        self.patient = patient

    def process(self, user_message: str) -> BotResponse:
        """Main entry — route to correct handler."""
        intent = detect_intent(user_message)

        # ── Global override intents (work in any state) ──
        if intent == 'goodbye':
            self.session.clear_context()
            return BotResponse(
                f"Goodbye, {self.patient.first_name}! "
                f"Take care and stay healthy. 😊",
                end_flow=True
            )

        if intent == 'help':
            self.session.clear_context()
            return self._help_menu()

        # ── Route based on current state ──
        state = self.session.state

        if state == 'idle':
            return self._handle_idle(user_message, intent)

        elif state == 'booking_select_spec':
            return self._handle_booking_spec(user_message)

        elif state == 'booking_select_doctor':
            return self._handle_booking_doctor(user_message)

        elif state == 'booking_select_date':
            return self._handle_booking_date(user_message)

        elif state == 'booking_select_slot':
            return self._handle_booking_slot(user_message)

        elif state == 'booking_confirm':
            return self._handle_booking_confirm(user_message, intent)

        elif state == 'reschedule_select_appt':
            return self._handle_reschedule_select(user_message)

        elif state == 'reschedule_select_date':
            return self._handle_reschedule_date(user_message)

        elif state == 'reschedule_select_slot':
            return self._handle_reschedule_slot(user_message)

        elif state == 'cancel_select_appt':
            return self._handle_cancel_select(user_message)

        elif state == 'cancel_confirm':
            return self._handle_cancel_confirm(user_message, intent)

        elif state == 'symptom_check':
            return self._handle_symptom_check(user_message)

        else:
            self.session.clear_context()
            return self._handle_idle(user_message, intent)

    # ── IDLE ──────────────────────────────────────────────────────────────────
    def _handle_idle(self, message: str, intent: str) -> BotResponse:

        if intent == 'greeting':
            return BotResponse(
                f"Hello {self.patient.first_name}! 👋 "
                f"I'm LifelineAI, your health assistant. "
                f"How can I help you today?",
                quick_replies=[
                    '📅 Book Appointment',
                    '🔄 Reschedule',
                    '❌ Cancel Appointment',
                    '🤒 Check Symptoms',
                    '📋 My Appointments',
                    '📁 My Documents',
                ]
            )

        elif intent == 'book_appointment':
            return self._start_booking(message)

        elif intent == 'reschedule_appointment':
            return self._start_reschedule()

        elif intent == 'cancel_appointment':
            return self._start_cancel()

        elif intent == 'symptom_check':
            return self._start_symptom_check(message)

        elif intent == 'view_appointments':
            return self._show_appointments()

        elif intent == 'view_records':
            return self._show_documents()

        elif intent == 'doctor_info':
            return self._show_doctors(message)

        elif intent == 'payment':
            return self._show_payments()

        elif intent == 'clinic_info':
            return self._show_clinic_info()

        elif intent == 'registration':
            return BotResponse(
                "You can register by going to our signup page. "
                "Click the button below!",
                buttons=[
                    {'label': '📝 Register Now',
                     'url':   '/accounts/auth/'}
                ]
            )

        else:
            # Unknown — use Claude AI for general questions
            return self._ask_claude(message)

    # ── BOOKING FLOW ──────────────────────────────────────────────────────────

    def _start_booking(self, message: str) -> BotResponse:
        """Start booking — check if specialization mentioned."""
        spec = extract_specialization(message)

        if spec:
            return self._show_doctors_for_booking(spec)

        specs = get_all_specializations()
        if not specs:
            return BotResponse(
                "Sorry, no doctors are available right now. "
                "Please try again later."
            )

        self.session.set_state('booking_select_spec')
        return BotResponse(
            "Sure! Let's book you an appointment. 📅\n\n"
            "Which specialization do you need?",
            quick_replies=specs
        )

    def _handle_booking_spec(self, message: str) -> BotResponse:
        spec = extract_specialization(message) or message.strip()
        return self._show_doctors_for_booking(spec)

    def _show_doctors_for_booking(self, spec: str) -> BotResponse:
        doctors = get_doctors_by_specialization(spec)

        if not doctors:
            return BotResponse(
                f"Sorry, no {spec} doctors are available right now. "
                f"Would you like to try a different specialization?",
                quick_replies=get_all_specializations()
            )

        self.session.set_state(
            'booking_select_doctor',
            {'spec': spec, 'doctors': doctors}
        )

        doctor_list = '\n'.join([
            f"**{i+1}. {d['name']}** — "
            f"{d['experience']} yrs exp | "
            f"⭐ {d['rating']} | "
            f"₹{d['fee']}"
            for i, d in enumerate(doctors)
        ])

        return BotResponse(
            f"Here are available **{spec}** doctors:\n\n"
            f"{doctor_list}\n\n"
            f"Reply with the number or doctor's name to select.",
            quick_replies=[
                f"{i+1}. {d['name']}"
                for i, d in enumerate(doctors)
            ]
        )

    def _handle_booking_doctor(self, message: str) -> BotResponse:
        doctors = self.session.context.get('doctors', [])
        selected = None

        # Try number selection
        msg = message.strip()
        if msg.isdigit():
            idx = int(msg) - 1
            if 0 <= idx < len(doctors):
                selected = doctors[idx]

        # Try name match
        if not selected:
            msg_lower = msg.lower()
            for d in doctors:
                if d['name'].lower() in msg_lower or \
                   msg_lower in d['name'].lower():
                    selected = d
                    break

        if not selected:
            return BotResponse(
                "I didn't catch that. Please reply with the "
                "number (1, 2, 3...) or the doctor's name.",
                quick_replies=[
                    f"{i+1}. {d['name']}"
                    for i, d in enumerate(doctors)
                ]
            )

        # Get available dates
        dates = get_next_available_dates(selected['id'])

        if not dates:
            return BotResponse(
                f"{selected['name']} has no available dates "
                f"in the next 2 weeks. "
                f"Would you like to choose a different doctor?",
                quick_replies=['Choose Different Doctor', 'Back to Menu']
            )

        self.session.set_state(
            'booking_select_date',
            {
                'selected_doctor_id':   selected['id'],
                'selected_doctor_name': selected['name'],
                'selected_doctor_fee':  selected['fee'],
                'available_dates':      dates,
            }
        )

        return BotResponse(
            f"Great choice! **{selected['name']}** is available on:\n\n" +
            '\n'.join([
                f"• {d['label']}" for d in dates
            ]) +
            "\n\nWhich date works for you?",
            quick_replies=[d['label'] for d in dates]
        )

    def _handle_booking_date(self, message: str) -> BotResponse:
        dates  = self.session.context.get('available_dates', [])
        doc_id = self.session.context.get('selected_doctor_id')

        # Try to match date from message
        selected_date = None
        msg_lower     = message.lower().strip()

        for d in dates:
            if (d['label'].lower() in msg_lower or
                    msg_lower in d['label'].lower() or
                    d['value'] in msg_lower):
                selected_date = d
                break

        # Try natural date extraction
        if not selected_date:
            date_hint = extract_date_hint(message)
            if date_hint:
                for d in dates:
                    if d['value'] == date_hint:
                        selected_date = d
                        break
                if not selected_date:
                    # Use the hint directly
                    import datetime
                    try:
                        dt = datetime.date.fromisoformat(date_hint)
                        selected_date = {
                            'value': date_hint,
                            'label': dt.strftime('%A, %d %B')
                        }
                    except ValueError:
                        pass

        if not selected_date:
            return BotResponse(
                "Please select one of the available dates:",
                quick_replies=[d['label'] for d in dates]
            )

        slots = get_available_slots(doc_id, selected_date['value'])

        if not slots:
            return BotResponse(
                f"No slots available on **{selected_date['label']}**. "
                f"Please choose another date:",
                quick_replies=[d['label'] for d in dates]
            )

        self.session.set_state(
            'booking_select_slot',
            {
                'selected_date':       selected_date['value'],
                'selected_date_label': selected_date['label'],
                'available_slots':     slots,
            }
        )

        return BotResponse(
            f"Available slots on **{selected_date['label']}**:\n\n" +
            ' · '.join(slots) +
            "\n\nWhich time works for you?",
            quick_replies=slots
        )

    def _handle_booking_slot(self, message: str) -> BotResponse:
        slots = self.session.context.get('available_slots', [])
        msg   = message.strip()

        selected_slot = None
        for slot in slots:
            if slot.lower() in msg.lower() or msg.lower() in slot.lower():
                selected_slot = slot
                break

        if not selected_slot:
            return BotResponse(
                "Please select one of the available time slots:",
                quick_replies=slots
            )

        ctx  = self.session.context
        self.session.set_state(
            'booking_confirm',
            {'selected_slot': selected_slot}
        )

        return BotResponse(
            f"Please confirm your appointment:\n\n"
            f"👨‍⚕️ **Doctor:** {ctx['selected_doctor_name']}\n"
            f"📅 **Date:** {ctx['selected_date_label']}\n"
            f"🕐 **Time:** {selected_slot}\n"
            f"💳 **Fee:** ₹{ctx['selected_doctor_fee']}\n\n"
            f"Shall I confirm this booking?",
            quick_replies=['✅ Yes, Confirm', '❌ Cancel']
        )

    def _handle_booking_confirm(self,
                                 message: str,
                                 intent: str) -> BotResponse:
        if intent == 'yes' or 'confirm' in message.lower():
            ctx    = self.session.context
            result = create_appointment(
                patient   = self.patient,
                doctor_id = ctx['selected_doctor_id'],
                date_str  = ctx['selected_date'],
                time_str  = ctx['selected_slot'],
            )

            self.session.clear_context()

            if result['success']:
                # Fire notifications
                try:
                    from appointments.models import Appointment
                    from notifications.utils import (
                        notify_appt_confirmed,
                        notify_doctor_new_booking,
                    )
                    appt = Appointment.objects.get(
                        appointment_id=result['appt_id']
                    )
                    notify_appt_confirmed(appt)
                    notify_doctor_new_booking(appt)
                except Exception:
                    pass

                return BotResponse(
                    f"🎉 Appointment confirmed!\n\n"
                    f"**Appointment ID:** {result['appt_id']}\n"
                    f"👨‍⚕️ {result['doctor']}\n"
                    f"📅 {result['date']} at {result['time']}\n"
                    f"💳 Fee: ₹{result['fee']}\n\n"
                    f"You can view it in My Appointments. "
                    f"Is there anything else I can help with?",
                    buttons=[{
                        'label': '📋 View My Appointments',
                        'url':   '/patients/appointments/'
                    }],
                    quick_replies=[
                        '🏠 Back to Menu',
                        '📅 Book Another',
                    ]
                )
            else:
                return BotResponse(
                    f"Sorry, {result['error']} "
                    f"Would you like to choose another slot?",
                    quick_replies=['Yes, Choose Again', 'Back to Menu']
                )

        else:
            self.session.clear_context()
            return BotResponse(
                "Booking cancelled. No worries! "
                "How else can I help you?",
                quick_replies=[
                    '📅 Book Appointment',
                    '🏠 Back to Menu'
                ]
            )

    # ── RESCHEDULE FLOW ───────────────────────────────────────────────────────

    def _start_reschedule(self) -> BotResponse:
        appts = get_patient_appointments(self.patient)

        if not appts:
            return BotResponse(
                "You have no upcoming appointments to reschedule. "
                "Would you like to book a new one?",
                quick_replies=['📅 Book Appointment', '🏠 Menu']
            )

        self.session.set_state(
            'reschedule_select_appt',
            {'appts': appts}
        )

        appt_list = '\n'.join([
            f"{i+1}. **{a['doctor']}** — "
            f"{a['date']} at {a['time']}"
            for i, a in enumerate(appts)
        ])

        return BotResponse(
            f"Which appointment would you like to reschedule?\n\n"
            f"{appt_list}",
            quick_replies=[
                f"{i+1}. {a['doctor']} — {a['date']}"
                for i, a in enumerate(appts)
            ]
        )

    def _handle_reschedule_select(self, message: str) -> BotResponse:
        appts = self.session.context.get('appts', [])
        msg   = message.strip()

        selected = None
        if msg.isdigit():
            idx = int(msg) - 1
            if 0 <= idx < len(appts):
                selected = appts[idx]

        if not selected:
            for a in appts:
                if a['doctor'].lower() in msg.lower():
                    selected = a
                    break

        if not selected:
            return BotResponse(
                "Please select the appointment number:",
                quick_replies=[
                    f"{i+1}. {a['doctor']}"
                    for i, a in enumerate(appts)
                ]
            )

        # Get doctor's available dates
        from appointments.models import Appointment
        try:
            appt_obj = Appointment.objects.get(id=selected['id'])
            dates    = get_next_available_dates(
                appt_obj.doctor.id
            )
        except Exception:
            dates = []

        if not dates:
            return BotResponse(
                "No new dates available for this doctor. "
                "Would you like to cancel instead?",
                quick_replies=['Cancel Instead', 'Back to Menu']
            )

        self.session.set_state(
            'reschedule_select_date',
            {
                'reschedule_appt_id': selected['id'],
                'reschedule_dates':   dates,
            }
        )

        return BotResponse(
            f"Select a new date for your appointment "
            f"with **{selected['doctor']}**:",
            quick_replies=[d['label'] for d in dates]
        )

    def _handle_reschedule_date(self, message: str) -> BotResponse:
        dates  = self.session.context.get('reschedule_dates', [])
        appt_id = self.session.context.get('reschedule_appt_id')

        selected_date = None
        msg_lower     = message.lower()

        for d in dates:
            if d['label'].lower() in msg_lower:
                selected_date = d
                break

        if not selected_date:
            date_hint = extract_date_hint(message)
            if date_hint:
                import datetime
                try:
                    dt = datetime.date.fromisoformat(date_hint)
                    selected_date = {
                        'value': date_hint,
                        'label': dt.strftime('%A, %d %B')
                    }
                except ValueError:
                    pass

        if not selected_date:
            return BotResponse(
                "Please pick one of these dates:",
                quick_replies=[d['label'] for d in dates]
            )

        from appointments.models import Appointment
        try:
            appt = Appointment.objects.get(id=appt_id)
            slots = get_available_slots(
                appt.doctor.id, selected_date['value']
            )
        except Exception:
            slots = []

        if not slots:
            return BotResponse(
                f"No slots on {selected_date['label']}. "
                f"Pick another date:",
                quick_replies=[d['label'] for d in dates]
            )

        self.session.set_state(
            'reschedule_select_slot',
            {
                'reschedule_date':       selected_date['value'],
                'reschedule_date_label': selected_date['label'],
                'reschedule_slots':      slots,
            }
        )

        return BotResponse(
            f"Available slots on **{selected_date['label']}**:\n\n"
            + ' · '.join(slots)
            + "\n\nWhich time?",
            quick_replies=slots
        )

    def _handle_reschedule_slot(self, message: str) -> BotResponse:
        slots   = self.session.context.get('reschedule_slots', [])
        appt_id = self.session.context.get('reschedule_appt_id')
        msg     = message.strip()

        selected_slot = None
        for slot in slots:
            if slot.lower() in msg.lower():
                selected_slot = slot
                break

        if not selected_slot:
            return BotResponse(
                "Please pick one of these slots:",
                quick_replies=slots
            )

        result = reschedule_appointment(
            patient        = self.patient,
            appointment_id = appt_id,
            new_date_str   = self.session.context['reschedule_date'],
            new_time_str   = selected_slot,
        )

        self.session.clear_context()

        if result['success']:
            return BotResponse(
                f"✅ Appointment rescheduled!\n\n"
                f"👨‍⚕️ {result['doctor']}\n"
                f"📅 {result['date']} at {result['time']}\n\n"
                f"Anything else I can help with?",
                quick_replies=['📋 My Appointments', '🏠 Menu']
            )
        else:
            return BotResponse(
                f"Sorry, {result['error']}",
                quick_replies=['Try Again', '🏠 Menu']
            )

    # ── CANCEL FLOW ───────────────────────────────────────────────────────────

    def _start_cancel(self) -> BotResponse:
        appts = get_patient_appointments(self.patient)

        if not appts:
            return BotResponse(
                "You have no upcoming appointments to cancel.",
                quick_replies=['📅 Book Appointment', '🏠 Menu']
            )

        self.session.set_state(
            'cancel_select_appt',
            {'appts': appts}
        )

        appt_list = '\n'.join([
            f"{i+1}. **{a['doctor']}** — "
            f"{a['date']} at {a['time']}"
            for i, a in enumerate(appts)
        ])

        return BotResponse(
            f"Which appointment would you like to cancel?\n\n"
            f"{appt_list}",
            quick_replies=[
                f"{i+1}. {a['doctor']}"
                for i, a in enumerate(appts)
            ]
        )

    def _handle_cancel_select(self, message: str) -> BotResponse:
        appts = self.session.context.get('appts', [])
        msg   = message.strip()

        selected = None
        if msg.isdigit():
            idx = int(msg) - 1
            if 0 <= idx < len(appts):
                selected = appts[idx]

        if not selected:
            for a in appts:
                if a['doctor'].lower() in msg.lower():
                    selected = a
                    break

        if not selected:
            return BotResponse(
                "Please select the appointment number:",
                quick_replies=[
                    f"{i+1}. {a['doctor']}"
                    for i, a in enumerate(appts)
                ]
            )

        self.session.set_state(
            'cancel_confirm',
            {'cancel_appt_id': selected['id']}
        )

        return BotResponse(
            f"Are you sure you want to cancel your appointment?\n\n"
            f"👨‍⚕️ **{selected['doctor']}**\n"
            f"📅 {selected['date']} at {selected['time']}",
            quick_replies=['✅ Yes, Cancel It', '❌ No, Keep It']
        )

    def _handle_cancel_confirm(self,
                                message: str,
                                intent: str) -> BotResponse:
        if intent == 'yes' or 'cancel' in message.lower():
            appt_id = self.session.context.get('cancel_appt_id')
            result  = cancel_appointment(self.patient, appt_id)
            self.session.clear_context()

            if result['success']:
                return BotResponse(
                    f"✅ Appointment cancelled.\n\n"
                    f"👨‍⚕️ {result['doctor']}\n"
                    f"📅 {result['date']} at {result['time']}\n\n"
                    f"Would you like to book a new appointment?",
                    quick_replies=['📅 Book New', '🏠 Menu']
                )
            else:
                return BotResponse(
                    f"Sorry, {result['error']}",
                    quick_replies=['🏠 Menu']
                )
        else:
            self.session.clear_context()
            return BotResponse(
                "No problem! Your appointment is kept. "
                "Anything else I can help with?",
                quick_replies=['📋 My Appointments', '🏠 Menu']
            )

    # ── SYMPTOM CHECK ─────────────────────────────────────────────────────────

    def _start_symptom_check(self, message: str) -> BotResponse:
        spec = recommend_specialization(message)

        if spec:
            doctors = get_doctors_by_specialization(spec)
            self.session.clear_context()

            response = (
                f"Based on your symptoms, I recommend consulting "
                f"a **{spec}** specialist.\n\n"
            )

            if doctors:
                response += "Here are our top doctors:\n\n"
                response += '\n'.join([
                    f"• **{d['name']}** — "
                    f"⭐ {d['rating']} | ₹{d['fee']}"
                    for d in doctors[:3]
                ])
                response += "\n\nWould you like to book an appointment?"

                return BotResponse(
                    response,
                    quick_replies=[
                        f"Book with {doctors[0]['name']}",
                        '📅 See More Doctors',
                        '🏠 Menu',
                    ]
                )
            else:
                return BotResponse(
                    response +
                    "Unfortunately no doctors are available right now.",
                    quick_replies=['🏠 Menu']
                )

        # No spec detected — ask more questions
        self.session.set_state('symptom_check')

        return BotResponse(
            "I'll help identify the right specialist for you. "
            "Please describe your symptoms in more detail.\n\n"
            "For example: *headache, fever, chest pain, skin rash...*",
            quick_replies=[
                'Headache & Dizziness',
                'Chest Pain',
                'Skin Problem',
                'Fever & Cold',
                'Back / Joint Pain',
                'Mental Health',
            ]
        )

    def _handle_symptom_check(self, message: str) -> BotResponse:
        self.session.state = 'idle'
        self.session.save()
        return self._start_symptom_check(message)

    # ── INFO HANDLERS ─────────────────────────────────────────────────────────

    def _show_appointments(self) -> BotResponse:
        appts = get_patient_appointments(self.patient)

        if not appts:
            return BotResponse(
                "You have no upcoming appointments.",
                quick_replies=['📅 Book Appointment', '🏠 Menu'],
                buttons=[{
                    'label': '📅 Book Now',
                    'url':   '/patients/find-doctors/'
                }]
            )

        appt_text = '\n'.join([
            f"**{i+1}. {a['doctor']}**\n"
            f"   📅 {a['date']} at {a['time']}\n"
            f"   Status: {a['status']}"
            for i, a in enumerate(appts)
        ])

        return BotResponse(
            f"Your upcoming appointments:\n\n{appt_text}",
            buttons=[{
                'label': '📋 View All Appointments',
                'url':   '/patients/appointments/'
            }],
            quick_replies=['🔄 Reschedule', '❌ Cancel', '🏠 Menu']
        )

    def _show_documents(self) -> BotResponse:
        docs = get_patient_documents(self.patient)

        if not docs:
            return BotResponse(
                "You have no medical documents yet. "
                "Your doctor will upload them after your consultation.",
                quick_replies=['📅 Book Appointment', '🏠 Menu']
            )

        doc_text = '\n'.join([
            f"• **{d['title']}** ({d['type']})\n"
            f"  By {d['doctor']} on {d['date']}"
            for d in docs
        ])

        return BotResponse(
            f"Your recent documents:\n\n{doc_text}",
            buttons=[{
                'label': '📁 View All Documents',
                'url':   '/patients/documents/'
            }]
        )

    def _show_doctors(self, message: str) -> BotResponse:
        spec = extract_specialization(message)

        if spec:
            doctors = get_doctors_by_specialization(spec)
            if doctors:
                doc_text = '\n'.join([
                    f"• **{d['name']}** — "
                    f"{d['experience']} yrs | "
                    f"⭐ {d['rating']} | ₹{d['fee']}"
                    for d in doctors
                ])
                return BotResponse(
                    f"**{spec}** doctors available:\n\n{doc_text}",
                    quick_replies=[
                        f"Book with {doctors[0]['name']}",
                        '🏠 Menu'
                    ]
                )

        return BotResponse(
            "Which specialization are you looking for?",
            quick_replies=get_all_specializations()
        )

    def _show_payments(self) -> BotResponse:
        payments = get_payment_status(self.patient)

        if not payments:
            return BotResponse(
                "You have no payment records yet.",
                quick_replies=['📅 Book Appointment', '🏠 Menu']
            )

        pay_text = '\n'.join([
            f"• ₹{p['amount']} — {p['doctor']}\n"
            f"  {p['date']} | {p['method']} | **{p['status']}**"
            for p in payments
        ])

        return BotResponse(
            f"Your recent payments:\n\n{pay_text}",
            buttons=[{
                'label': '💳 Payment History',
                'url':   '/patients/payment-history/'
            }]
        )

    def _show_clinic_info(self) -> BotResponse:
        return BotResponse(
            "**Lifeline Care Clinic Info** 🏥\n\n"
            "🕐 **Hours:** Mon–Sat, 9:00 AM – 8:00 PM\n"
            "📍 **Location:** Available online & in-person\n"
            "💳 **Fees:** ₹200 – ₹1500 (varies by specialist)\n"
            "📞 **Support:** Available 24/7 via chat\n\n"
            "**Services:**\n"
            "• Cardiology • Neurology • Dermatology\n"
            "• Orthopedics • Pediatrics • Psychiatry\n"
            "• Gynecology • General Medicine & more",
            quick_replies=[
                '📅 Book Appointment',
                '👨‍⚕️ Find Doctors',
                '🏠 Menu'
            ]
        )

    def _help_menu(self) -> BotResponse:
        return BotResponse(
            f"Hi {self.patient.first_name}! Here's what I can do:\n\n"
            "📅 **Book** an appointment\n"
            "🔄 **Reschedule** an appointment\n"
            "❌ **Cancel** an appointment\n"
            "🤒 **Check symptoms** & get specialist advice\n"
            "📋 **View** your appointments\n"
            "📁 **Access** your medical documents\n"
            "💳 **Check** payment history\n"
            "🏥 **Clinic** information\n\n"
            "What would you like to do?",
            quick_replies=[
                '📅 Book Appointment',
                '🔄 Reschedule',
                '❌ Cancel',
                '🤒 Symptoms',
                '📋 Appointments',
                '📁 Documents',
            ]
        )

    def _ask_claude(self, message: str) -> BotResponse:
        """Fall back to Claude AI for general health questions."""
        try:
            import anthropic
            import os

            client   = anthropic.Anthropic(
                api_key=os.environ.get('ANTHROPIC_API_KEY')
            )
            response = client.messages.create(
                model      = 'claude-haiku-4-5-20251001',
                max_tokens = 512,
                system     = (
                    "You are LifelineAI, a helpful healthcare assistant "
                    "for Lifeline Care platform in India. "
                    "Answer health questions briefly and clearly. "
                    "Always recommend consulting a real doctor for diagnosis. "
                    "Keep responses under 150 words. Use simple language."
                ),
                messages   = [{'role': 'user', 'content': message}],
            )
            reply = response.content[0].text

        except Exception:
            reply = (
                "I'm not sure about that. I can help you book "
                "appointments, check symptoms, or view your records. "
                "What would you like to do?"
            )

        return BotResponse(
            reply,
            quick_replies=[
                '📅 Book Appointment',
                '🤒 Check Symptoms',
                '🏠 Menu'
            ]
        )