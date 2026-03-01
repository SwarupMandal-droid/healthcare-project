from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('verify/', views.verify_payment, name='verify'),
    path('history/', views.payment_history, name='history'),
]