from django.shortcuts import render

def book_appointment(request, doctor_id):
    return render(request, 'appointments/book.html')

def confirm_appointment(request):
    return render(request, 'appointments/confirm.html')

def appointment_success(request):
    return render(request, 'appointments/success.html')