import flask
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
import psycopg2
import pandas as pd
import pdfplumber
import re
from io import StringIO, BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json
from functools import wraps
import os
import csv
import secrets
# tabula is no longer needed

import threading
import time
import uuid
import imaplib
import email
from email.header import decode_header

# --- Configuration ---
# Use a strong secret key via environment variable; fallback to a secure random value for dev.
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)

# Restrict CORS to a trusted frontend origin (set FRONTEND_ORIGIN in your environment).
# If you deploy the frontend and backend on different domains, set FRONTEND_ORIGIN to the frontend URL.
# For quick testing, set it to '*' to allow all origins, but for production, set it to your specific frontend URL.
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', '*')

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DB_CONFIG = DATABASE_URL
else:
    DB_CONFIG = {
        'dbname': 'students_details',
        'user': 'postgres',
        'password': 'password123',
        'host': 'localhost',
        'port': '5432'
    }

# --- App Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Use a wide-open CORS policy when FRONTEND_ORIGIN is set to '*'.
# Otherwise, restrict to the exact frontend origin.
if FRONTEND_ORIGIN == '*':
    CORS(app, origins='*', supports_credentials=True)
else:
    CORS(app, origins=[FRONTEND_ORIGIN], supports_credentials=True)

# --- Rate limiting helpers (simple in-memory, per-IP login limits) ---
_login_attempts = {}  # ip -> [timestamp, ...]
LOGIN_ATTEMPT_WINDOW = 15 * 60  # seconds
MAX_LOGIN_ATTEMPTS = 5


def _cleanup_login_attempts():
    now = time.time()
    for ip in list(_login_attempts.keys()):
        _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < LOGIN_ATTEMPT_WINDOW]
        if not _login_attempts[ip]:
            del _login_attempts[ip]


def _record_login_attempt(ip: str):
    _cleanup_login_attempts()
    _login_attempts.setdefault(ip, []).append(time.time())


def _is_rate_limited(ip: str) -> bool:
    _cleanup_login_attempts()
    attempts = _login_attempts.get(ip, [])
    return len(attempts) >= MAX_LOGIN_ATTEMPTS


# --- Security headers ---
@app.after_request
def set_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=()'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    return response

# --- Configuration ---
# Use a strong secret key via environment variable; fallback to a secure random value for dev.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)

# Restrict CORS to a trusted frontend origin (set FRONTEND_ORIGIN in your environment).
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:3000')

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DB_CONFIG = DATABASE_URL 
else:
    DB_CONFIG = {
        'dbname': 'students_details',
        'user': 'postgres',
        'password': 'password123',
        'host': 'localhost',
        'port': '5432'
    }

# --- DB Connection Helper ---
def get_db_connection():
    if isinstance(DB_CONFIG, str): 
        conn = psycopg2.connect(DB_CONFIG)
    else: 
        conn = psycopg2.connect(**DB_CONFIG)
    return conn
def ensure_admin_exists():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM teachers")
        count = cursor.fetchone()[0]

        if count == 0:
            admin_password = generate_password_hash("admin123", method='pbkdf2:sha256')

            cursor.execute(
                "INSERT INTO teachers (name, email, password_hash, is_admin) VALUES (%s,%s,%s,%s)",
                ("Admin", "admin@gmail.com", admin_password, True)
            )

            conn.commit()
            print("Default admin created: admin@gmail.com / admin123")

        cursor.close()
        conn.close()

    except Exception as e:
        print("Admin creation error:", e)

# --- DB Helper for Analytics (Unchanged) ---
def update_dashboard_analytics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM history WHERE sent_at >= CURRENT_DATE;")
        emails_today = cursor.fetchone()[0]
        cursor.execute("SELECT count(DISTINCT student_reg_no) FROM history WHERE sent_at >= CURRENT_DATE;")
        unique_students = cursor.fetchone()[0]
        cursor.execute("SELECT subject FROM history WHERE subject IS NOT NULL GROUP BY subject ORDER BY count(*) DESC LIMIT 1;")
        most_frequent = cursor.fetchone()
        most_frequent_subject = most_frequent[0] if most_frequent else 'N/A'
 
        cursor.execute(
            "UPDATE dashboard_analytics SET emails_sent_today = %s, unique_students_contacted = %s, most_frequent_subject = %s, last_updated = NOW() WHERE id = 1;",
            (emails_today, unique_students, most_frequent_subject)
        )
        conn.commit()
        cursor.close()
  
        conn.close()
    except Exception as e:
        print(f"Error updating analytics: {e}")

