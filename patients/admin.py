from django.contrib import admin
from .models import PatientProfile

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'gender', 'blood_group', 'age']
    search_fields = ['user__first_name', 'user__last_name']
    list_filter   = ['gender', 'blood_group']