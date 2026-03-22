#!/usr/bin/env python3
"""
Email Configuration Tester
Tests SMTP connectivity and Gmail credentials before deploying.
Run: python test_email_config.py
"""

import sys
import socket
import smtplib
from email_util import EmailSender
import getpass


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_dns_resolution():
    """Test DNS resolution for SMTP server."""
    print_section("Testing DNS Resolution")
    try:
        ip = socket.gethostbyname('smtp.gmail.com')
        print(f"✅ DNS Resolution: smtp.gmail.com -> {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS Resolution Failed: {e}")
        print("   This means your network cannot reach Gmail SMTP server.")
        print("   Check: Firewall settings, VPN, ISP restrictions")
        return False


def test_smtp_connection(host='smtp.gmail.com', port=587):
    """Test SMTP server connection."""
    print_section("Testing SMTP Connection")
    try:
        print(f"Connecting to {host}:{port}...")
        server = smtplib.SMTP(host, port, timeout=10)
        print(f"✅ SMTP Connection successful")
        server.ehlo()
        print(f"✅ EHLO successful")
        server.starttls()
        print(f"✅ STARTTLS successful")
        server.quit()
        return True
    except socket.timeout:
        print(f"❌ SMTP Connection Timeout")
        print("   This means the server is not responding within 10 seconds.")
        print("   Check: Firewall blocking port 587, Network connectivity")
        return False
    except ConnectionRefusedError:
        print(f"❌ SMTP Connection Refused")
        print("   Check: Host and port are correct, Firewall not blocking port 587")
        return False
    except Exception as e:
        print(f"❌ SMTP Connection Error: {type(e).__name__}: {e}")
        return False


def test_gmail_credentials():
    """Test Gmail authentication."""
    print_section("Testing Gmail Credentials")
    
    email = input("\nEnter Gmail email address: ").strip()
    password = getpass.getpass("Enter Gmail App Password (NOT regular password): ")
    
    if not email or not password:
        print("❌ Email or password is empty")
        return False
    
    try:
        print(f"\nTesting credentials for: {email}")
        sender = EmailSender(email, password, max_retries=1, timeout=15)
        sender.connect()
        print("✅ Gmail authentication successful!")
        sender.logout()
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail Authentication Failed")
        print("   Check: Email address and App Password are correct")
        print("   Remember: Use App Password, NOT your regular password")
        print("   Get it from: https://myaccount.google.com/security")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


def test_email_sending():
    """Test actual email sending."""
    print_section("Testing Email Sending")
    
    email = input("Enter Gmail email address: ").strip()
    password = getpass.getpass("Enter Gmail App Password: ")
    recipient = input("Enter test recipient email: ").strip()
    
    if not all([email, password, recipient]):
        print("❌ Missing required information")
        return False
    
    try:
        print(f"\nSending test email from {email} to {recipient}...")
        sender = EmailSender(email, password, max_retries=1, timeout=15)
        sender.connect()
        
        success, msg = sender.send_email(
            to_email=recipient,
            subject="MonitorMail - SMTP Test",
            body_html="<h2>SMTP Test Successful!</h2><p>If you received this email, your configuration is working correctly.</p>"
        )
        
        sender.logout()
        
        if success:
            print("✅ Email sent successfully!")
            print(f"   Check {recipient} inbox (and spam folder)")
            return True
        else:
            print(f"❌ Failed to send email: {msg}")
            return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  MonitorMail Email Configuration Tester")
    print("  This tool helps diagnose email configuration issues")
    print("="*60)
    
    results = {}
    
    # Run tests
    results['DNS'] = test_dns_resolution()
    results['SMTP'] = test_smtp_connection()
    
    print_section("Testing Gmail Credentials")
    response = input("\nRun Gmail credential test? (y/n): ").strip().lower()
    if response == 'y':
        results['Gmail'] = test_gmail_credentials()
    
    if response == 'y':
        print_section("Testing Email Sending")
        response2 = input("\nRun email sending test? (y/n): ").strip().lower()
        if response2 == 'y':
            results['Sending'] = test_email_sending()
    
    # Summary
    print_section("Test Summary")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test:20} {status}")
    
    all_passed = all(results.values())
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ All tests passed! Your email configuration is working.")
        print("   You can now deploy the application.")
    else:
        print("❌ Some tests failed. Fix the issues above before deploying.")
        print("   Check DEPLOYMENT_GUIDE.md for troubleshooting tips.")
    print(f"{'='*60}\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
