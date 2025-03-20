import datetime
from django.conf import settings
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account

def get_calendar_service():
    """
    Creates and returns a Google Calendar API service object.
    The service_account.json file and the corresponding permission Settings are required.
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

def create_calendar_event(event_obj):
    # Create a new event in Google Calendar and return the event ID.
    service = get_calendar_service()
    start_datetime = datetime.datetime.combine(event_obj.date, event_obj.time)
    end_datetime = start_datetime + datetime.timedelta(hours=1)  # The default duration is 1 hour

    # Constructs the Google Calendar event data to be created
    event_data = {
        'summary': event_obj.title,
        'description': event_obj.description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'UTC',
        },
        'location': event_obj.location,
    }
    created_event = service.events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=event_data).execute()
    return created_event.get('id')

def update_calendar_event(event_obj):
    # Update event information.
    service = get_calendar_service()
    if not event_obj.calendar_event_id:
        return  # If we cannot update without an ID, consider creating first

    start_datetime = datetime.datetime.combine(event_obj.date, event_obj.time)
    end_datetime = start_datetime + datetime.timedelta(hours=1)

    event_data = {
        'summary': event_obj.title,
        'description': event_obj.description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'UTC',
        },
        'location': event_obj.location,
    }
    updated_event = service.events().patch(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        eventId=event_obj.calendar_event_id,
        body=event_data
    ).execute()
    return updated_event.get('id')

def delete_calendar_event(event_obj):
    # Delete an event from Google Calendar
    service = get_calendar_service()
    if event_obj.calendar_event_id:
        service.events().delete(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            eventId=event_obj.calendar_event_id
        ).execute()
