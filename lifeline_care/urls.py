from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/',  admin.site.urls),
    path('',               include('patients.urls',     namespace='patients')),
    path('accounts/',      include('accounts.urls',     namespace='accounts')),
    path('doctors/',       include('doctors.urls',      namespace='doctors')),
    path('appointments/',  include('appointments.urls', namespace='appointments')),
    path('payments/',      include('payments.urls',     namespace='payments')),
    path('ai/',            include('ai_assistant.urls', namespace='ai_assistant')),
    path('admin-panel/',   include('admin_panel.urls',  namespace='admin_panel')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)