# --- Email Monitoring (Phase 1: Simple IMAP-based rule matching) ---
monitor_lock = threading.Lock()
monitors = {}  # monitor_id -> monitor config
monitor_matches = {}  # monitor_id -> list of match events


def _decode_header_value(value):
    if not value:
        return ''
    decoded_parts = decode_header(value)
    result = ''
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            try:
                result += part.decode(encoding or 'utf-8', errors='ignore')
            except Exception:
                result += part.decode('utf-8', errors='ignore')
        else:
            result += part
    return result


def _extract_email_snippet(msg):
    # Try to get a short snippet from the email body
    snippet = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and not part.get('Content-Disposition'):
                try:
                    snippet = part.get_payload(decode=True).decode(errors='ignore')
                    break
                except Exception:
                    continue
    else:
        try:
            snippet = msg.get_payload(decode=True).decode(errors='ignore')
        except Exception:
            snippet = ''
    return (snippet or '').strip().replace('\r', '').replace('\n', ' ')[:250]


def _run_monitor_once(monitor):
    # Monitor structure: {id, name, imap_host, imap_port, username, password, folder, subject_contains, interval_seconds, last_checked, seen_uids}
    try:
        imap_host = monitor.get('imap_host')
        imap_port = int(monitor.get('imap_port', 993))
        username = monitor.get('username')
        password = monitor.get('password')
        folder = monitor.get('folder') or 'INBOX'
        subject_filter = (monitor.get('subject_contains') or '').strip().lower()

        if not imap_host or not username or not password or not subject_filter:
            return

        mail = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=30)
        mail.login(username, password)
        mail.select(folder)

        # Search for unseen messages
        res, data = mail.search(None, 'UNSEEN')
        if res != 'OK':
            mail.logout()
            return

        uids = data[0].split() if data and data[0] else []
        new_uids = []
        seen_uids = monitor.setdefault('seen_uids', set())
        for uid in uids:
            if uid in seen_uids:
                continue
            new_uids.append(uid)

        if not new_uids:
            mail.logout()
            return

        for uid in new_uids:
            res, msg_data = mail.fetch(uid, '(RFC822)')
            if res != 'OK' or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            try:
                msg = email.message_from_bytes(raw)
            except Exception:
                continue
            subj = _decode_header_value(msg.get('Subject'))
            sender = _decode_header_value(msg.get('From'))
            snippet = _extract_email_snippet(msg)
            match = False
            if subject_filter in (subj or '').lower() or subject_filter in (snippet or '').lower():
                match = True
            if match:
                event = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'subject': subj,
                    'from': sender,
                    'snippet': snippet,
                    'uid': uid.decode() if isinstance(uid, bytes) else str(uid)
                }
                with monitor_lock:
                    monitor_matches.setdefault(monitor['id'], []).append(event)
            seen_uids.add(uid)

        mail.logout()
    except Exception as e:
        # Log, but do not raise to keep the background thread running
        print(f"Monitor error (id={monitor.get('id')}): {e}")


def _monitor_loop():
    while True:
        now = time.time()
        with monitor_lock:
            monitors_list = list(monitors.values())
        for monitor in monitors_list:
            interval = int(monitor.get('interval_seconds', 60))
            last_checked = monitor.get('last_checked', 0)
            if now - last_checked >= interval:
                monitor['last_checked'] = now
                _run_monitor_once(monitor)
        time.sleep(5)


def _ensure_monitor_thread():
    if not hasattr(app, '_monitor_thread_started'):
        thread = threading.Thread(target=_monitor_loop, daemon=True)
        thread.start()
        app._monitor_thread_started = True

# --- Authentication Decorators (Unchanged) ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            g.current_user = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=["HS256"],
                options={'require': ['exp', 'iat']}
            )
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=["HS256"],
                options={'require': ['exp', 'iat']}
            )
            if not data.get('is_admin'):
                return jsonify({'message': 'Admin privileges required!'}), 403
            g.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# --- PDF Processing Logic (Original for Low Attendance Workflow) ---
