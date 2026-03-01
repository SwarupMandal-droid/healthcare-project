from django.contrib import admin
from .models import Appointment, Review

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ['appointment_id', 'patient', 'doctor',
                     'appointment_date', 'start_time', 'status']
    list_filter   = ['status', 'appointment_date']
    search_fields = ['appointment_id', 'patient__first_name',
                     'doctor__user__first_name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'rating', 'created_at']
    list_filter  = ['rating']