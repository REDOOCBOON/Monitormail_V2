#!/usr/bin/env python3
"""
Test the actual /api/send-emails endpoint to see what error it returns
"""

import requests
import json

# Backend URL
API_URL = "http://localhost:5000"

# Test data
email_payload = {
    "email_data": [
        {
            "reg_no": "RA1234567890123",
            "name": "Test Student",
            "student_email": "ujjwal3rd@gmail.com",
            "parent_email": None,
            "subject": "Test Email",
            "email_body": "This is a test email from MonitorMail"
        }
    ],
    "sender_email": "ujjwal3rd@gmail.com",
    "sender_password": "ajps ucvj ohto wndw"
}

# Dummy JWT token (since we need to be "authenticated")
# In real app, you'd get this from login endpoint
dummy_token = "test-token-placeholder"

def send_test_email():
    """Test the send-emails endpoint"""
    print("="*60)
    print("  Testing /api/send-emails endpoint")
    print("="*60)
    
    # Prepare request as FormData (like frontend does)
    files = {
        'email_payload': (None, json.dumps(email_payload))
    }
    
    headers = {
        'x-access-token': dummy_token
    }
    
    print(f"\nSending email payload...")
    print(f"Endpoint: {API_URL}/api/send-emails")
    print(f"Sender: {email_payload['sender_email']}")
    print(f"Password length: {len(email_payload['sender_password'])} chars")
    
    try:
        response = requests.post(
            f"{API_URL}/api/send-emails",
            files=files,
            headers=headers,
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("\n✅ Email sent successfully!")
            else:
                print(f"\n❌ Failed: {result.get('error')}")
        else:
            print(f"\n❌ Error ({response.status_code})")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {API_URL}")
        print(f"   Make sure Flask app is running: python app.py")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == '__main__':
    send_test_email()
