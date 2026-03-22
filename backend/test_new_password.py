#!/usr/bin/env python3
"""
Quick Email Diagnostics - Testing new app password
"""

import socket
import smtplib
import sys

def test_gmail_auth(email, password):
    print("\n" + "="*60)
    print("  TEST: Gmail Authentication with New Password")
    print("="*60)
    
    print(f"Testing login for: {email}")
    print(f"Testing with new app password...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        print("Authenticating...")
        server.login(email, password)
        print("✅ Authentication PASSED!")
        
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ FAILED: Authentication error")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return False

def test_send_email(email, password):
    print("\n" + "="*60)
    print("  TEST: Send Test Email")
    print("="*60)
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(email, password)
        
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email
        msg['Subject'] = "MonitorMail - Test Email"
        msg.attach(MIMEText("<h2>✅ Email System Working!</h2><p>Your email configuration is now set up correctly.</p>", 'html'))
        
        print(f"Sending test email to {email}...")
        server.sendmail(email, [email], msg.as_string())
        print("✅ Test email sent successfully!")
        print(f"   Check your inbox (and spam folder) for the test email")
        
        server.quit()
        return True
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return False

def main():
    email = "ujjwal3rd@gmail.com"
    password = "ajps ucvj ohto wndw"  # New app password with spaces
    
    print("\n" + "="*60)
    print("  MonitorMail - New Password Test")
    print("="*60)
    
    # Test authentication
    if test_gmail_auth(email, password):
        print("\n✅ Authentication successful with new password!")
        
        # Try sending test email
        if test_send_email(email, password):
            print("\n" + "="*60)
            print("  ✅ ALL TESTS PASSED!")
            print("="*60)
            print("\nYour email configuration is now working correctly!")
            print("You can now:")
            print("  1. Push code to GitHub")
            print("  2. Deploy to Render/Vercel")
            print("  3. Use the app to send emails reliably")
            return 0
    
    print("\n" + "="*60)
    print("  ❌ TEST FAILED")
    print("="*60)
    print("\nPossible solutions:")
    print("  1. Make sure you copied the ENTIRE password with spaces")
    print("  2. Try generating a NEW app password again")
    print("  3. Ensure 2-Step Verification is enabled")
    return 1

if __name__ == '__main__':
    sys.exit(main())
