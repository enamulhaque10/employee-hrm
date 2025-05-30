from django.core.management.base import BaseCommand
from employee.tasks import send_event_reminders,send_mail_casual_to_permanent_employee

class Command(BaseCommand):
    help = 'Send reminder emails for upcoming events.'

    def handle(self, *args, **kwargs):
        send_event_reminders()
        send_mail_casual_to_permanent_employee()
