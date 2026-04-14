#!/usr/bin/env python3
"""
Email Logs Viewer
View emails logged during development (when email service is not configured).
Run: python view_email_logs.py
"""

import os
import sys
from pathlib import Path


def view_email_logs():
    """Display all logged emails."""
    log_dir = 'email_logs'
    
    if not os.path.exists(log_dir):
        print("📁 No email logs directory found.")
        print("   Email logs are created in 'email_logs/' when you send emails locally")
        print("   without BREVO_API_KEY or GMAIL_PASSWORD configured.")
        return
    
    log_files = sorted(Path(log_dir).glob('email_*.txt'), reverse=True)
    
    if not log_files:
        print("📁 No email logs found in 'email_logs/' directory.")
        print("   Send some emails locally to generate logs.")
        return
    
    print(f"\n📧 Found {len(log_files)} logged email(s):\n")
    
    for i, log_file in enumerate(log_files, 1):
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            print(f"\n{'='*70}")
            print(f"[{i}] {log_file.name}")
            print(f"{'='*70}")
            print(content)
        except Exception as e:
            print(f"Error reading {log_file.name}: {e}")
    
    print(f"\n{'='*70}")
    print(f"✅ Viewed {len(log_files)} email log(s)")
    print("To actually send emails:")
    print("  - On Render: Change BREVO_FROM_EMAIL to your verified Brevo email")
    print("  - Local: Set BREVO_API_KEY or GMAIL_PASSWORD environment variable")


if __name__ == '__main__':
    view_email_logs()
