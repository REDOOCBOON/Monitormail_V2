# 🔧 MonitorMail Email Sending - Quick Fix Guide

## Problem: "Emails sent" but not received?

This usually means Brevo is accepting the request but **rejecting the sender email** because it's not verified in your Brevo account.

---

## ✅ Quick Fix (5 minutes)

### Step 1: Check your Brevo account
1. Log in to https://app.brevo.com
2. Go to **Settings → Senders & API**
3. Look for your **verified sender emails** (should have a ✅)

### Step 2: Set the CORRECT sender email
You need to configure the `BREVO_FROM_EMAIL` environment variable with an **actual verified email** from your Brevo account.

**PowerShell (Local Development):**
```powershell
# Replace YOUR_VERIFIED_EMAIL with an actual verified email from Brevo
$env:BREVO_FROM_EMAIL = "YOUR_VERIFIED_EMAIL@domain.com"
python backend/app.py
```

**Environment variables (Production on Render/Vercel):**
```
BREVO_FROM_EMAIL=YOUR_VERIFIED_EMAIL@domain.com
```

### Step 3: Verify it's working
Run the diagnostic tool:
```bash
python backend/test_brevo_diagnostic.py
```

Answer `y` when asked to test email sending. You should see:
- ✅ `Response Status: 201`
- ✅ A `messageId` in the response

---

## 🔍 Why does this happen?

When you send an email through Brevo's REST API, the **sender address MUST be verified in your Brevo account**. Here's what's happening:

1. Default sender: `noreply@monitormail.com` ❌ (NOT verified in Brevo)
2. Brevo receives the request → accepts it (HTTP 201) ✅
3. Brevo tries to send the email → FAILS because sender isn't verified ❌
4. But you see "sent" in the database because the API call succeeded 🐛

---

## ⚙️ Configuration Options

### Option 1: Default Setup (Recommended for School)
Use your school's email as the sender:
```powershell
$env:BREVO_FROM_EMAIL = "notifications@yourschool.edu"
```

Then verify this email in Brevo:
1. Go to Brevo Settings → Senders
2. Add the email
3. Brevo will send a verification link to that email
4. Click the link to verify

### Option 2: Use a Service Email
```powershell
$env:BREVO_FROM_EMAIL = "monitormail@yourschool.edu"
```

### Option 3: Use Your Personal Verified Email (Temporary)
```powershell
$env:BREVO_FROM_EMAIL = "your-email@gmail.com"
```
(If you already have it verified in Brevo)

---

## 📋 Environment Variables

Set BOTH of these:

```powershell
# Your Brevo API Key (REST API)
$env:BREVO_API_KEY = "xkeysib-xxxx...xxxx"

# Your VERIFIED sender email from Brevo account
$env:BREVO_FROM_EMAIL = "notifications@yourschool.edu"
```

---

## ✅ Testing Email Sending

After configuring, test with:

```bash
cd backend
python test_brevo_diagnostic.py
```

Expected output when everything is correct:
```
USE_BREVO: True ✅
BREVO_API_KEY set: True ✅
BREVO_FROM_EMAIL: notifications@yourschool.edu ✅

Response Status: 201 ✅
✅ API request was successful! ✅
```

---

## 🚀 After Configuration

1. Restart the backend:  
   ```bash
   python backend/app.py
   ```

2. Go to frontend and send a test email

3. You should receive it within 30 seconds

---

## 💡 Troubleshooting

| Issue | Solution |
|-------|----------|
| Still not receiving emails | Check Brevo spam folder, verify sender email is in Brevo account |
| Getting "Invalid API key" error | Copy BREVO_API_KEY carefully (no spaces/newlines) |
| Getting 400 Bad Request | Email address format is wrong, check for typos |
| Getting 429 Rate Limited | You've sent too many emails (Brevo rate limit). Wait 1 hour. |

---

## 📚 More Help

- [Brevo API Documentation](https://developers.brevo.com/docs/send-transactional-emails)
- [Email Sending Setup Guide](./BREVO_SETUP_GUIDE.md)
- Check logs: `python test_brevo_diagnostic.py`
