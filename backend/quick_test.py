#!/usr/bin/env python3
"""
Quick Email Diagnostics - No interaction needed
Automatically tests with hardcoded values
"""

import socket
import smtplib
import sys

def test_dns():
    print("="*60)
    print("  TEST 1: DNS Resolution")
    print("="*60)
    try:
        ip = socket.gethostbyname('smtp.gmail.com')
        print(f"✅ SUCCESS: smtp.gmail.com resolved to {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ FAILED: Cannot resolve smtp.gmail.com")
        print(f"   Error: {e}")
        print(f"   This means your network cannot reach Gmail servers")
        return False

def test_smtp_connection():
    print("\n" + "="*60)
    print("  TEST 2: SMTP Connection")
    print("="*60)
    try:
        print("Connecting to smtp.gmail.com:587...")
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        print("✅ Connected to SMTP server")
        
        print("Sending EHLO...")
        server.ehlo()
        print("✅ EHLO successful")
        
        print("Starting TLS...")
        server.starttls()
        print("✅ TLS started")
        
        server.quit()
        print("✅ Connection test PASSED")
        return True
    except socket.timeout:
        print(f"❌ FAILED: Connection timeout after 15 seconds")
        print(f"   Firewall is likely blocking port 587")
        return False
    except socket.gaierror as e:
        print(f"❌ FAILED: DNS error - {e}")
        return False
    except ConnectionRefusedError:
        print(f"❌ FAILED: Connection refused")
        print(f"   Port 587 is blocked or unreachable")
        return False
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return False

def test_gmail_auth():
    print("\n" + "="*60)
    print("  TEST 3: Gmail Authentication")
    print("="*60)
    
    email = "ujjwal3rd@gmail.com"
    password = "uupocbnipisbtnia"
    
    print(f"Testing login for: {email}")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        print("Authenticating...")
        server.login(email, password)
        print("✅ Authentication PASSED")
        
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ FAILED: Authentication error")
        print(f"   1. Check email is correct: {email}")
        print(f"   2. Check app password is correct (NOT regular password)")
        print(f"   3. Verify 2-Step Verification is enabled")
        print(f"   Error: {e}")
        return False
    except socket.timeout:
        print(f"❌ FAILED: Connection timeout (firewall blocking port 587)")
        return False
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  MonitorMail Email Diagnostics")
    print("="*60 + "\n")
    
    results = {}
    results['DNS'] = test_dns()
    results['SMTP'] = test_smtp_connection()
    results['Gmail'] = test_gmail_auth()
    
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test:20} {status}")
    print("="*60 + "\n")
    
    if all(results.values()):
        print("✅ All tests passed! Email should work.")
    else:
        print("❌ Some tests failed. See above for solutions.")
        if not results['DNS']:
            print("\n🔧 FIX: Check your internet connection or DNS settings")
        if not results['SMTP']:
            print("\n🔧 FIX: Check if firewall is blocking port 587")
            print("   - Windows Firewall may need to be configured")
            print("   - Corporate firewall may block SMTP")
            print("   - ISP may block SMTP on consumer connections")
        if not results['Gmail']:
            print("\n🔧 FIX: Use correct app password from Google Account")
            print("   - Go to: https://myaccount.google.com/security")
            print("   - Create new app password for Mail/Windows")
            print("   - Use that password (not your regular password)")

if __name__ == '__main__':
    main()
