from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('patients.urls')),              # Home page lives here
    path('accounts/', include('accounts.urls')),     # Login, Signup, Auth
    # path('patients/', include('patients.urls')),     # Patient dashboard
    path('doctors/', include('doctors.urls')),       # Doctor dashboard
    path('appointments/', include('appointments.urls')),  # Booking
    path('payments/', include('payments.urls')),     # Payments
    path('ai/', include('ai_assistant.urls')),       # AI Assistant
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)