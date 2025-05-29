# myapp/tasks.py

from django.utils import timezone
from datetime import datetime
from .models import EventCalender
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_event_reminders():
    now = timezone.now().date()
    calendar_events = EventCalender.objects.filter(reminder_date__date=now)

    for event in calendar_events:
        sender_email = "enamulcse12@gmail.com"
        receiver_email = event.reminder_person or "fallback@example.com"
        app_password = "iorg yewo vzwp gtgx"

        subject = event.event_title
        email_body_html = f"""
            <html>
            <body>
                <p>This is a reminder for the event: <strong>{event.event_title}</strong>.</p>
                <p>Event Date: <strong>{event.event_date}</strong></p>
                <p>Description: <strong>{event.event_description}</strong></p>
            </body>
            </html>
        """

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(email_body_html, "html"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print(f"Reminder sent to {receiver_email}")
        except Exception as e:
            print(f"Error sending email: {e}")
        finally:
            server.quit()
