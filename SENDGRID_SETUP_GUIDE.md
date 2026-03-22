# SendGrid Setup Guide for MonitorMail Production Email

> **Problem Solved**: Previously, MonitorMail used Gmail SMTP which fails on Render because port 587 is blocked for security reasons. This guide switches to SendGrid, which works reliably in all cloud environments.

## Why SendGrid?

- ✅ Works on Render, Vercel, and all cloud platforms
- ✅ No SMTP port blocking issues
- ✅ Higher email delivery reliability
- ✅ Shared server email for all teachers (no individual credentials needed)
- ✅ Same code works locally (development) and production (SendGrid)

---

## Step 1: Create SendGrid Account

1. **Go to SendGrid**: https://sendgrid.com/
2. **Click "Sign up for free"** (free tier includes 100 emails/day)
3. **Fill in your details**:
   - Email: Your email address
   - Password: Strong password
   - Company name: MonitorMail (or your org name)
4. **Verify your email** by clicking the link sent to your inbox
5. **Complete account setup** - Accept the terms

---

## Step 2: Generate SendGrid API Key

### In SendGrid Dashboard:

1. **Click your profile icon** (top right) → **Settings**
2. **Left sidebar** → **API Keys**
3. **Click "Create API Key"** button
4. **Name it**: `MonitorMail-Production` (or any name)
5. **Permissions**: Select **Full Access** (or minimum `Mail Send` permission)
6. **Copy the API key** that appears (starts with `SG.` and is very long)
   - ⚠️ **IMPORTANT**: Save this somewhere safe - SendGrid shows it only once!
   - If you lose it, create a new one

---

## Step 3: Add Environment Variables to Render

### In Render Dashboard:

1. **Go to your Render backend service**: https://render.com/dashboard
2. **Click on your "monitormail-backend" service**
3. **Click "Environment"** tab (next to "Build Logs")
4. **Click "Add Environment Variable"** → Add these:

| Key | Value |
|-----|-------|
| `SENDGRID_API_KEY` | `SG.xxx...yyy` (your full API key from Step 2) |
| `SENDGRID_FROM_EMAIL` | `noreply@monitormail.com` |

5. **Click "Save"** - Render will automatically redeploy your app

---

## Step 4: Verify SendGrid Domain (Optional but Recommended)

> This step improves email delivery rates. Skip if you want to test first.

### Add Domain to SendGrid:

1. **SendGrid Dashboard** → **Settings** → **Sender Authentication**
2. **Click "Authenticate Your Domain"**
3. **Enter domain**: `monitormail.com` (or your actual domain)
4. **SendGrid shows DNS records** to add to your domain provider
5. **Add the DNS records** to your domain (at GoDaddy, Namecheap, etc.)
6. **Come back to SendGrid** and click "Verify"

### If you don't have a custom domain:
- Keep using `noreply@monitormail.com` (generic, but works fine)
- Or use your Gmail address temporarily: `ujjwal3rd@gmail.com`

---

## Step 5: Test the Setup

### Test Locally First:

1. **In your local terminal**, open Python:
```bash
cd backend
python3
```

2. **Create test script** `test_sendgrid.py`:
```python
import smtplib
import os

# Set environment variables for testing
os.environ['SENDGRID_API_KEY'] = 'SG.xxx...yyy'  # paste your API key here
os.environ['SENDGRID_FROM_EMAIL'] = 'noreply@monitormail.com'

from email_util import EmailSender

# Test SendGrid SMTP
try:
    sender = EmailSender()
    success, msg = sender.send_email(
        to_email='your-email@gmail.com',
        subject='📧 SendGrid Test - MonitorMail',
        body_html='<h2>✅ SendGrid is working!</h2><p>Email sent successfully.</p>'
    )
    print(f"Result: {success} - {msg}")
    sender.logout()
except Exception as e:
    print(f"ERROR: {e}")
```

3. **Run the test**:
```bash
python3 test_sendgrid.py
```

4. **Check your email inbox** - You should receive the test email

---

## Step 6: How Multiple Teachers Send Emails Now

### **Before** (Gmail SMTP - ❌ broken on Render):
```
Teacher Login → Gmail SMTP with Personal Credentials → Email Sent
 ↓
Problem: Render blocks port 587, each teacher needs their own Gmail account
```

### **After** (SendGrid SMTP - ✅ works everywhere):
```
Teacher Login → SendGrid SMTP (shared server credentials) → Email Sent
                    ↓
All emails appear from: noreply@monitormail.com
Email system works for unlimited teachers!
```

