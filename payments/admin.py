from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['transaction_id', 'patient', 'amount',
                     'method', 'status', 'paid_at']
    list_filter   = ['status', 'method']
    search_fields = ['transaction_id', 'patient__first_name']