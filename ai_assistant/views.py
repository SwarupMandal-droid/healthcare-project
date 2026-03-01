from django.shortcuts import render
from django.http import JsonResponse

def chat(request):
    return render(request, 'ai_assistant/chat.html')

def send_message(request):
    return JsonResponse({'message': 'AI coming soon'})