from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    Notice, NoticeCategory, NoticeAcknowledgement, NoticeView,
    Circular, Event, Notification, SMSLog, EmailLog
)
from .forms import (
    NoticeForm, NoticeCategoryForm, CircularForm, EventForm,
    NoticeSearchForm, BulkNotificationForm
)
from students.models import Student
from teachers.models import Teacher
from classes.models import Class

# ========== Notice Board Dashboard ==========
@login_required
def notice_dashboard(request):
    """Notice board dashboard"""
    today = timezone.now().date()
    
    # Statistics
    total_notices = Notice.objects.filter(status='published').count()
    pinned_notices = Notice.objects.filter(is_pinned=True, status='published').count()
    expired_notices = Notice.objects.filter(expiry_date__lt=today, status='published').count()
    upcoming_events = Event.objects.filter(start_date__gte=today, is_active=True).count()
    
    # Recent notices
    recent_notices = Notice.objects.filter(
        status='published'
    ).select_related('category', 'author').order_by('-publish_date')[:5]
    
    # Upcoming events
    events = Event.objects.filter(
        start_date__gte=today,
        is_active=True
    ).order_by('start_date')[:5]
    
    # Unread notifications for user
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    context = {
        'total_notices': total_notices,
        'pinned_notices': pinned_notices,
        'expired_notices': expired_notices,
        'upcoming_events': upcoming_events,
        'recent_notices': recent_notices,
        'events': events,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'notices/dashboard.html', context)


# ========== Notice Views ==========
@login_required
def notice_list(request):
    """List all notices"""
    notices = Notice.objects.filter(status='published').select_related('category', 'author')
    
    # Filter based on user role
    if request.user.role not in ['super_admin', 'admin']:
        filtered_notices = []
        for notice in notices:
            if notice.can_view(request.user):
                filtered_notices.append(notice.id)
        notices = notices.filter(id__in=filtered_notices)
    
    # Search form
    form = NoticeSearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        priority = form.cleaned_data.get('priority')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if query:
            notices = notices.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )
        
        if category:
            notices = notices.filter(category=category)
        
        if priority:
            notices = notices.filter(priority=priority)
        
        if date_from:
            notices = notices.filter(publish_date__gte=date_from)
        
        if date_to:
            notices = notices.filter(publish_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(notices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Record view for each notice
    for notice in page_obj:
        NoticeView.objects.get_or_create(
            notice=notice,
            user=request.user,
            defaults={'ip_address': request.META.get('REMOTE_ADDR')}
        )
        # Increment view count
        notice.view_count += 1
        notice.save(update_fields=['view_count'])
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    return render(request, 'notices/notice_list.html', context)


@login_required
def notice_detail(request, pk):
    """View notice details"""
    notice = get_object_or_404(Notice, pk=pk, status='published')
    
    # Check if user can view
    if not notice.can_view(request.user) and request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to view this notice.")
        return redirect('notice_list')
    
    # Record view
    NoticeView.objects.get_or_create(
        notice=notice,
        user=request.user,
        defaults={'ip_address': request.META.get('REMOTE_ADDR')}
    )
    
    # Handle acknowledgment
    if request.method == 'POST' and notice.requires_acknowledgment:
        ack, created = NoticeAcknowledgement.objects.get_or_create(
            notice=notice,
            user=request.user
        )
        if created:
            messages.success(request, "Thank you for acknowledging this notice.")
        return redirect('notice_detail', pk=notice.pk)
    
    # Check if user has acknowledged
    has_acknowledged = NoticeAcknowledgement.objects.filter(
        notice=notice,
        user=request.user
    ).exists()
    
    context = {
        'notice': notice,
        'has_acknowledged': has_acknowledged,
    }
    return render(request, 'notices/notice_detail.html', context)


@login_required
def notice_create(request):
    """Create new notice"""
    if request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to create notices.")
        return redirect('notice_list')
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.author = request.user
            notice.save()
            form.save_m2m()
            
            # Send notifications if enabled
            if notice.send_email or notice.send_sms or notice.send_push:
                # This would trigger background tasks
                messages.info(request, "Notifications will be sent to target audience.")
            
            messages.success(request, "Notice created successfully!")
            return redirect('notice_detail', pk=notice.pk)
    else:
        form = NoticeForm()
    
    context = {
        'form': form,
        'title': 'Create Notice',
    }
    return render(request, 'notices/notice_form.html', context)


@login_required
def notice_edit(request, pk):
    """Edit notice"""
    if request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to edit notices.")
        return redirect('notice_list')
    
    notice = get_object_or_404(Notice, pk=pk)
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, "Notice updated successfully!")
            return redirect('notice_detail', pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)
    
    context = {
        'form': form,
        'title': 'Edit Notice',
    }
    return render(request, 'notices/notice_form.html', context)


@login_required
def notice_delete(request, pk):
    """Delete notice"""
    if request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to delete notices.")
        return redirect('notice_list')
    
    notice = get_object_or_404(Notice, pk=pk)
    
    if request.method == 'POST':
        notice.delete()
        messages.success(request, "Notice deleted successfully!")
        return redirect('notice_list')
    
    context = {'notice': notice}
    return render(request, 'notices/notice_confirm_delete.html', context)


@login_required
def notice_archive(request):
    """View archived/expired notices"""
    if request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to view archives.")
        return redirect('notice_list')
    
    today = timezone.now().date()
    expired_notices = Notice.objects.filter(
        Q(expiry_date__lt=today) | Q(status='archived')
    ).select_related('category', 'author')
    
    paginator = Paginator(expired_notices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'is_archive': True,
    }
    return render(request, 'notices/notice_list.html', context)


# ========== Event Views ==========
@login_required
def event_list(request):
    """List all events"""
    today = timezone.now().date()
    
    # Filters
    event_type = request.GET.get('type')
    period = request.GET.get('period', 'upcoming')
    
    events = Event.objects.filter(is_active=True)
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    if period == 'upcoming':
        events = events.filter(start_date__gte=today)
    elif period == 'ongoing':
        events = events.filter(start_date__lte=today, end_date__gte=today)
    elif period == 'past':
        events = events.filter(end_date__lt=today)
    
    events = events.order_by('start_date')
    
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'period': period,
        'event_type': event_type,
    }
    return render(request, 'notices/event_list.html', context)


