import calendar
import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from .models import Event, Registration
from .forms import UserRegistrationForm, EventForm
from .google_calendar import create_calendar_event, update_calendar_event

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            messages.success(request, 'Registration successful. You can log in now .')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('event_list')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def event_list(request):
    events = Event.objects.all().order_by('date', 'time')
    return render(request, 'event_list.html', {'events': events})

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registered = Registration.objects.filter(user=request.user, event=event).exists()
    return render(request, 'event_detail.html', {'event': event, 'registered': registered})

@login_required
def create_event(request):
    # Create a new event and optionally sync to Google Calendar
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            sync_to_calendar = form.cleaned_data.get('sync_to_calendar', False)
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()

            # If Sync to Google Calendar is checked
            if sync_to_calendar:
                calendar_id = create_calendar_event(event)
                event.calendar_event_id = calendar_id
                event.save()

            messages.success(request, 'Event created successfully.')
            return redirect('event_list')
    else:
        form = EventForm()
    return render(request, 'create_event.html', {'form': form})

@login_required
def edit_event(request, event_id):
    # Edit existing events and update them to Google Calendar.
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            sync_to_calendar = form.cleaned_data.get('sync_to_calendar', False)
            event = form.save(commit=False)
            event.save()

            if sync_to_calendar:
                # calendar_event_id is updated if it exists; otherwise, it is created first
                if event.calendar_event_id:
                    update_calendar_event(event)
                else:
                    new_id = create_calendar_event(event)
                    event.calendar_event_id = new_id
                    event.save()

            messages.success(request, 'Event updated successfully.')
            return redirect('event_detail', event_id=event.id)
    else:
        # Set sync_to_calendar to True for front-end display
        
        form = EventForm(instance=event, initial={'sync_to_calendar': True})
    return render(request, 'create_event.html', {'form': form, 'edit_mode': True})

@login_required
def delete_event(request, event_id):
    # Delete the event and (optionally) delete the corresponding event on Google Calendar
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    if request.method == 'POST':
        # delete_calendar_event(event)
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('event_list')
    return render(request, 'event_detail.html', {'event': event})

@login_required
def register_for_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    reg, created = Registration.objects.get_or_create(user=request.user, event=event)
    if created:
        messages.success(request, f'You have registered for {event.title}.')
    else:
        messages.info(request, 'You are already registered for this event.')
    return redirect('event_detail', event_id=event.id)


@login_required
def cancel_registration(request, event_id):
    """
    取消当前用户对某个活动的注册（将状态改为 'Canceled'）。
    """
    event = get_object_or_404(Event, id=event_id)
    registration = get_object_or_404(Registration, user=request.user, event=event)

    if request.method == "POST":
        registration.status = "Canceled"
        registration.save()
        messages.success(request, f'You have canceled your registration for {event.title}.')
        return redirect('my_events')

    # 若是 GET 请求，跳转到二次确认页面
    return render(request, 'confirm_cancel.html', {'event': event})

@login_required
def my_events(request):
    registrations = Registration.objects.filter(user=request.user)

    today = datetime.date.today()

    # 用一个列表来存储已注册的活动信息，避免在模板中查找字典
    user_events_by_date = []
    for reg in registrations:
        event_date = reg.event.date
        if event_date.year == today.year and event_date.month == today.month:
            user_events_by_date.append((event_date.day, reg.event.title))

    # 生成当月的所有天
    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(today.year, today.month))

    # 将天数分组成“周”
    weeks = []
    temp = []
    for idx, day in enumerate(month_days):
        if idx % 7 == 0 and idx != 0:
            weeks.append(temp)
            temp = []
        temp.append(day)
    if temp:
        weeks.append(temp)

    context = {
        'registrations': registrations,
        'year': today.year,
        'month': today.month,
        'month_name': today.strftime('%B'),
        'weeks': weeks,  
        'user_events_by_date': user_events_by_date,  # 直接传递列表
    }
    return render(request, 'my_events.html', context)

@login_required
def unregister_event(request, event_id):
    """
    用户取消报名（硬删除数据库记录），从“我的活动”中移除，并允许后续重新报名。
    如果有Google Calendar集成，也可在此同步删除。
    """
    event = get_object_or_404(Event, id=event_id)
    reg = Registration.objects.filter(user=request.user, event=event).first()
    if not reg:
        messages.warning(request, 'You are not registered for this event.')
        return redirect('my_events')

    if request.method == 'POST':
        # 硬删除报名记录
        reg.delete()
        # 如果有Google Calendar 同步报名功能，这里也要删除/更新
        # remove_registration_from_calendar(...)

        messages.success(request, f'You have successfully unregistered from {event.title}.')
        return redirect('my_events')

    # 如果是GET请求，先跳转到确认页面
    return render(request, 'unregister_confirm.html', {'event': event})