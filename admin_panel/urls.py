from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('',              views.dashboard,        name='dashboard'),
    path('doctors/',      views.manage_doctors,   name='doctors'),
    path('doctors/<int:doctor_id>/verify/',
                          views.verify_doctor,    name='verify_doctor'),
    path('doctors/<int:doctor_id>/toggle/',
                          views.toggle_doctor,    name='toggle_doctor'),
    path('patients/',     views.manage_patients,  name='patients'),
    path('appointments/', views.manage_appointments, name='appointments'),
    path('payments/',     views.manage_payments,  name='payments'),
]