#!/usr/bin/env python3
"""
Email Sending Debugger
Comprehensive test to figure out why emails aren't arriving.
Run: python debug_email_sending.py
"""

import os
import sys
import json
import requests
from email_util import EmailSender, USE_BREVO, BREVO_API_KEY, BREVO_FROM_EMAIL, BREVO_API_URL


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def validate_email(email):
    """Check if email format is valid."""
    if not email or not isinstance(email, str):
        return False, "Email is empty or not a string"
    if '@' not in email:
        return False, "Missing @ symbol"
    parts = email.split('@')
    if len(parts) != 2:
        return False, "Multiple @ symbols"
    local, domain = parts
    if not local:
        return False, "Empty local part (before @)"
    if not domain or '.' not in domain:
        return False, "Invalid domain"
    return True, "Valid"


def test_email_configuration():
    """Test email configuration."""
    print_section("Email Configuration Status")
    
    print(f"USE_BREVO: {USE_BREVO}")
    print(f"BREVO_API_KEY configured: {bool(BREVO_API_KEY)}")
    if BREVO_API_KEY:
        print(f"   Key preview: {BREVO_API_KEY[:10]}...{BREVO_API_KEY[-5:]}")
    print(f"BREVO_FROM_EMAIL: {BREVO_FROM_EMAIL}")
    
    if not USE_BREVO:
        print("\n❌ Brevo API is NOT configured!")
        print("   Set BREVO_API_KEY environment variable")
        return False
    
    print("\n✅ Brevo is configured")
    
    # Validate sender email
    is_valid, msg = validate_email(BREVO_FROM_EMAIL)
    if not is_valid:
        print(f"❌ BREVO_FROM_EMAIL is invalid: {msg}")
        return False
    
    print(f"✅ BREVO_FROM_EMAIL format is valid")
    
    # Check if it's using default
    if BREVO_FROM_EMAIL == 'noreply@monitormail.com':
        print("\n⚠️  WARNING: Using default BREVO_FROM_EMAIL!")
        print("   This email might NOT be verified in your Brevo account")
        print("   Change to a verified email from your Brevo account")
        return False
    
    return True


def test_recipient_email(email):
    """Test if recipient email is valid."""
    print_section(f"Testing Recipient Email: {email}")
    
    is_valid, msg = validate_email(email)
    print(f"Email format validation: {msg}")
    
    if not is_valid:
        print(f"❌ Invalid recipient email!")
        return False
    
    print(f"✅ Recipient email is valid")
    return True


def test_send_via_api(recipient_email):
    """Test sending a real email via Brevo API."""
    print_section("Testing Email Send via Brevo API")
    
    if not USE_BREVO or not BREVO_API_KEY:
        print("❌ Brevo not configured, skipping API test")
        return False
    
    headers = {
        'accept': 'application/json',
        'api-key': BREVO_API_KEY,
        'content-type': 'application/json'
    }
    
    payload = {
        'sender': {
            'name': 'MonitorMail Debug',
            'email': BREVO_FROM_EMAIL
        },
        'to': [{'email': recipient_email}],
        'subject': '🧪 MonitorMail Email Test',
        'htmlContent': '''
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>🧪 Email Test from MonitorMail</h2>
                <p>If you received this email, the email sending system is working correctly!</p>
                <p><strong>Test timestamp:</strong> {}</p>
                <hr/>
                <p><small>This is an automated test email. You can safely delete it.</small></p>
            </body>
        </html>
        '''.format(__import__('datetime').datetime.now().isoformat())
    }
    
    print(f"Sending test email to: {recipient_email}")
    print(f"From: {BREVO_FROM_EMAIL}")
    print(f"API URL: {BREVO_API_URL}")
    
    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in (200, 201):
            print("\n✅ API returned success (201/200)")
            try:
                data = response.json()
                if 'messageId' in data:
                    print(f"   Message ID: {data['messageId']}")
            except:
                pass
            
            print("\n📋 Next Steps:")
            print("   1. Check your email inbox for the test email")
            print("   2. If not there, check SPAM/PROMOTIONS folder")
            print("   3. If still not there after 2-3 minutes, check Brevo dashboard:")
            print("      - https://app.brevo.com → Activity → Emails")
            return True
        else:
            print(f"\n❌ API returned error status {response.status_code}")
            if response.status_code == 401:
                print("   Possible issues:")
                print("   - BREVO_API_KEY is invalid or expired")
                print("   - Check your Brevo account for a new API key")
            elif response.status_code == 400:
                print("   Bad request - check email addresses")
            return False
            
    except requests.Timeout:
        print("❌ API request timed out")
        return False
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_brevo_dashboard_instructions():
    """Show how to check Brevo dashboard."""
    print_section("Checking Brevo Dashboard")
    
    print("To verify emails are being sent:")
    print("\n1. Log in to Brevo: https://app.brevo.com")
    print("2. Go to: Settings → Activity → Emails")
    print("3. Look for your test email")
    print("4. Check the status:")
    print("   ✅ 'Sent' = email delivered to mail server")
    print("   ⏳ 'Pending' = waiting to be sent")
    print("   ❌ 'Failed' = something went wrong (click for details)")
    print("   📧 'Opened' = recipient opened the email")
    print("\nIf status is 'Sent' but you didn't receive it:")
    print("   → Check your SPAM/PROMOTIONS folder")
    print("   → Check that recipient email is correct")
    print("   → BREVO_FROM_EMAIL sender must be verified")


def main():
    """Run all diagnostics."""
    print("\n🔍 MonitorMail Email Sending Debugger")
    print("=" * 70)
    
    # Step 1: Check configuration
    config_ok = test_email_configuration()
    if not config_ok:
        print("\n❌ Configuration issue detected. Fix and retry.")
        sys.exit(1)
    
    # Step 2: Get test email
    print("\n" + "=" * 70)
    test_email = input("Enter a test email address to send to: ").strip()
    
    if not test_email:
        print("❌ No email provided")
        sys.exit(1)
    
    # Step 3: Validate recipient
    if not test_recipient_email(test_email):
        print("❌ Invalid recipient email")
        sys.exit(1)
    
    # Step 4: Send test email
    result = test_send_via_api(test_email)
    
    if result:
        check_brevo_dashboard_instructions()
        
        print("\n" + "=" * 70)
        print("🔄 Troubleshooting Steps:")
        print("=" * 70)
        print("1️⃣  Check your INBOX and SPAM/PROMOTIONS folder")
        print("2️⃣  Wait 2-3 minutes (sometimes takes time)")
        print("3️⃣  Check Brevo dashboard (app.brevo.com → Activity)")
        print("4️⃣  Verify BREVO_FROM_EMAIL is fully verified in Brevo")
        print("5️⃣  If still issues, check the Brevo docs:")
        print("     https://developers.brevo.com/docs/send-transactional-emails")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
