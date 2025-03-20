from django.contrib import admin

# Register your models here.
# events/admin.py
from django.contrib import admin
from .models import Event, Registration

admin.site.register(Event)
admin.site.register(Registration)
