from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('chat/',    views.chat_page,    name='chat'),
    path('message/', views.send_message, name='message'),
    path('history/', views.chat_history, name='history'),
    path('clear/',   views.clear_chat,   name='clear'),
]