def process_pdf_to_csv_string(pdf_file):
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    pattern = re.compile(r'(RA\w{13})([\s\S]*?)(?=RA\w{13}|S\.No|Total Students|\Z)') 
    student_blocks = pattern.findall(full_text)
    csv_output = StringIO()
    csv_output.write("Reg.No,Subject,Percentage\n")
    for reg_no, content in student_blocks:
        subjects_pattern = re.compile(r'\b(\d{2}[A-Z]{3,}\d{3,}[A-Z]?(?:\s?\([A-Z0-9]\))?)\b')
        percentages_pattern = re.compile(r'\b(\d{1,3}[,.]\d{2})\b')
        subjects = subjects_pattern.findall(content)
        potential_percentages = percentages_pattern.findall(content)
        limit = min(len(subjects), len(potential_percentages))
        
     
        for i in range(limit):
            subject = " ".join(subjects[i].replace('\n', ' ').split()).strip()
            percentage = potential_percentages[i].replace(',', '.').strip()
            try:
                if 0 <= float(percentage) <= 100:
      
                    csv_output.write(f'"{reg_no.strip()}","{subject}","{percentage}"\n')
            except ValueError:
                continue 
    return csv_output.getvalue()

# --- API Endpoints ---

@app.route('/api/auth/login', methods=['POST'])
def login():
    auth = request.authorization
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if _is_rate_limited(ip):
        return jsonify({'message': 'Too many login attempts. Please try again later.'}), 429

    if not auth or not auth.username or not auth.password:
        _record_login_attempt(ip)
        return jsonify({'message': 'Could not verify'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, name, is_admin FROM teachers WHERE email = %s", (auth.username,))
        teacher = cursor.fetchone()
        cursor.close()
        conn.close()

        if not teacher:
            _record_login_attempt(ip)
            return jsonify({'message': 'User not found'}), 401

        if check_password_hash(teacher[2], auth.password):
            # Reset attempts on successful login
            if ip in _login_attempts:
                del _login_attempts[ip]

            now = datetime.now(timezone.utc)
            token = jwt.encode({
                'id': teacher[0],
                'user': teacher[1],
                'name': teacher[3],
                'is_admin': teacher[4],
                'iat': now,
                'nbf': now,
                'exp': now + timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({
                'token': token,
                'user': {'id': teacher[0], 'email': teacher[1], 'name': teacher[3], 'is_admin': teacher[4]}
            })

        _record_login_attempt(ip)
        return jsonify({'message': 'Incorrect password'}), 401
    except Exception as e:
        return jsonify({'message': f'Database connection error: {e}'}), 500

@app.route('/api/upload-pdf', methods=['POST'])
@token_required
def upload_pdf():
    file = request.files.get('file')
    if not file: return jsonify({'error': 'No file part'}), 400
    try:
        csv_data = process_pdf_to_csv_string(file)
   
        return jsonify({'csv_data': csv_data})
    except Exception as e:
        return jsonify({'error': f'Failed to process PDF: {e}'}), 500

@app.route('/api/sort-attendance', methods=['POST'])
@token_required
def sort_attendance():
    csv_data = request.get_json().get('csv_data', '')
    try:
        df = pd.read_csv(StringIO(csv_data))
        df['Percentage'] = pd.to_numeric(df['Percentage'], errors='coerce')
      
        df.dropna(subset=['Percentage'], inplace=True) 
        low_attendance_df = df[df['Percentage'] < 75] 
        return jsonify({'sorted_csv_data': low_attendance_df.to_csv(index=False)})
    except Exception as e:
        return jsonify({'error': f'Failed to sort data: {e}'}), 500

@app.route('/api/fetch-details', methods=['POST'])
@token_required
def fetch_details():
    sorted_csv = request.get_json().get('sorted_csv_data', '')
    conn = None 
    try:
        df = pd.read_csv(StringIO(sorted_csv))
        reg_nos = df['Reg.No'].unique().tolist()
        if not reg_nos: return jsonify([])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        query = 'SELECT "Reg.No", name, email, parent_email FROM students WHERE "Reg.No" IN %s'
        cursor.execute(query, (tuple(reg_nos),))
        student_details = cursor.fetchall()
        cursor.close()
        conn.close() 

        details_map = {row[0]: {'name': row[1], 'student_email': row[2], 'parent_email': row[3]} for row in student_details}
        grouped_subjects = df.groupby('Reg.No')[['Subject', 'Percentage']].apply(lambda x: x.to_dict('records')).reset_index(name='subjects')
        
        merged_data = []
        for _, row in grouped_subjects.iterrows():
            reg_no = row['Reg.No']
            details = details_map.get(reg_no)
            if details:
                merged_data.append({
                    'reg_no': reg_no,
                    'name': details.get('name'),
                    'student_email': details.get('student_email'),
                    'parent_email': details.get('parent_email'),
                    'subjects': row['subjects'],
                    'missing': False
                })
            else:
                # Student not found in DB; allow frontend to collect details
                merged_data.append({
                    'reg_no': reg_no,
                    'name': '',
                    'student_email': '',
                    'parent_email': '',
                    'subjects': row['subjects'],
                    'missing': True
                })
        return jsonify(merged_data)
    except Exception as e:
         if conn: 
            conn.close()
         print(f"Error details in fetch_details: {e}") 
         return jsonify({'error': f'Database fetch failed: {e}'}), 500

@app.route('/api/send-emails', methods=['POST'])
@token_required
def send_emails_endpoint():
   
    conn = None 
    try:
        email_payload_str = request.form.get('email_payload')
        if not email_payload_str:
            return jsonify({'success': False, 'reason': 'Email payload is missing.'}), 400
        
        data = json.loads(email_payload_str)
        attachment = request.files.get('attachment')
 
        
        email_data = data.get('email_data')
        sender_email = data.get('sender_email')
        sender_password = data.get('sender_password')
        teacher_email = g.current_user['user']

        attachment_payload = None
        attachment_filename = None
        if attachment:
 
            attachment_filename = attachment.filename
            attachment_payload = attachment.read()

        def clean_email(email_str):
            if not email_str or not isinstance(email_str, str): return None
            if '@' in email_str and '.' in email_str.split('@')[-1]: 
 
                return email_str.strip() 
            return None

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
        server.login(sender_email, sender_password)
        results = []
        conn = get_db_connection()
        
        for student in email_data:
            if not isinstance(student, dict) or 'reg_no' not in student:
                results.append({'reg_no': 'Unknown', 'status': 'failed', 'reason': 'Invalid student data format.'})
             
                continue
            
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
              
                msg['Subject'] = student.get('subject', "Important: Attendance Notification") 
                
                recipients = []
                student_email = clean_email(student.get('student_email'))
                if student_email: recipients.append(student_email)
                
                parent_email = clean_email(student.get('parent_email'))
                if parent_email and parent_email not in recipients: recipients.append(parent_email)
                
   
                if student_email:
                    msg['To'] = student_email
                    if parent_email:
                    
                        msg['Cc'] = parent_email
                elif parent_email: 
                     msg['To'] = parent_email
                else: 
             
                    results.append({'reg_no': student['reg_no'], 'status': 'failed', 'reason': 'No valid recipient emails found.'})
                    continue

                email_body_html = student.get('email_body', '').replace('\n', '<br>')
                msg.attach(MIMEText(email_body_html, 'html'))

    
                if attachment_payload and attachment_filename:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment_payload) 
                  
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
                    msg.attach(part)

                server.sendmail(sender_email, recipients, msg.as_string())
               
                results.append({'reg_no': student['reg_no'], 'status': 'success'})

                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO history (student_reg_no, student_name, subject, body, recipients, teacher_email) VALUES (%s, %s, %s, %s, %s, %s)",
                        (student['reg_no'], student.get('name'), msg['Subject'], student.get('email_body', ''), ", ".join(recipients), teacher_email)
                    )
                conn.commit()

     
            except Exception as e:
                print("EMAIL ERROR:", str(e))
                conn.rollback() 
                results.append({'reg_no': student['reg_no'], 'status': 'failed', 'reason': str(e)})
        
        server.quit()
        conn.close()
     
        update_dashboard_analytics()
        return jsonify({'success': True, 'results': results})
    except smtplib.SMTPAuthenticationError:
        if conn: conn.close()
        return jsonify({'success': False, 'reason': 'Gmail authentication failed. Check email/App Password.'}), 401
    except Exception as e:
        if conn: conn.close() 
        return jsonify({'success': False, 'reason': str(e)}), 500

@app.route('/api/alert-all', methods=['POST'])
@token_required
def alert_all_students():
    conn = None
    try:
        alert_payload_str = request.form.get('alert_payload')
        if not alert_payload_str:
            return jsonify({'success': False, 'reason': 'Alert payload is missing.'}), 400
        
       
        data = json.loads(alert_payload_str)
        attachment = request.files.get('attachment')
        
        sender_email = data.get('sender_email')
        sender_password = data.get('sender_password')
        subject = data.get('subject', 'Important Notification')
        email_body = data.get('email_body', '')
        teacher_email = g.current_user['user']

   
        attachment_payload = None
        attachment_filename = None
        if attachment:
            attachment_filename = attachment.filename
            attachment_payload = attachment.read()

        def clean_email(email_str):
            if not email_str or not isinstance(email_str, str): return None
            if '@' in email_str and '.' in email_str.split('@')[-1]: 
                return email_str.strip() 
            return None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT "Reg.No", name, email, parent_email FROM students')
        all_students = cursor.fetchall()
        
        if not all_students:
            cursor.close()
            conn.close()
           
            return jsonify({'success': False, 'reason': 'No students found in database.'}), 404

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
        server.login(sender_email, sender_password)
        results = {'success_count': 0, 'fail_count': 0, 'failed_regs': []}
        
        for student in all_students:
     
            reg_no, name, student_email, parent_email = student
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['Subject'] = subject
                
                recipients = []
                s_email = clean_email(student_email)
                p_email = clean_email(parent_email)
      
                if s_email: recipients.append(s_email)
                if p_email and p_email not in recipients: recipients.append(p_email)
                
                if s_email:
         
                    msg['To'] = s_email
                    if p_email: msg['Cc'] = p_email
                elif p_email: 
                     msg['To'] = p_email
                else: 
                    results['fail_count'] += 1
                    results['failed_regs'].append(reg_no)
                 
                    continue

                body_personalized = email_body.replace('[Student Name]', name or 'Student')
                email_body_html = body_personalized.replace('\n', '<br>')
                msg.attach(MIMEText(email_body_html, 'html'))

                
                if attachment_payload and attachment_filename:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment_payload) 
                    encoders.encode_base64(part)
          
                    part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
                    msg.attach(part)

                server.sendmail(sender_email, recipients, msg.as_string())
                results['success_count'] += 1

         
                with get_db_connection() as log_conn:
                    with log_conn.cursor() as log_cursor:
                        log_cursor.execute(
                    
                            "INSERT INTO history (student_reg_no, student_name, subject, body, recipients, teacher_email) VALUES (%s, %s, %s, %s, %s, %s)",
                            (reg_no, name, subject, email_body, ", ".join(recipients), teacher_email)
                    
                        )
                        log_conn.commit()

            except Exception as e:
                print("EMAIL ERROR:", str(e))
                results['fail_count'] += 1
                
                results['failed_regs'].append(reg_no)
        
        server.quit()
        cursor.close()
        conn.close()
        update_dashboard_analytics()
        return jsonify({'success': True, 'results': results})
        
    except smtplib.SMTPAuthenticationError:
        if conn: conn.close()
  
        return jsonify({'success': False, 'reason': 'Gmail authentication failed. Check email/App Password.'}), 401
    except Exception as e:
        if conn: conn.close() 
        return jsonify({'success': False, 'reason': str(e)}), 500

@app.route('/api/dashboard-analytics', methods=['GET'])
@token_required
def get_dashboard_analytics():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emails_sent_today, unique_students_contacted, most_frequent_subject FROM dashboard_analytics WHERE id = 1")
        analytics = cursor.fetchone()
        cursor.execute("SELECT student_name, student_reg_no, count(*) as email_count FROM history GROUP BY student_name, student_reg_no ORDER BY email_count DESC LIMIT 5;")
        top_students = [{'name': row[0], 'reg_no': row[1], 'count': row[2]} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        if analytics:
            return jsonify({
                'emails_sent_today': analytics[0],
                'unique_students_contacted': analytics[1],
 
                'most_frequent_subject': analytics[2],
                'top_students': top_students
            })
        return jsonify({'error': 'Analytics data not found'}), 404
    except Exception as e:
        if conn: conn.close()
 
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers', methods=['GET'])
@admin_required
def get_teachers():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, is_admin FROM teachers ORDER BY name")
        teachers = [{'id': row[0], 'name': row[1], 'email': row[2], 'is_admin': row[3]} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(teachers)
    except Exception as e:
        if conn: conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers', methods=['POST'])
@admin_required
def create_teacher():
    conn = None
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        is_admin = data.get('is_admin', False)

        if not name or not email or not password:
            return jsonify({'message': 'Missing data'}), 400

        # FIX: use Werkzeug default hash (scrypt)
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO teachers (name, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, is_admin)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Teacher created successfully'}), 201

    except psycopg2.errors.UniqueViolation:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'message': 'Email already exists'}), 409

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'message': str(e)}), 500


