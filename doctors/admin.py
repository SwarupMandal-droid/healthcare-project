from django.contrib import admin
from .models import (DoctorProfile, Specialization,
                     DoctorAvailability, TimeSlot, PatientDocument)

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'specialization', 'experience_years',
                     'consultation_fee', 'is_verified', 'is_available']
    list_filter   = ['specialization', 'is_verified', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day', 'start_time', 'end_time', 'is_active']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'is_booked']
    list_filter  = ['is_booked', 'date']

@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display  = ['title', 'doctor', 'patient', 'doc_type', 'uploaded_at']
    list_filter   = ['doc_type']
    search_fields = ['title', 'patient__first_name']