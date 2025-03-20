from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Event, Registration
import datetime

# Create your tests here.


class BasicViewTests(TestCase):
    def test_home_status_code(self):

        # Test whether we can access the home page/访问首页

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_event_list_requires_login(self):
        """
        When accessing the event_list view without being logged in, the test first jumps to the login page/
        测试在未登录的情况下，访问 event_list 视图时，会先跳转到登录页面
        """
        response = self.client.get(reverse('event_list'))
        # 未登录时，会跳转到 LOGIN_URL (/login/)，返回 302
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/events/')

class UserRegistrationTest(TestCase):
    def test_user_registration_form(self):
        # Test registration/测试注册
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': '12345678',
            'confirm_password': '12345678'
        }
        response = self.client.post(reverse('register'), data=data)
        
        # After successful registration, go to the login page / 注册成功后直接跳转到登录页面
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('login'))

        # Check whether the user is valid
        self.assertTrue(User.objects.filter(username='testuser').exists())

class EventTests(TestCase):
    def setUp(self):

        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='test12345')
        
        self.client.login(username='testuser', password='test12345')

    def test_create_event_view(self):

        # Test creation activity
        data = {
            'title': 'Test Event',
            'description': 'Just a test',
            'date': '2025-03-20',
            'time': '12:00:00',
            'location': 'Campus Hall'
            # 'sync_to_calendar': True
        }
        response = self.client.post(reverse('create_event'), data=data)

        # After the creation is successful, go to 'event_list'
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event_list'))

        event = Event.objects.filter(title='Test Event').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.organizer.username, 'testuser')

    def test_register_for_event(self):
        # Test if you can successfully sign up for the event
        event = Event.objects.create(
            title='Another Event',
            description='Test Desc',
            date=datetime.date(2025, 5, 1),
            time=datetime.time(10, 0, 0),
            location='Library',
            organizer=self.user
        )

        response = self.client.get(reverse('register_for_event', args=[event.id]))
        
        self.assertRedirects(response, reverse('event_detail', args=[event.id]))

        # 检查Registration表
        reg = Registration.objects.filter(user=self.user, event=event).first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.status, 'Registered')
