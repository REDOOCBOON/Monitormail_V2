#!/usr/bin/env python3
"""
Direct test of the email sending endpoint logic
"""

from email_util import EmailSender
import logging

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_email_endpoint():
    """Test the exact same email sending logic the endpoint uses"""
    
    print("="*60)
    print("  Testing Email Endpoint Logic")
    print("="*60)
    
    sender_email = "ujjwal3rd@gmail.com"
    sender_password = "ajps ucvj ohto wndw"
    
    student = {
        "reg_no": "RA1234567890123",
        "name": "Test Student",
        "student_email": "ujjwal3rd@gmail.com",
        "parent_email": None,
        "subject": "Test Email from Endpoint",
        "email_body": "This is a test email from the MonitorMail endpoint"
    }
    
    print(f"\nTesting email send with:")
    print(f"  Sender: {sender_email}")
    print(f"  Recipient: {student['student_email']}")
    print(f"  Subject: {student['subject']}")
    
    try:
        # This is the exact logic from the endpoint
        email_sender = EmailSender(sender_email, sender_password, max_retries=3, timeout=30)
        
        print(f"\n1. Connecting to SMTP...")
        email_sender.connect()
        print(f"✅ Connected!")
        
        print(f"\n2. Preparing email...")
        to_email = student['student_email']
        subject = student.get('subject', "Important: Attendance Notification")
        body_html = student.get('email_body', '').replace('\n', '<br>')
        cc_email = student.get('parent_email')
        
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Body length: {len(body_html)} chars")
        
        print(f"\n3. Sending email...")
        success, msg = email_sender.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            cc_email=cc_email
        )
        
        print(f"   Result: {msg}")
        
        if success:
            print(f"\n✅ Email sent successfully!")
        else:
            print(f"\n❌ Failed: {msg}")
        
        print(f"\n4. Closing connection...")
        email_sender.logout()
        print(f"✅ Closed!")
        
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = test_email_endpoint()
    exit(0 if result else 1)
