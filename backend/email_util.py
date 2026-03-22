"""
Email sending utility with Brevo SMTP relay for production environments.
Supports both Brevo SMTP and fallback Gmail SMTP for local development.
"""
import smtplib
import socket
import time
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configure logging
logger = logging.getLogger(__name__)

# Check if we're using Brevo (production) or Gmail SMTP (development)
USE_BREVO = os.environ.get('BREVO_SMTP_PASSWORD') is not None
BREVO_SMTP_EMAIL = os.environ.get('BREVO_SMTP_EMAIL')
BREVO_SMTP_PASSWORD = os.environ.get('BREVO_SMTP_PASSWORD')
BREVO_FROM_EMAIL = os.environ.get('BREVO_FROM_EMAIL', 'noreply@monitormail.com')

class EmailSender:
    """Handles email sending with Brevo (production) or Gmail SMTP (development)."""
    
    def __init__(self, sender_email=None, sender_password=None, max_retries=3, timeout=30):
        """
        Initialize email sender.
        
        For production (with BREVO_SMTP_PASSWORD):
          - sender_email and sender_password are ignored
          - Uses Brevo SMTP relay automatically
          
        For development (without BREVO_SMTP_PASSWORD):
          - Uses Gmail SMTP (sender_email and sender_password required)
        """
        self.sender_email = sender_email or BREVO_FROM_EMAIL
        self.sender_password = sender_password
        self.max_retries = max_retries
        self.timeout = timeout
        self.server = None
        self.use_brevo = USE_BREVO
        
        if self.use_brevo:
            logger.info(f"Configured for Brevo SMTP relay (production)")
        else:
            logger.info(f"Configured for Gmail SMTP (development mode)")
    
    def connect(self):
        """
        Establish SMTP connection.
        
        Uses Brevo SMTP relay if BREVO_SMTP_PASSWORD is set.
        Falls back to Gmail SMTP otherwise.
        """
        if self.use_brevo:
            return self._connect_brevo()
        else:
            return self._connect_gmail()
    
    def _connect_brevo(self):
        """Connect to Brevo SMTP relay."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[Attempt {attempt}/{self.max_retries}] Connecting to Brevo SMTP...")
                
                socket.setdefaulttimeout(self.timeout)
                
                # Brevo SMTP Server (simple SMTP with email:password auth)
                self.server = smtplib.SMTP('smtp-relay.brevo.com', 587, timeout=self.timeout)
                self.server.ehlo()
                self.server.starttls()
                self.server.ehlo()
                
                # Brevo uses standard email:password authentication
                self.server.login(BREVO_SMTP_EMAIL, BREVO_SMTP_PASSWORD)
                
                logger.info("✅ Brevo SMTP connection successful!")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ Brevo authentication failed: {e}")
                self.server = None
                raise
            except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
                logger.warning(f"⚠️  Connection attempt {attempt} failed: {type(e).__name__}: {e}")
                self.server = None
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed to connect after {self.max_retries} attempts")
                    raise
            except Exception as e:
                logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
                self.server = None
                raise
        
        return False
    
    def _connect_gmail(self):
        """Connect to Gmail SMTP (for local development only)."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[Attempt {attempt}/{self.max_retries}] Connecting to Gmail SMTP...")
                
                socket.setdefaulttimeout(self.timeout)
                
                self.server = smtplib.SMTP('smtp.gmail.com', 587, timeout=self.timeout)
                self.server.ehlo()
                self.server.starttls()
                self.server.ehlo()
                self.server.login(self.sender_email, self.sender_password)
                
                logger.info("✅ Gmail SMTP connection successful!")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ Gmail authentication failed: {e}")
                self.server = None
                raise
            except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
                logger.warning(f"⚠️  Connection attempt {attempt} failed: {type(e).__name__}: {e}")
                self.server = None
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed to connect after {self.max_retries} attempts")
                    raise
            except Exception as e:
                logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
                self.server = None
                raise
        
        return False
    
    def send_email(self, to_email, subject, body_html, cc_email=None, attachment_data=None, attachment_filename=None):
        """
        Send a single email with optional attachment.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            cc_email: CC recipient (optional)
            attachment_data: Binary attachment data (optional)
            attachment_filename: Attachment filename (optional)
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not self.server:
                self.connect()
            
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            if cc_email:
                msg['Cc'] = cc_email
            msg['Subject'] = subject
            
            # Attach HTML body
            msg.attach(MIMEText(body_html, 'html'))
            
            # Attach file if provided
            if attachment_data and attachment_filename:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment_data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
                msg.attach(part)
            
            # Determine recipients
            recipients = [to_email]
            if cc_email and cc_email not in recipients:
                recipients.append(cc_email)
            
            # Send email
            logger.info(f"Sending email to {to_email}...")
            self.server.sendmail(self.sender_email, recipients, msg.as_string())
            logger.info(f"✅ Email sent to {to_email}")
            return True, "Email sent successfully"
            
        except (socket.timeout, socket.error, OSError) as e:
            error_msg = f"Network error: {type(e).__name__}"
            logger.error(f"❌ {error_msg}: {e}")
            self.server = None
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {e}"
            logger.error(f"❌ {error_msg}")
            self.server = None
            return False, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Unexpected error sending email: {error_msg}")
            self.server = None
            return False, error_msg
    
    def send_emails_batch(self, email_list, subject, body_html, attachment_data=None, attachment_filename=None):
        """
        Send emails to multiple recipients.
        
        Args:
            email_list: List of dicts with 'to', 'cc' (optional), 'name' keys
            subject: Email subject
            body_html: HTML email body
            attachment_data: Binary attachment data (optional)
            attachment_filename: Attachment filename (optional)
        
        Returns:
            list: Results for each email
        """
        results = []
        
        for idx, email_info in enumerate(email_list, 1):
            try:
                to_email = email_info.get('to')
                cc_email = email_info.get('cc')
                
                if not to_email or '@' not in to_email:
                    results.append({
                        'email': to_email or 'Unknown',
                        'status': 'failed',
                        'reason': 'Invalid email address'
                    })
                    continue
                
                success, msg = self.send_email(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    cc_email=cc_email,
                    attachment_data=attachment_data,
                    attachment_filename=attachment_filename
                )
                
                results.append({
                    'email': to_email,
                    'status': 'success' if success else 'failed',
                    'reason': msg if not success else None
                })
                
            except Exception as e:
                results.append({
                    'email': email_info.get('to', 'Unknown'),
                    'status': 'failed',
                    'reason': str(e)
                })
            
            logger.info(f"Progress: {idx}/{len(email_list)}")
        
        return results
    
    def logout(self):
        """Safely close SMTP connection."""
        try:
            if self.server:
                self.server.quit()
                logger.info("SMTP connection closed")
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
            try:
                if self.server:
                    self.server.close()
            except:
                pass
        finally:
            self.server = None
    
    def __enter__(self):
        """Context manager entry."""
        try:
            self.connect()
        except Exception as e:
            logger.error(f"Failed to connect in context manager: {e}")
            raise
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()
        return False
