from django.shortcuts import render

def checkout(request):
    return render(request, 'payments/checkout.html')

def verify_payment(request):
    return render(request, 'payments/verify.html')

def payment_history(request):
    return render(request, 'payments/history.html')