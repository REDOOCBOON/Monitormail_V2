#!/usr/bin/env python3
"""
Brevo Email Diagnostic Tool
Tests Brevo email sending and provides detailed debugging information.
Run: python test_brevo_diagnostic.py
"""

import os
import sys
import json
from email_util import EmailSender, USE_BREVO, BREVO_API_KEY, BREVO_FROM_EMAIL, BREVO_API_URL

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_environment():
    """Test if environment is properly configured."""
    print_section("Environment Configuration")
    
    print(f"USE_BREVO: {USE_BREVO}")
    print(f"BREVO_API_KEY set: {bool(BREVO_API_KEY)}")
    if BREVO_API_KEY:
        print(f"BREVO_API_KEY (masked): {BREVO_API_KEY[:10]}...{BREVO_API_KEY[-5:]}")
    print(f"BREVO_FROM_EMAIL: {BREVO_FROM_EMAIL}")
    print(f"BREVO_API_URL: {BREVO_API_URL}")
    
    if not USE_BREVO:
        print("\n⚠️  WARNING: Brevo is NOT configured!")
        print("   Set BREVO_API_KEY environment variable to use Brevo.")
        print("   Otherwise, Gmail SMTP will be used (requires GMAIL_PASSWORD)")
        gmail_password = os.environ.get('GMAIL_PASSWORD')
        print(f"   GMAIL_PASSWORD set: {bool(gmail_password)}")
        if not gmail_password:
            print("   ❌ Neither Brevo nor Gmail is configured!")
            return False
    else:
        print("✅ Brevo is configured")
    
    return True

def test_email_sender_initialization():
    """Test EmailSender initialization."""
    print_section("EmailSender Initialization")
    
    try:
        sender = EmailSender(
            sender_email="test@monitormail.com", 
            sender_password=None,
            max_retries=1,
            timeout=10
        )
        print(f"✅ EmailSender initialized successfully")
        print(f"   - use_brevo: {sender.use_brevo}")
        print(f"   - sender_email: {sender.sender_email}")
        return True, sender
    except Exception as e:
        print(f"❌ Failed to initialize EmailSender: {e}")
        return False, None

def test_send_test_email(sender):
    """Test sending a test email."""
    print_section("Test Email Sending")
    
    test_to_email = "test@example.com"  # Use a test email
    test_subject = "MonitorMail Test Email"
    test_body = "<p>This is a test email from MonitorMail diagnostic.</p><p>If you received this, email sending is working!</p>"
    test_cc = "cc@example.com"
    
    print(f"Sending test email:")
    print(f"  To: {test_to_email}")
    print(f"  CC: {test_cc}")
    print(f"  Subject: {test_subject}")
    print(f"  Using: {'Brevo API' if sender.use_brevo else 'Gmail SMTP'}")
    
    try:
        success, message = sender.send_email(
            to_email=test_to_email,
            subject=test_subject,
            body_html=test_body,
            cc_email=test_cc
        )
        
        if success:
            print(f"✅ Email sent successfully!")
            print(f"   Message: {message}")
        else:
            print(f"❌ Email sending failed!")
            print(f"   Error: {message}")
        
        return success
    except Exception as e:
        print(f"❌ Exception occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sender.logout()

def test_brevo_api_directly():
    """Test Brevo API directly with a raw request."""
    if not USE_BREVO:
        print("\nℹ️  Skipping direct API test (Brevo not configured)")
        return
    
    print_section("Direct Brevo API Test")
    
    try:
        import requests
    except ImportError:
        print("❌ requests library not installed")
        return
    
    headers = {
        'accept': 'application/json',
        'api-key': BREVO_API_KEY,
        'content-type': 'application/json'
    }
    
    payload = {
        'sender': {
            'name': 'MonitorMail',
            'email': BREVO_FROM_EMAIL
        },
        'to': [{'email': 'test@example.com'}],
        'subject': 'Direct API Test',
        'htmlContent': '<p>Direct API test</p>'
    }
    
    print(f"Making direct request to: {BREVO_API_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in (200, 201):
            print("✅ API request was successful!")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ API request failed: {type(e).__name__}: {e}")

def main():
    """Run all diagnostics."""
    print("\n🔍 MonitorMail Email Diagnostic Tool")
    print("=" * 70)
    
    # Test environment
    if not test_environment():
        print("\n❌ Email service is not properly configured!")
        sys.exit(1)
    
    # Test EmailSender initialization
    success, sender = test_email_sender_initialization()
    if not success or not sender:
        print("\n❌ Failed to initialize EmailSender!")
        sys.exit(1)
    
    # Test sending email
    # Note: This will only work if the sender email is verified in Brevo
    # or if Gmail SMTP is being used with proper credentials
    print("\nℹ️  WARNING: Test email will only succeed if:")
    if sender.use_brevo:
        print("   - BREVO_FROM_EMAIL is verified in your Brevo account")
    else:
        print("   - Your Gmail is using an app password (not regular password)")
        print("   - Two-factor authentication is enabled and allowed for app passwords")
    
    response = input("\nProceed with test email send? (y/n): ").strip().lower()
    if response == 'y':
        test_send_test_email(sender)
    
    # Direct Brevo API test
    if USE_BREVO:
        test_brevo_api_directly()
    
    print("\n" + "="*70)
    print("Diagnostic complete!")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
