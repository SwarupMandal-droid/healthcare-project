from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('message/', views.send_message, name='message'),   # AJAX endpoint
]