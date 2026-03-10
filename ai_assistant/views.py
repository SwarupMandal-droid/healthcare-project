from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ai_assistant.models import ChatSession, ChatMessage
from ai_assistant.intent import detect_intent
from ai_assistant.state_machine import ChatStateMachine
import json
import os


# ── Chat Page ─────────────────────────────────────────────────────────────────
@login_required
def chat_page(request):
    if request.user.role != 'patient':
        return redirect('accounts:auth')

    session, _ = ChatSession.objects.get_or_create(
        patient   = request.user,
        is_active = True,
        defaults  = {}
    )

    messages = session.messages.order_by('created_at')

    context = {
        'session':  session,
        'messages': messages,
    }
    return render(request, 'patients/ai_assistant.html', context)


# ── Send Message (AJAX) ───────────────────────────────────────────────────────
@login_required
@require_POST
def send_message(request):
    try:
        data       = json.loads(request.body)
        user_input = data.get('message', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not user_input:
        return JsonResponse({'error': 'Empty message'}, status=400)

    if len(user_input) > 2000:
        return JsonResponse({'error': 'Message too long'}, status=400)

    # Get or create active session
    session, _ = ChatSession.objects.get_or_create(
        patient   = request.user,
        is_active = True,
        defaults  = {}
    )

    # Detect intent and save user message
    intent = detect_intent(user_input)

    ChatMessage.objects.create(
        session = session,
        sender  = 'user',
        message = user_input,
        intent  = intent,
    )

    # Process through state machine
    bot      = ChatStateMachine(session, request.user)
    response = bot.process(user_input)

    # Save bot response
    ChatMessage.objects.create(
        session = session,
        sender  = 'ai',
        message = response.message,
    )

    # If flow ended — close session
    if response.end_flow:
        session.is_active = False
        session.save()

    return JsonResponse(response.to_dict())


# ── Chat History (AJAX) ───────────────────────────────────────────────────────
@login_required
def chat_history(request):
    session, _ = ChatSession.objects.get_or_create(
        patient   = request.user,
        is_active = True,
        defaults  = {}
    )

    messages = [
        {
            'sender':  m.sender,
            'message': m.message,
            'time':    m.created_at.strftime('%I:%M %p'),
        }
        for m in session.messages.order_by('created_at')
    ]
    return JsonResponse({'messages': messages})


# ── Clear Chat ────────────────────────────────────────────────────────────────
@login_required
@require_POST
def clear_chat(request):
    ChatSession.objects.filter(
        patient   = request.user,
        is_active = True
    ).update(is_active=False)

    return JsonResponse({'status': 'cleared'})