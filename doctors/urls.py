from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('appointments/', views.my_appointments, name='appointments'),
    path('documents/', views.patient_documents, name='documents'),
    path('upload/', views.upload_documents, name='upload'),
    path('profile/', views.profile, name='profile'),
]