### Architecture Benefits:
- ✅ Teachers use their MonitorMail login (example: `ujjwal3rd@gmail.com`)
- ✅ System sends emails from shared SendGrid account
- ✅ No need for individual email credentials
- ✅ Works on Render, Vercel, local development everywhere
- ✅ Scalable - add unlimited teachers without complexity

---

## Step 7: Deploy to Production

### After Render auto-redeploy from environment variables:

1. **Test the production URL**:
   - Go to: `https://your-vercel-app.vercel.app`
   - **Login** with your teacher account
   - **Send a test email** to one student
   - **Check if email arrives** in your inbox (may take 30 seconds)

2. **Monitor logs** (if there are issues):
   - **In Render dashboard** → **Logs** tab
   - Look for `SendGrid` connection messages
   - Check for errors like "authentication failed"

---

## Step 8: Troubleshooting

### **Email not arriving?**

1. **Check logs in Render**:
   ```
   Configured for SendGrid SMTP relay
   Sending email to student@example.com...
   ✅ Email sent to student@example.com
   ```
   - If you see `✅`, email was sent correctly
   - Might be in SPAM folder instead

2. **API Key wrong?**
   - Verify in Render → Environment tab
   - API key should start with `SG.`
   - Check for copy-paste errors (extra spaces?)

3. **SendGrid account issues?**
   - Log in to SendGrid dashboard
   - Check if account is in trial mode (might have rate limits)
   - Check "Activity" for bounce/error logs

### **Still seeing "Network is unreachable"?**

1. **Clear browser cache** and refresh
2. **Check Render logs** while trying to send
3. **Restart Render** service: Dashboard → Service → Manual Deploy
4. **Verify environment variables** are actually applied (might need manual redeploy)

---

## Step 9: Update Your Code Locally (Already Done ✅)

> The `backend/email_util.py` has been updated to support SendGrid automatically.

The file now:
- ✅ Detects `SENDGRID_API_KEY` environment variable
- ✅ If set: Uses SendGrid SMTP relay (production)
- ✅ If not set: Uses Gmail SMTP (local development)
- ✅ Handles both modes transparently

**No code changes needed in `app.py`** - It already uses `EmailSender` class correctly!

---

## Reference: Code Flow

### When you send an email in production:

```
Vercel Frontend (React)
    ↓ sends FormData with email list
Render Backend (Flask / app.py)
    ↓ creates EmailSender()
email_util.py checks environment
    ↓ SENDGRID_API_KEY found → uses SendGrid
SendGrid SMTP relay (port 587 - works on Render!)
    ↓ 
SendGrid delivery servers
    ↓
✅ Email delivered to student inbox
```

---

## Checklist: Confirm Setup Complete

- [ ] SendGrid account created
- [ ] API key generated and copied
- [ ] API key added to Render Environment variables
- [ ] SENDGRID_FROM_EMAIL added to Render Environment variables
- [ ] Render auto-deployed after adding variables
- [ ] Local test sending email (optional but recommended)
- [ ] Production test (login → send email → receive email)
- [ ] Multiple teachers can login and send emails

---

## FAQ

**Q: Can we use Gmail SMTP instead?**
A: Not reliably in production. Render blocks port 587. SendGrid is the solution.

**Q: Do teachers need their own SendGrid accounts?**
A: No! All emails are sent through one shared SendGrid account using the API key.

**Q: How many emails can we send per day?**
A: SendGrid free tier = 100 emails/day. Pro plans are unlimited (~$19/month).

**Q: Can I use a custom domain (example@myschool.com)?**
A: Yes! In Step 4, authenticate your custom domain. Then set `SENDGRID_FROM_EMAIL` to your custom domain.

**Q: What if I lose my API key?**
A: Create a new one in SendGrid → Settings → API Keys → Create API Key

**Q: How do I test locally without the API key?**
A: Leave `SENDGRID_API_KEY` unset in your `.env` file - system falls back to Gmail SMTP locally.

---

## Next Steps

1. ✅ Follow Steps 1-3 above
2. ✅ Render will auto-redeploy
3. ✅ Test in production (Vercel app)
4. ✅ Verify email delivery
5. ✅ Train multiple teachers to use the system

**Questions?** Check the logs in Render dashboard or review [SendGrid Docs](https://sendgrid.com/docs/for-developers/sending-email/quickstart-nodejs/).

---

**Last Updated**: 2025
**System**: MonitorMail Production Email
**Status**: ✅ Ready for Production
