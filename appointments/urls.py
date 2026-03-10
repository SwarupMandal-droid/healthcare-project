from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('book/<int:doctor_id>/',   views.book_appointment,   name='book'),
    path('confirm/',                views.confirm_appointment, name='confirm'),
    path('payment/',                views.process_payment,     name='payment'),
    path('success/<str:appt_id>/',  views.appointment_success, name='success'),
    path('cancel/<int:appt_id>/',   views.cancel_appointment,  name='cancel'),
    path('complete/<int:appt_id>/', views.complete_appointment, name='complete'),
    path('slots/',                  views.get_slots,            name='slots'),
]