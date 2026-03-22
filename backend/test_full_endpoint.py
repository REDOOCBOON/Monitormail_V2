#!/usr/bin/env python3
"""
Complete test of the /api/send-emails endpoint with proper authentication
"""

import os
import sys
import json
import jwt
from datetime import datetime, timedelta, timezone
from flask import Flask
from werkzeug.test import Client
from werkzeug.serving import WSGIRequestHandler
import logging

# Suppress verbose logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Change to backend directory to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app as flask_app
    print("✅ Flask app imported successfully")
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

def test_send_emails_endpoint():
    """Test the send-emails endpoint with proper JWT token"""
    
    print("\n" + "="*70)
    print("  FULL ENDPOINT TEST: /api/send-emails")
    print("="*70)
    
    # Create a test client
    client = flask_app.test_client()
    
    # Generate a valid JWT token for testing
    secret_key = flask_app.config['SECRET_KEY']
    now = datetime.now(timezone.utc)
    token = jwt.encode({
        'id': 1,
        'user': 'ujjwal3rd@gmail.com',
        'name': 'Test User',
        'is_admin': True,
        'iat': now,
        'nbf': now,
        'exp': now + timedelta(hours=24)
    }, secret_key, algorithm="HS256")
    
    # Prepare email payload
    email_payload = {
        "email_data": [
            {
                "reg_no": "RA1234567890123",
                "name": "Test Student",
                "student_email": "ujjwal3rd@gmail.com",
                "parent_email": None,
                "subject": "Test Email from Endpoint",
                "email_body": "This is a test email from MonitorMail endpoint"
            }
        ],
        "sender_email": "ujjwal3rd@gmail.com",
        "sender_password": "ajps ucvj ohto wndw"
    }
    
    # Prepare request
    data = {
        'email_payload': json.dumps(email_payload)
    }
    
    headers = {
        'x-access-token': token
    }
    
    print(f"\nTesting with:")
    print(f"  ✓ Valid JWT token")
    print(f"  ✓ Email: ujjwal3rd@gmail.com")
    print(f"  ✓ App Password: ajps ucvj ohto wndw")
    print(f"  ✓ Recipient: ujjwal3rd@gmail.com")
    
    print(f"\nSending request to /api/send-emails...")
    
    try:
        response = client.post(
            '/api/send-emails',
            data=data,
            headers=headers
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        try:
            response_data = response.get_json()
            print(f"Response Body:")
            print(json.dumps(response_data, indent=2))
            
            if response.status_code == 200 and response_data.get('success'):
                print(f"\n✅ SUCCESS! Emails sent successfully")
                return True
            else:
                error = response_data.get('error', 'Unknown error')
                print(f"\n❌ FAILED: {error}")
                return False
        except:
            print(f"Raw Response: {response.data.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  MONITORMAIL ENDPOINT INTEGRATION TEST")
    print("="*70)
    
    success = test_send_emails_endpoint()
    
    print("\n" + "="*70)
    if success:
        print("✅ ALL TESTS PASSED - Email endpoint is working!")
        print("="*70)
        sys.exit(0)
    else:
        print("❌ TEST FAILED - Check error messages above")
        print("="*70)
        sys.exit(1)
