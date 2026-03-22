# MonitorMail - Complete Deployment Guide

## ✅ Email Sending Fixes Implemented

### Problems Fixed:
1. **errno 101 "Network is unreachable"** - SMTP connection timeout issues on production servers
2. **Retry logic** - Exponential backoff (2s, 4s, 8s) for transient network failures
3. **Socket configuration** - Proper timeout handling and socket configuration
4. **Error handling** - Detailed error messages to diagnose network, authentication, and DNS issues
5. **Production-ready** - Works on Render, Vercel, and other platforms

### Key Changes:
- **New module**: `email_util.py` - Robust EmailSender class with retry logic and comprehensive error handling
- **Updated**: `app.py` - Uses EmailSender class with proper logging
- **Both endpoints updated**:
  - `/api/send-emails` - Send emails to individual students
  - `/api/alert-all` - Send mass alerts to all students

---

## 🚀 Local Development Setup

### 1. Install Dependencies
```powershell
cd backend
python -m pip install -r requirements.txt
```

### 2. Set Environment Variables (PowerShell)
```powershell
$env:SECRET_KEY = "your-secret-key-here"
$env:DATABASE_URL = "postgresql://user:password@localhost:5432/students_details"
$env:FRONTEND_ORIGIN = "http://localhost:3000"
$env:FLASK_DEBUG = "true"
```

Or use a `.env` file (install `python-dotenv` first):
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/students_details
FRONTEND_ORIGIN=http://localhost:3000
FLASK_DEBUG=true
```

### 3. Run Backend
```powershell
python app.py
```

Server will start at `http://localhost:5000`

### 4. Run Frontend (in another terminal)
```powershell
cd frontend
npm install  # First time only
npm start
```

Frontend will start at `http://localhost:3000`

---

## 📧 Email Configuration

### Gmail App Password Setup:
1. Go to: https://myaccount.google.com/security
2. Enable "2-Step Verification" if not already enabled
3. Create an "App password" for "Mail" on "Windows Computer"
4. Copy the 16-character password
5. Use this password in the app (NOT your regular Gmail password)

### Example Email Payload:
```json
{
  "email_data": [{
    "reg_no": "RA1234567890123",
    "name": "John Doe",
    "student_email": "john@example.com",
    "parent_email": "parent@example.com",
    "subject": "Low Attendance Alert",
    "email_body": "Dear [Student Name],\n\nYour attendance is below 75%..."
  }],
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password"
}
```

---

## 🌐 Deployment to Render

### Prerequisites:
- GitHub repository with code pushed
- Neon PostgreSQL instance (free tier available)
- Render account (free tier available)

### 1. Create PostgreSQL Database on Neon
1. Sign up at https://neon.tech
2. Create a new project
3. Copy the connection string (looks like: `postgresql://user:password@...`)

### 2. Deploy Backend to Render
1. Sign up at https://render.com
2. Click "New+" > "Web Service"
3. Select GitHub repository
4. Configure:
   - **Name**: `monitormail-api-v2` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python app.py`
   - **Port**: `5000`
   
5. Set Environment Variables:
   ```
   DATABASE_URL = postgresql://[neon-connection-string]
   SECRET_KEY = [generate-strong-key]
   FRONTEND_ORIGIN = https://your-frontend-domain.com
   FLASK_DEBUG = false
   PORT = 5000
   ```

6. Click "Create Web Service"

### 3. Deploy Frontend to Vercel
1. Sign up at https://vercel.com
2. Install Vercel CLI: `npm install -g vercel`
3. In frontend directory: `vercel`
4. During setup, set:
   ```
   REACT_APP_API_URL = https://your-backend.onrender.com
   ```

5. Or set environment variables in Vercel dashboard:
   - Settings > Environment Variables
   - Add: `REACT_APP_API_URL = https://monitormail-api-v2.onrender.com`

### 4. Update Frontend API Configuration
In `frontend/src/api.js`, verify:
```javascript
const API_URL = process.env.REACT_APP_API_URL || "https://monitormail-api-v2.onrender.com";
```

---

## 🔧 Troubleshooting

### Email Sending Issues:

#### ❌ "Network is unreachable"
**Solutions**:
1. **Check firewall**: Port 587 (SMTP) must be open
2. **Check credentials**: Use Gmail App Password, NOT regular password
3. **Check internet connection**: Restart your router
4. **On Render**: May need to use SendGrid SMTP relay
5. **DNS issues**: Try using IP instead of hostname (not recommended for production)

#### ❌ "Authentication failed"
**Solutions**:
1. Verify Gmail account and app password are correct
2. Ensure 2-Step Verification is enabled in Google Account
3. Check for special characters in password (use exact copy)
4. Ensure account hasn't been recently logged in from new location

#### ❌ "Connection timeout"
**Solutions**:
1. Check if `smtp.gmail.com` is reachable: `ping smtp.gmail.com`
2. Increase timeout value in code (already set to 30 seconds)
3. Check if ISP is blocking SMTP
4. Try using different network (mobile hotspot)

### Database Issues:

#### ❌ Database connection errors
1. Verify `DATABASE_URL` is correct
2. Check if database credentials are correct
3. Ensure Neon IP whitelist includes your server
4. For Render: Database must be accessible from Render's IPs

---

## 📝 Log Monitoring

### View Render Logs:
In Render dashboard > your service > Logs

### View Application Logs:
Logs are printed to stdout with format:
```
2024-01-15 10:30:45 - email_util - INFO - [Attempt 1/3] Connecting to SMTP server...
2024-01-15 10:30:48 - email_util - INFO - ✅ SMTP connection successful!
```

---

## ✅ Testing Checklist

- [ ] Backend runs without errors: `python app.py`
- [ ] Frontend connects to backend without CORS errors
- [ ] Can login with admin credentials
- [ ] Can upload PDF file
- [ ] Can sort attendance data
- [ ] Can fetch student details from database
- [ ] Can send test email to single student
- [ ] Can send mass alert to all students
- [ ] Emails appear in Gmail inbox (check spam folder)
- [ ] Email history is logged in database
- [ ] Dashboard analytics update correctly

---

## 🚀 Git Push Instructions

```powershell
# Stage all changes
git add .

# Commit with meaningful message
git commit -m "Fix SMTP email sending with production-ready error handling and retry logic"

# Push to GitHub
git push origin main

# Render will auto-deploy if webhook is configured
```

---

## 📞 Support Tips

1. **Before deploying**: Test locally first
2. **Gmail issues**: Check https://myaccount.google.com/security
3. **Render issues**: Check https://status.render.com
4. **Neon issues**: Check https://neon.tech/docs
5. **Check logs**: Always check application logs for detailed error messages

---

**Last Updated**: January 2025  
**Email Module Version**: 1.0  
**Status**: Production Ready ✅
