# email_utils.py
from django.core.mail import send_mail
from django.conf import settings


def send_html_email(subject, html_message, recipient_list, from_email=None):
    """
    Send HTML formatted email

    Args:
        subject (str): Email subject
        html_message (str): HTML content of the email
        recipient_list (list): List of recipient email addresses
        from_email (str, optional): Sender email address. Defaults to settings.DEFAULT_FROM_EMAIL.

    Returns:
        bool: Whether the email was sent successfully
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Plain text alternative for email clients that don't support HTML
    plain_message = html_message.replace('<br>', '\n').replace('</p><p>', '\n\n')
    plain_message = ''.join([i if ord(i) < 128 else ' ' for i in plain_message])

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False