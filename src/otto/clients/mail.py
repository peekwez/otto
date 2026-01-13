from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from otto.core.logging import get_logger
from otto.core.settings import get_settings


def send_mail(
    to_emails: str = "jad.dimachkieh@gmail.com",
    subject: str = "Sending with Twilio SendGrid is Fun",
    content: str = "<strong>and easy to do anywhere, even with Python</strong>",
) -> None:
    settings = get_settings()
    logger = get_logger(__name__)
    logger.info(f"Sending email to {to_emails} with subject '{subject}'")
    message = Mail(
        from_email="kwesi@kwap-consulting.com",
        to_emails=to_emails,
        subject=subject,
        html_content=content,
    )
    try:
        sg = SendGridAPIClient(settings.sendgrid.api_key.get_secret_value())
        # sg.set_sendgrid_data_residency("eu")
        # uncomment the above line if you are sending mail using a regional EU sub user
        response = sg.send(message)
        logger.info(f"Email sent with status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
