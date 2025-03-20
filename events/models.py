from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')

    # When syncing to Google Calendar, you can record the returned Calendar Event ID
    calendar_event_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.title

class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=20, default='Registered')  # 或 Canceled

    def __str__(self):
        return f"{self.user.username} -> {self.event.title}"
