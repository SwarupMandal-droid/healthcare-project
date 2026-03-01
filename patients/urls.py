from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.home, name='home'),
    path('patients/dashboard/', views.dashboard, name='dashboard'),
    path('patients/find-doctors/', views.find_doctors, name='find_doctors'),
    path('patients/appointments/', views.my_appointments, name='appointments'),
    path('patients/documents/', views.my_documents, name='documents'),
    path('patients/ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('patients/payment-history/', views.payment_history, name='payment_history'),
    path('patients/profile/', views.profile, name='profile'),
]