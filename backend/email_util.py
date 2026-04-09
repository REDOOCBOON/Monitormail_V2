"""
Email sending utility with Brevo REST API for production environments.
Uses Brevo's HTTP API instead of SMTP (more reliable on cloud platforms like Vercel).
Supports fallback Gmail SMTP for local development.
"""
import requests
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
USE_BREVO = os.environ.get('BREVO_API_KEY') is not None and bool(os.environ.get('BREVO_API_KEY', '').strip())
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '').strip()  # Strip whitespace/newlines
BREVO_FROM_EMAIL = os.environ.get('BREVO_FROM_EMAIL', 'noreply@monitormail.com')
BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'

# Log configuration on startup
if not USE_BREVO:
    logger.info("📧 Brevo API key not configured. Defaulting to Gmail SMTP for email sending.")

class EmailSender:
    """Handles email sending with Brevo API (production) or Gmail SMTP (development)."""
    
    def __init__(self, sender_email=None, sender_password=None, max_retries=3, timeout=30):
        """
        Initialize email sender.
        
        For production (with BREVO_API_KEY):
          - Uses Brevo REST API (HTTP-based, more reliable on cloud platforms like Vercel)
          - sender_email and sender_password are ignored
          
        For development (without BREVO_API_KEY):
          - Uses Gmail SMTP
          - Requires sender_email and sender_password
        """
        self.sender_email = sender_email or BREVO_FROM_EMAIL
        self.sender_password = sender_password
        self.max_retries = max_retries
        self.timeout = timeout
        self.server = None
        self.use_brevo = USE_BREVO
        
        if self.use_brevo:
            logger.info(f"📧 Configured for Brevo REST API (production - HTTP-based)")
            if not BREVO_FROM_EMAIL or BREVO_FROM_EMAIL == 'noreply@monitormail.com':
                logger.warning(f"⚠️  WARNING: BREVO_FROM_EMAIL is using default '{BREVO_FROM_EMAIL}'")
                logger.warning(f"   This email MUST be verified in your Brevo account for emails to send!")
                logger.warning(f"   Set BREVO_FROM_EMAIL environment variable to a verified email address in Brevo")
        else:
            logger.info(f"📧 Configured for Gmail SMTP (development mode)")
    
    def connect(self):
        """Not needed for Brevo API (stateless HTTP). For Gmail, establish SMTP connection."""
        if self.use_brevo:
            logger.info("✅ Brevo API ready (no connection needed - stateless HTTP)")
            return True
        else:
            return self._connect_gmail()
    
    def _send_via_brevo_api(self, to_email, subject, body_html, cc_email=None, attachment_data=None, attachment_filename=None):
        """Send email via Brevo REST API (reliable on cloud platforms like Vercel)."""
        headers = {
            'accept': 'application/json',
            'api-key': BREVO_API_KEY,
            'content-type': 'application/json'
        }
        
        # CRITICAL: Use verified BREVO_FROM_EMAIL (configured in Brevo account)
        # The self.sender_email (teacher email) is NOT verified in Brevo and will be rejected
        # We must use the confirmed sender email from Brevo
        sender_email = BREVO_FROM_EMAIL
        sender_name = 'MonitorMail' if sender_email == BREVO_FROM_EMAIL else f'MonitorMail ({self.sender_email})'
        
        payload = {
            'sender': {
                'name': sender_name,
                'email': sender_email
            },
            'to': [{'email': to_email}],
            'subject': subject,
            'htmlContent': body_html
        }
        
        if cc_email:
            payload['cc'] = [{'email': cc_email}]
        
        # Note: File attachments via API require base64 encoding
        # For now, we'll skip attachments in API mode (can be added later if needed)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[Attempt {attempt}/{self.max_retries}] Sending via Brevo API to {to_email}...")
                logger.debug(f"   From: {sender_email}")
                if cc_email:
                    logger.debug(f"   CC: {cc_email}")
                response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=self.timeout)
                
                if response.status_code in (200, 201):
                    logger.info(f"✅ Email sent via Brevo API to {to_email}")
                    return True, "Email sent successfully"
                elif response.status_code == 400:
                    logger.error(f"❌ Bad request: {response.text}")
                    return False, f"Bad request: {response.text}"
                elif response.status_code == 401:
                    logger.error(f"❌ Invalid API key")
                    return False, "Invalid Brevo API key"
                elif response.status_code == 429:
                    logger.warning(f"⚠️  Rate limited (attempt {attempt}/{self.max_retries})")
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return False, "Rate limited - too many requests"
                else:
                    logger.warning(f"⚠️  API error (attempt {attempt}/{self.max_retries}): {response.status_code}")
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return False, f"Brevo API error: {response.status_code}"
                        
            except requests.Timeout:
                logger.warning(f"⚠️  API timeout (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return False, "API timeout after retries"
            except requests.RequestException as e:
                logger.warning(f"⚠️  Request error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return False, f"Network error: {str(e)}"
            except Exception as e:
                logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
                return False, f"Error: {str(e)}"
        
        return False, "Failed to send email"
    
    def _connect_gmail(self):
        """Connect to Gmail SMTP (for local development only)."""
        # Check if password is available
        if not self.sender_password:
            logger.error("❌ Gmail SMTP requires sender_password. None provided.")
            raise ValueError("Gmail SMTP password is required but not provided.")
        
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
            # Use Brevo API if available (production)
            if self.use_brevo:
                return self._send_via_brevo_api(to_email, subject, body_html, cc_email, attachment_data, attachment_filename)
            
            # Fall back to Gmail SMTP for development
            # Check if we have credentials before trying to connect
            if not self.sender_password:
                logger.error("❌ No email credentials available. Set BREVO_API_KEY environment variable or configure Gmail credentials.")
                return False, "Email service not properly configured. No credentials available."
            
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
            if attachment_filename and attachment_data:
                try:
                    part = MIMEBase('application', 'octet-stream')
                    # Ensure attachment_data is bytes
                    if isinstance(attachment_data, str):
                        attachment_data = attachment_data.encode('utf-8')
                    elif attachment_data is None:
                        logger.warning(f"Attachment data is None, skipping attachment")
                        attachment_data = None
                    
                    if attachment_data:  # Only attach if we have data
                        part.set_payload(attachment_data)
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
                        msg.attach(part)
                except Exception as attach_err:
                    logger.warning(f"Failed to attach file: {attach_err}. Continuing without attachment.")
                    # Continue sending email even if attachment fails
            
            # Determine recipients
            recipients = [to_email]
            if cc_email and cc_email not in recipients:
                recipients.append(cc_email)
            
            # Send email
            logger.info(f"Sending email to {to_email} via Gmail SMTP...")
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
