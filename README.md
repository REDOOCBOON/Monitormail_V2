# MonitorMail

MonitorMail is a lightweight student notification system that allows teachers to:

- Upload PDF attendance reports
- Parse and identify low attendance students
- Send email notifications to students and parents
- Manage students and teachers
- Monitor incoming emails via IMAP rules

---

## 🧩 Project Structure

- `backend/` - Flask API for authentication, PDF parsing, email sending, and database storage.
- `frontend/` - React (Create React App) UI for interacting with the backend.

---

## 🚀 Getting Started

### Prerequisites:
- Python 3.8+
- Node.js 14+
- PostgreSQL database (local or cloud)
- Gmail account with App Password enabled

### 1) Backend (Flask)

1. Install Python dependencies

```powershell
cd backend
python -m pip install -r requirements.txt
```

2. Configure environment variables (recommended)

Create a `.env` file or set environment variables directly:

- `SECRET_KEY` - secret key used for JWT signing (required)
- `DATABASE_URL` - optional PostgreSQL connection string (defaults to local config)
- `FRONTEND_ORIGIN` - frontend URL for CORS (defaults to `http://localhost:3000`)
- `FLASK_DEBUG` - set to `true`/`1` to enable debug mode

Example (PowerShell):

```powershell
$env:SECRET_KEY = "supersecretkey"
$env:FRONTEND_ORIGIN = "http://localhost:3000"
$env:FLASK_DEBUG = "true"
```

3. **Test Email Configuration** (before first use)

```powershell
python backend/test_email_config.py
```

This tool will:
- Test DNS resolution for SMTP server
- Test SMTP connectivity
- Verify Gmail credentials
- Send a test email to verify everything works

4. Run the backend

```powershell
python app.py
```

The API will start on `http://localhost:5000` by default.

---

### 2) Frontend (React)

1. Install node dependencies

```powershell
cd frontend
npm install
```

2. Configure API URL (optional)

Set environment variable:
```powershell
$env:REACT_APP_API_URL = "http://localhost:5000"
```

3. Run the frontend

```powershell
npm start
```

The UI should open in your browser at `http://localhost:3000` (or another port if 3000 is busy).

---

## 🔐 Security Notes

- **Always set `SECRET_KEY`** for production so JWT tokens remain valid across restarts.
- **Run behind HTTPS** to prevent token/session interception.
- Use strong passwords and consider using App Passwords for Gmail.

## 📧 Email Configuration

### Gmail Setup:
1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate an App Password for "Mail" and "Windows Computer"
3. Copy the 16-character password (without spaces)
4. Use this password in the app (NOT your regular Gmail password)

### Test Your Email Setup:
```powershell
python backend/test_email_config.py
```

### Understanding Email Errors:
- **"Network is unreachable"**: Check firewall, VPN, or ISP restrictions
- **"Authentication failed"**: Verify App Password is correct, not regular password
- **"Connection timeout"**: Check internet connection, DNS resolution

For detailed troubleshooting, see `DEPLOYMENT_GUIDE.md`

---

## 🧪 Usage

1. Open the UI and sign in using a teacher account stored in the database.
2. Upload the PDF attendance report on the “Low Attendance” tab.
3. Pick students with <75% attendance.
4. Choose or edit an email template.
5. Send notifications to students/parents.

---

## 🚀 Next Enhancements (Optional)

- Switch to cookie-based auth (HttpOnly tokens)
- Add role-based access for teachers vs admins
- Add audit logging for email sends
- Add more robust validation and rate limiting
- Use SendGrid as fallback email service

## 📱 Deployment

For complete deployment instructions to Render (backend), Vercel (frontend), and Neon (database), see:
### [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

Quick deployment checklist:
1. ✅ Test locally with `test_email_config.py`
2. ✅ Push code to GitHub
3. ✅ Connect Render to GitHub for auto-deploy
4. ✅ Set environment variables on Render
5. ✅ Create Neon PostgreSQL instance
6. ✅ Deploy frontend to Vercel
7. ✅ Update API URLs

---