@login_required
def event_detail(request, pk):
    """View event details"""
    event = get_object_or_404(Event, pk=pk, is_active=True)
    
    context = {
        'event': event,
    }
    return render(request, 'notices/event_detail.html', context)


@login_required
def event_create(request):
    """Create new event"""
    if request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to create events.")
        return redirect('event_list')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, "Event created successfully!")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'title': 'Create Event',
    }
    return render(request, 'notices/event_form.html', context)


# ========== Circular Views ==========
@login_required
def circular_list(request):
    """List all circulars"""
    circulars = Circular.objects.filter(is_active=True).order_by('-issue_date')
    
    # Filter by type
    circ_type = request.GET.get('type')
    if circ_type:
        circulars = circulars.filter(circular_type=circ_type)
    
    paginator = Paginator(circulars, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'circ_type': circ_type,
    }
    return render(request, 'notices/circular_list.html', context)


@login_required
def circular_detail(request, pk):
    """View circular details"""
    circular = get_object_or_404(Circular, pk=pk, is_active=True)
    
    context = {
        'circular': circular,
    }
    return render(request, 'notices/circular_detail.html', context)


# ========== Notification Views ==========
@login_required
def notification_list(request):
    """View user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read
    if request.GET.get('mark_read'):
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('notification_list')
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'notices/notification_list.html', context)


@login_required
def notification_mark_read(request, pk):
    """Mark single notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    return redirect('notification_list')


@login_required
def bulk_notification(request):
    """Send bulk notifications"""
    if request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to send bulk notifications.")
        return redirect('notice_dashboard')
    
    if request.method == 'POST':
        form = BulkNotificationForm(request.POST)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            title = form.cleaned_data['title']
            message = form.cleaned_data['message']
            send_email = form.cleaned_data['send_email']
            send_sms = form.cleaned_data['send_sms']
            send_push = form.cleaned_data['send_push']
            
            recipients = []
            
            # Get recipients based on type
            if recipient_type == 'all_students':
                students = Student.objects.filter(is_active=True)
                recipients = [s.user for s in students if hasattr(s, 'user')]
            elif recipient_type == 'all_teachers':
                teachers = Teacher.objects.filter(is_active=True)
                recipients = [t.user for t in teachers if hasattr(t, 'user')]
            elif recipient_type == 'specific_class':
                target_class = form.cleaned_data['target_class']
                students = Student.objects.filter(current_class=target_class.name, is_active=True)
                recipients = [s.user for s in students if hasattr(s, 'user')]
            elif recipient_type == 'specific_students':
                students = form.cleaned_data['target_students']
                recipients = [s.user for s in students if hasattr(s, 'user')]
            
            # Create notifications
            for user in recipients:
                Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    notification_type='info'
                )
            
            # Log bulk action
            messages.success(request, f"Notifications sent to {len(recipients)} recipients.")
            return redirect('notice_dashboard')
    else:
        form = BulkNotificationForm()
    
    context = {
        'form': form,
        'title': 'Send Bulk Notification',
    }
    return render(request, 'notices/bulk_notification.html', context)


# ========== Category Views ==========
@login_required
def category_list(request):
    """List notice categories"""
    categories = NoticeCategory.objects.annotate(
        notice_count=Count('notices')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'notices/category_list.html', context)


@login_required
def category_create(request):
    """Create notice category"""
    if request.user.role not in ['super_admin', 'admin']:
        messages.error(request, "You don't have permission to create categories.")
        return redirect('category_list')
    
    if request.method == 'POST':
        form = NoticeCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully!")
            return redirect('category_list')
    else:
        form = NoticeCategoryForm()
    
    context = {
        'form': form,
        'title': 'Create Category',
    }
    return render(request, 'notices/category_form.html', context)
