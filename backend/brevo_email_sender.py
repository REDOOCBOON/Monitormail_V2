"""
Brevo Email Sender - Send emails using Brevo SMTP relay or API
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)


class BrevoEmailSender:
    """Send emails using Brevo SMTP API"""
    
    def __init__(self):
        self.api_key = os.environ.get('BREVO_API_KEY', '').strip()
        self.api_url = "https://api.brevo.com/v3/smtp/email"
        self.from_email = os.environ.get('BREVO_FROM_EMAIL', 'noreply@monitormail.com')
        self.from_name = "MonitorMail"
        
        if not self.api_key:
            logger.warning("⚠️ BREVO_API_KEY not configured")
    
    def send_email(self, to_email, subject, body_html, cc_email=None, attachment_data=None, attachment_filename=None):
        """
        Send email via Brevo API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            cc_email: CC email (optional)
            attachment_data: Binary attachment data (optional, not supported yet)
            attachment_filename: Attachment filename (optional)
        
        Returns:
            (success: bool, message: str)
        """
        if not self.api_key:
            return (False, "Brevo API key not configured")
        
        # Build the email payload
        payload = {
            "sender": {
                "email": self.from_email,
                "name": self.from_name
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": body_html
        }
        
        # Add CC if provided
        if cc_email and cc_email != to_email:
            payload["cc"] = [{"email": cc_email}]
        
        # Prepare headers
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.api_key
        }
        
        try:
            logger.info(f"Sending email via Brevo to {to_email}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Check if request was successful
            if response.status_code in [200, 201]:
                logger.info(f"✅ Email sent to {to_email} via Brevo API")
                return (True, f"Email sent successfully. Message ID: {response.json().get('messageId', 'N/A')}")
            else:
                error_msg = response.text or f"HTTP {response.status_code}"
                logger.error(f"❌ Brevo API error: {error_msg}")
                return (False, f"Brevo API error: {error_msg}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Brevo request error: {str(e)}")
            return (False, f"Brevo request error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Brevo error: {str(e)}")
            return (False, f"Brevo error: {str(e)}")

    def logout(self):
        """No-op logout method for API consistency. Brevo doesn't use persistent connections."""
        logger.info("Brevo email sender session closed")


def is_brevo_configured():
    """Check if Brevo API key is configured"""
    return bool(os.environ.get('BREVO_API_KEY', '').strip())
