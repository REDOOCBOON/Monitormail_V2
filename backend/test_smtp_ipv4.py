import smtplib

EMAIL = 'ujjwal3rd@gmail.com'
PASSWORD = 'watptalyceqyfqcd'

print('Testing IPv4 SMTP...')
try:
    print('Connecting to 192.178.211.108:587...')
    server = smtplib.SMTP('192.178.211.108', 587, timeout=60)
    print('Start TLS...')
    server.starttls()
    print('EHLO...')
    server.ehlo()
    print('Login...')
    server.login(EMAIL, PASSWORD)
    print('✅ SUCCESS: IPv4 SMTP working!')
    server.quit()
except Exception as e:
    print('❌ ERROR:', repr(e))
    print('Type:', type(e).__name__)

