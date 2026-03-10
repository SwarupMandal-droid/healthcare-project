from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def all_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Mark all as read when page is opened
    notifications.filter(is_read=False).update(is_read=True)

    context = {'notifications': notifications}
    return render(request, 'notifications/all.html', context)


@login_required
def unread_count(request):
    count = Notification.objects.filter(
        user=request.user, is_read=False
    ).count()
    notifications = list(
        Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:8].values(
            'id', 'title', 'message',
            'category', 'is_read', 'link',
            'created_at'
        )
    )
    # Format created_at
    from django.utils.timesince import timesince
    for n in notifications:
        n['time'] = timesince(n['created_at']) + ' ago'
        n['created_at'] = str(n['created_at'])

    return JsonResponse({
        'count':         count,
        'notifications': notifications,
    })


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def mark_one_read(request, notif_id):
    notif = get_object_or_404(
        Notification, id=notif_id, user=request.user
    )
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def delete_one(request, notif_id):
    notif = get_object_or_404(
        Notification, id=notif_id, user=request.user
    )
    notif.delete()
    return JsonResponse({'status': 'deleted'})