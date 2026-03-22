import smtplib

EMAIL = "ujjwal3rd@gmail.com"
PASSWORD = "watptalyceqyfqcd"

try:
    print("Connecting...")
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    
    print("Starting TLS...")
    server.starttls()
    
    print("Logging in...")
    server.login(EMAIL, PASSWORD)
    
    print("✅ SUCCESS: SMTP working")
    
    server.quit()

except Exception as e:
    print("❌ ERROR:", e)