@app.route('/api/teachers/<int:teacher_id>', methods=['PUT'])
@admin_required
def update_teacher(teacher_id):
    conn = None
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        is_admin = data.get('is_admin')
        password = data.get('password')
        if not name or not email or is_admin is None:
            return jsonify({'message': 'Missing required fields'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        if password:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute("UPDATE teachers SET name = %s, email = %s, is_admin = %s, password_hash = %s WHERE id = %s",(name, email, is_admin, hashed_password, teacher_id))
        else:
            cursor.execute("UPDATE teachers SET name = %s, email = %s, is_admin = %s WHERE id = %s",(name, email, is_admin, teacher_id))
    
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Teacher updated successfully'})
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers/<int:teacher_id>', methods=['DELETE'])
@admin_required
def delete_teacher(teacher_id):
    conn = None
    try:
        if teacher_id == g.current_user.get('id'):
            return jsonify({'message': 'Admin cannot delete their own account'}), 403
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
       
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Teacher deleted successfully'})
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500

# --- STUDENT MANAGEMENT ENDPOINTS (with "batch" removed) ---
@app.route('/api/students', methods=['GET'])
@token_required
def get_students():
    search_query = request.args.get('search', '')
  
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # --- FIX: Removed 'batch' from query ---
        cursor.execute(
            'SELECT id, "Reg.No", name, section, department, phone_number, email, parent_mobile, parent_email FROM students WHERE "Reg.No" ILIKE %s OR name ILIKE %s ORDER BY name', 
            ('%' + search_query + '%', '%' + search_query + '%')
        )
        students = [{'id': r[0],'reg_no': r[1],'name': r[2],'section': r[3],'department': r[4],'phone_number': r[5],'email': r[6],'parent_mobile': r[7],'parent_email': r[8]} for r in cursor.fetchall()]
        cursor.close()
        
        conn.close()
        return jsonify(students)
    except Exception as e:
        if conn: conn.close() 
        print(f"Error details in get_students: {e}") 
        return jsonify({'error': f'Database fetch failed: {e}'}), 500

@app.route('/api/students', methods=['POST'])
@token_required 
def create_student():
    data = request.get_json()
    conn = None
    try:
    
        conn = get_db_connection()
        cursor = conn.cursor()
        # --- FIX: Removed 'batch' from query ---
        cursor.execute(
            'INSERT INTO students ("Reg.No", name, section, department, phone_number, email, parent_mobile, parent_email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
     
            (data['reg_no'], data['name'], data['section'], data['department'], data['phone_number'], data['email'], data['parent_mobile'], data['parent_email'])
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Student created successfully', 'id': new_id}), 201
    except psycopg2.errors.UniqueViolation:
 
        if conn: conn.rollback(); conn.close()
        return jsonify({'message': 'Registration number already exists'}), 409
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
@token_required 
def update_student(student_id):
    conn = None
    try:
        data = request.get_json()
 
        conn = get_db_connection()
        cursor = conn.cursor()
        # --- FIX: Removed 'batch' from query ---
        cursor.execute(
            'UPDATE students SET "Reg.No" = %s, name = %s, section = %s, department = %s, phone_number = %s, email = %s, parent_mobile = %s, parent_email = %s WHERE id = %s',
            (data['reg_no'], data['name'], data['section'], data['department'], data['phone_number'], data['email'], data['parent_mobile'], data['parent_email'], student_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Student updated successfully'})
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@token_required 
def delete_student(student_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
      
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Student deleted successfully'})
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500


# --- Templates and History endpoints (Unchanged) ---
@app.route('/api/templates', methods=['GET'])
@token_required
def get_templates():
 
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, body FROM templates ORDER BY name")
        templates = [{'id': row[0], 'name': row[1], 'body': row[2]} for row in cursor.fetchall()]
        cursor.close()
     
        conn.close()
        return jsonify(templates)
    except Exception as e:
        if conn: conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates', methods=['POST'])
@token_required
def create_template():
    conn = None
    try:
        data = request.get_json()
       
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO templates (name, body) VALUES (%s, %s) RETURNING id, name, body", (data['name'], data['body']))
        new_template = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'id': new_template[0], 'name': new_template[1], 'body': new_template[2]}), 201
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/<int:template_id>', methods=['PUT'])
@token_required
def update_template(template_id):
    conn = None
    try:
        data = request.get_json()
        conn = get_db_connection()
  
        cursor = conn.cursor()
        cursor.execute("UPDATE templates SET name = %s, body = %s WHERE id = %s", (data['name'], data['body'], template_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Template updated successfully'})
    except Exception as e:
   
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
@token_required
def delete_template(template_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM templates WHERE id = %s", (template_id,))
   
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Template deleted successfully'})
    except Exception as e:
        if conn: conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
@token_required
def get_history():
    search_query = request.args.get('search', '')
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = 'SELECT id, student_reg_no, student_name, subject, body, recipients, sent_at, teacher_email FROM history WHERE student_reg_no ILIKE %s OR student_name ILIKE %s ORDER BY sent_at DESC'
        search_term = '%' + search_query + '%'
        cursor.execute(sql, (search_term, search_term))
        history_logs = [{'id': r[0],'student_reg_no': r[1],'student_name': r[2],'subject': r[3],'body': r[4],'recipients': r[5],'sent_at': r[6].isoformat(),'teacher_email': r[7]} for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(history_logs)
    except Exception as e:
        if conn: conn.close()
  
        return jsonify({'error': str(e)}), 500


# --- Email Monitor Endpoints (Phase 1 MVP) ---
@app.route('/api/monitors', methods=['GET'])
@token_required
def list_monitors():
    _ensure_monitor_thread()
    with monitor_lock:
        return jsonify([{
            'id': m['id'],
            'name': m.get('name'),
            'imap_host': m.get('imap_host'),
            'imap_port': m.get('imap_port'),
            'username': m.get('username'),
            'folder': m.get('folder'),
            'subject_contains': m.get('subject_contains'),
            'interval_seconds': m.get('interval_seconds'),
            'last_checked': m.get('last_checked')
        } for m in monitors.values()])

@app.route('/api/monitors', methods=['POST'])
@token_required
def create_monitor():
    payload = request.get_json() or {}
    name = payload.get('name', '').strip() or 'Unnamed Monitor'
    imap_host = payload.get('imap_host', '').strip()
    imap_port = payload.get('imap_port', 993)
    username = payload.get('username', '').strip()
    password = payload.get('password', '')
    folder = payload.get('folder', 'INBOX').strip() or 'INBOX'
    subject_contains = payload.get('subject_contains', '').strip()
    interval_seconds = int(payload.get('interval_seconds', 60))

    if not imap_host or not username or not password or not subject_contains:
        return jsonify({'message': 'imap_host, username, password, and subject_contains are required.'}), 400

    monitor_id = str(uuid.uuid4())
    monitor = {
        'id': monitor_id,
        'name': name,
        'imap_host': imap_host,
        'imap_port': imap_port,
        'username': username,
        'password': password,
        'folder': folder,
        'subject_contains': subject_contains,
        'interval_seconds': interval_seconds,
        'last_checked': 0,
        'seen_uids': set()
    }
    with monitor_lock:
        monitors[monitor_id] = monitor
        monitor_matches.setdefault(monitor_id, [])

    _ensure_monitor_thread()
    return jsonify({'id': monitor_id, 'name': name}), 201

@app.route('/api/monitors/<monitor_id>', methods=['DELETE'])
@token_required
def delete_monitor(monitor_id):
    with monitor_lock:
        if monitor_id in monitors:
            monitors.pop(monitor_id, None)
            monitor_matches.pop(monitor_id, None)
            return jsonify({'message': 'Monitor deleted.'})
    return jsonify({'message': 'Monitor not found.'}), 404

@app.route('/api/monitors/<monitor_id>/matches', methods=['GET'])
@token_required
def get_monitor_matches(monitor_id):
    with monitor_lock:
        matches = monitor_matches.get(monitor_id, [])
    return jsonify(matches)


@app.route('/api/export-excel-structured', methods=['POST'])
@token_required
def export_excel_structured():
    sorted_csv = request.get_json().get('sorted_csv_data', '')
    try:
        df = pd.read_csv(StringIO(sorted_csv))
        pivot_df = df.pivot_table(index='Reg.No', columns='Subject', values='Percentage').reset_index()
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
   
            pivot_df.to_excel(writer, index=False, sheet_name='Low_Attendance_Pivot')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name='Structured_Attendance_Report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({'error': f'Excel export failed: {e}'}), 500
        
if __name__ == '__main__':
    ensure_admin_exists()

    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug_mode)
