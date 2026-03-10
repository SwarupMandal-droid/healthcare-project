import re


# ── Intent Definitions ────────────────────────────────────────────────────────
INTENTS = {

    'greeting': [
        r'\b(hi|hello|hey|good morning|good evening|good afternoon|namaste)\b',
    ],

    'book_appointment': [
        r'\b(book|schedule|make|set up|fix|arrange)\b.{0,20}\b(appointment|consultation|visit|meeting)\b',
        r'\b(i want|i need|i would like).{0,20}\b(doctor|consult|appointment)\b',
        r'\b(see a doctor|visit doctor|meet doctor)\b',
        r'\bbook\b',
    ],

    'reschedule_appointment': [
        r'\b(reschedule|change|move|shift|update).{0,20}\b(appointment|slot|time)\b',
        r'\b(different time|another time|change time)\b',
    ],

    'cancel_appointment': [
        r'\b(cancel|cancellation|remove|delete).{0,20}\b(appointment|booking|slot)\b',
        r'\b(don\'t want|do not want).{0,20}\b(appointment)\b',
    ],

    'check_availability': [
        r'\b(available|availability|free|open).{0,30}\b(doctor|dr\.?|slot|time)\b',
        r'\bwhen.{0,20}\b(doctor|dr\.?|available)\b',
        r'\bis dr\.?.{0,30}available\b',
    ],

    'symptom_check': [
        r'\b(symptom|feeling|suffering|pain|fever|cough|headache|vomit|nausea|dizzy|breathless|chest pain|back pain|stomach)\b',
        r'\b(i have|i am having|i feel|i am feeling).{0,30}\b(pain|ache|fever|cough|cold|weakness)\b',
        r'\b(what doctor|which doctor|which specialist).{0,20}\b(should i|for)\b',
    ],

    'view_appointments': [
        r'\b(my appointment|upcoming appointment|scheduled|booking history)\b',
        r'\b(show|view|list|see).{0,20}\b(appointment|booking|schedule)\b',
        r'\bwhat.{0,20}appointment\b',
    ],

    'view_records': [
        r'\b(prescription|lab report|medical record|report|document|diet chart)\b',
        r'\b(show|view|get|access).{0,20}\b(record|report|prescription|document)\b',
    ],

    'doctor_info': [
        r'\b(doctor|specialist|physician).{0,20}\b(available|list|show|find|search)\b',
        r'\b(find|search|show|list).{0,20}\b(doctor|specialist)\b',
        r'\bwho is.{0,20}\b(doctor|dr\.?)\b',
        r'\bdr\.?\s+\w+\b',
    ],

    'payment': [
        r'\b(pay|payment|fee|charge|cost|price|bill|invoice|receipt)\b',
        r'\b(how much|what is the fee|consultation charge)\b',
        r'\b(payment status|payment link|pay now)\b',
    ],

    'clinic_info': [
        r'\b(clinic|hospital|centre|center).{0,20}\b(timing|time|hour|address|location|fee)\b',
        r'\b(where|address|location|directions)\b',
        r'\b(timing|hours|open|close|working hours)\b',
        r'\b(service|services offered|what do you treat)\b',
    ],

    'registration': [
        r'\b(register|signup|sign up|create account|new account|new patient)\b',
        r'\b(join|enroll)\b',
    ],

    'goodbye': [
        r'\b(bye|goodbye|see you|thank you|thanks|that\'s all|no more|done|exit|quit)\b',
    ],

    'help': [
        r'\b(help|assist|support|what can you do|options|menu)\b',
    ],

    'yes': [
        r'^(yes|yeah|yep|yup|sure|ok|okay|correct|right|confirm|go ahead|proceed)\.?$',
    ],

    'no': [
        r'^(no|nope|nah|cancel|stop|don\'t|do not|negative)\.?$',
    ],
}


def detect_intent(text: str) -> str:
    """
    Detect intent from user message.
    Returns intent string or 'unknown'.
    """
    text_lower = text.lower().strip()

    for intent, patterns in INTENTS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent

    return 'unknown'


def extract_specialization(text: str) -> str | None:
    """Extract specialization name from text."""
    from doctors.models import Specialization

    text_lower = text.lower()
    specs = Specialization.objects.all()

    for spec in specs:
        if spec.name.lower() in text_lower:
            return spec.name

    # Common symptom-to-specialization keywords
    keyword_map = {
        'heart':       'Cardiology',
        'cardiac':     'Cardiology',
        'chest':       'Cardiology',
        'neuro':       'Neurology',
        'brain':       'Neurology',
        'headache':    'Neurology',
        'migraine':    'Neurology',
        'skin':        'Dermatology',
        'acne':        'Dermatology',
        'rash':        'Dermatology',
        'bone':        'Orthopedics',
        'joint':       'Orthopedics',
        'fracture':    'Orthopedics',
        'child':       'Pediatrics',
        'baby':        'Pediatrics',
        'kid':         'Pediatrics',
        'eye':         'Ophthalmology',
        'vision':      'Ophthalmology',
        'tooth':       'Dentistry',
        'dental':      'Dentistry',
        'lung':        'Pulmonology',
        'breathing':   'Pulmonology',
        'kidney':      'Nephrology',
        'mental':      'Psychiatry',
        'anxiety':     'Psychiatry',
        'depression':  'Psychiatry',
        'gynec':       'Gynecology',
        'women':       'Gynecology',
    }

    for keyword, spec_name in keyword_map.items():
        if keyword in text_lower:
            return spec_name

    return None


def extract_doctor_name(text: str) -> str | None:
    """Try to extract a doctor name from text."""
    patterns = [
        r'\bdr\.?\s+([a-zA-Z\s]+)',
        r'\bdoctor\s+([a-zA-Z\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_date_hint(text: str) -> str | None:
    """Extract date hints like today, tomorrow, day after."""
    import datetime
    text_lower = text.lower()
    today = datetime.date.today()

    if 'today'         in text_lower:
        return today.isoformat()
    if 'tomorrow'      in text_lower:
        return (today + datetime.timedelta(days=1)).isoformat()
    if 'day after'     in text_lower:
        return (today + datetime.timedelta(days=2)).isoformat()

    # Try to match DD Month or Month DD
    months = {
        'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
        'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12
    }
    for month_str, month_num in months.items():
        pattern = rf'(\d{{1,2}})\s*{month_str}'
        match   = re.search(pattern, text_lower)
        if match:
            day  = int(match.group(1))
            year = today.year
            try:
                d = datetime.date(year, month_num, day)
                if d < today:
                    d = datetime.date(year + 1, month_num, day)
                return d.isoformat()
            except ValueError:
                pass

    return None