from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',            views.all_notifications, name='all'),
    path('unread/',     views.unread_count,       name='unread_count'),
    path('mark-read/',  views.mark_all_read,      name='mark_all_read'),
    path('mark/<int:notif_id>/', views.mark_one_read, name='mark_one'),
    path('delete/<int:notif_id>/', views.delete_one, name='delete'),
]