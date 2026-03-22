# Brevo SMTP Setup Guide for MonitorMail Production Email

> **Free Forever Solution**: Brevo offers 300 emails/day permanently free with no trial expiration. Perfect for school email systems!

## Why Brevo?

- ✅ **300 emails/day FREE forever** (no credit card required)
- ✅ Works perfectly on Render (no port blocking issues)
- ✅ Reliable enterprise-grade SMTP
- ✅ Same code works locally (development) and production (Brevo)
- ✅ Shared server email for all teachers (no individual credentials)
- ✅ Trusted by 500k+ users globally

---

## Step 1: Create Brevo Account

1. **Go to Brevo**: https://www.brevo.com/
2. **Click "Sign up"** (choose "For Business" or "For Education" if available)
3. **Fill in your details**:
   - Email: Your email address
   - Password: Strong password
   - Company: MonitorMail (or your org name)
4. **Verify your email** by clicking the link in your inbox
5. **Complete setup** - Accept terms and create account

---

## Step 2: Generate SMTP Credentials

### In Brevo Dashboard:

1. **After login**, click your profile icon (top right)
2. **Go to "SMTP & API"** or **"Settings" → "SMTP & API"**
3. **Under SMTP**, you'll see:
   - **SMTP Server**: `smtp.brevo.com` ✅ (you'll need this)
   - **SMTP Port**: `587` ✅ (you'll need this)
   - **Your Brevo Email**: Something like `account@brevo.fr` (this is your SMTP username)
   
4. **Click "Generate SMTP Password"** button
5. **Copy the SMTP password** that appears
   - ⚠️ **IMPORTANT**: Save this somewhere safe - you'll need it!
   - If you lose it for security, you can generate a new one anytime

### You now have:
- **Brevo SMTP Email**: `account@brevo.fr` (or whatever Brevo assigned)
- **Brevo SMTP Password**: Long random string (starts with `xb...`)
- **Server**: `smtp.brevo.com:587`

---

## Step 3: Add Environment Variables to Render

### In Render Dashboard:

1. **Go to**: https://render.com/dashboard
2. **Click your "monitormail-backend" service**
3. **Click "Environment"** tab (next to "Build & Deploy", "Logs")
4. **Click "Add Environment Variable"** and add:

| Key | Value |
|-----|-------|
| `BREVO_SMTP_EMAIL` | `account@brevo.fr` (Your Brevo email from Step 2) |
| `BREVO_SMTP_PASSWORD` | `xb...` (Your Brevo SMTP password from Step 2) |
| `BREVO_FROM_EMAIL` | `noreply@monitormail.com` (What appears in "From" field) |

5. **Click "Save"** - Render will auto-redeploy your application

---

## Step 4: Customize "From" Email Address (Optional)

By default, emails appear from `noreply@monitormail.com`.

### To use a different email:

**Option A: Use your own email**
- In Render environment, set:
  - `BREVO_FROM_EMAIL` = `ujjwal3rd@gmail.com` (your email address)
  - Emails appear as coming from you

**Option B: Verify a custom domain** (if you own a domain)
1. **In Brevo**, go to "Senders List"
2. **Add a new sender** with your domain (example@yourschool.com)
3. **Verify the domain** by adding DNS records
4. **Set `BREVO_FROM_EMAIL`** = your verified domain email

---

## Step 5: Test the Setup

### Test Locally First:

1. **In local terminal**, create test script `test_brevo.py`:

```bash
cd backend
```

```python
# test_brevo.py
import os

# FOR TESTING ONLY - Set these from Step 2
os.environ['BREVO_SMTP_EMAIL'] = 'account@brevo.fr'  # Your Brevo email
os.environ['BREVO_SMTP_PASSWORD'] = 'xb...'  # Your Brevo password
os.environ['BREVO_FROM_EMAIL'] = 'noreply@monitormail.com'

from email_util import EmailSender

try:
    sender = EmailSender()
    success, msg = sender.send_email(
        to_email='your-email@gmail.com',
        subject='📧 Brevo Test - MonitorMail',
        body_html='<h2>✅ Brevo SMTP is working!</h2><p>Email sent successfully.</p>'
    )
    print(f"Result: {success} - {msg}")
    sender.logout()
except Exception as e:
    print(f"ERROR: {e}")
```

2. **Run the test**:
```bash
python3 test_brevo.py
```

3. **Check your email inbox** (30 seconds) - You should receive the test email

### Test in Production:

1. **Go to your Vercel app** (your frontend URL)
2. **Login** with teacher account
3. **Send a test email** to a student
4. **Check student's inbox** (may take 30 seconds)
5. **Email should arrive** from `noreply@monitormail.com` ✅

---

## Step 6: How Multiple Teachers Work Now

### The New Architecture:

```
┌────────────────────────────────────────────┐
│ All Teachers Login to MonitorMail          │
│ (with their own credentials)               │
└────────────────────┬───────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ Send Email to Students │
        └────────┬───────────────┘
                 │
                 ↓
    ┌───────────────────────────┐
    │ Brevo SMTP Relay          │
    │ (Shared server email)     │
    └────────┬──────────────────┘
             │
             ↓
   ┌─────────────────────────┐
   │ Email in Student Inbox  │
   │ From: noreply@...       │
   └─────────────────────────┘
```

### Benefits:
- ✅ Teachers use their MonitorMail login (example: `ujjwal3rd@gmail.com`)
- ✅ All emails sent through one shared Brevo account
- ✅ No individual teacher email credentials required
- ✅ Works on Render (no SMTP port blocking)
- ✅ Unlimited teachers can send simultaneously
- ✅ Free forever (300 emails/day)

---

## Step 7: Brevo Account Limits & Upgrades

### Free Tier (Forever):
- **300 emails/day** 
- **All features included**
- No credit card required
- Perfect for most schools

### If you need more:
- **Upgrade to Premium**: $20/month for 10,000+ emails
- **Pay-as-you-go**: $0.01 per email after free tier
- **Education discount**: Contact Brevo sales for non-profit rates

---

## Step 8: Monitor Email Delivery

### View Sent Emails in Brevo:

1. **In Brevo Dashboard**, go to **"Transactional"** or **"Email Activity"**
2. **See all emails sent** from your account
3. **Track delivery status** (sent, delivered, opened, bounced)
4. **Useful data**:
   - Total emails sent today
   - Delivery success rate
   - Any bounced emails (invalid addresses)

---

## Step 9: Troubleshooting

### Email Not Arriving?

1. **Check Brevo logs**:
   - Brevo Dashboard → Email Activity
   - Look for your test email
   - Check status (Sent? Delivered? Bounced?)

2. **Check Render logs**:
   - Render Dashboard → Your service → Logs
   - Look for: `Configured for Brevo SMTP relay`
   - Look for: `✅ Brevo SMTP connection successful!`
   - Look for: `✅ Email sent to student@example.com`

3. **Common issues**:
   - **Wrong SMTP credentials**: Re-check Step 2
   - **Email in SPAM**: Check student's spam folder
   - **Invalid recipient email**: Student email might be wrong

4. **Restart Render**:
   - Render Dashboard → Your service → Manual Deploy
   - This forces a fresh connection

---

## Step 10: Update Code (Already Done ✅)

> The `backend/email_util.py` has been updated to support Brevo automatically.

The file now:
- ✅ Detects `BREVO_SMTP_PASSWORD` environment variable
- ✅ If set: Uses Brevo SMTP relay (production)
- ✅ If not set: Uses Gmail SMTP (local development)
- ✅ Handles both modes transparently

**No changes needed in `app.py`** - Everything works as-is!

---

## Checklist: Confirm Setup Complete

- [ ] Brevo account created
- [ ] SMTP credentials generated (SMTP Email & Password)
- [ ] `BREVO_SMTP_EMAIL` added to Render environment
- [ ] `BREVO_SMTP_PASSWORD` added to Render environment
- [ ] `BREVO_FROM_EMAIL` added to Render environment (optional, defaults to noreply@monitormail.com)
- [ ] Render auto-deployed (auto-redeployment happens 1-2 minutes after adding variables)
- [ ] Local test email sent (optional but recommended)
- [ ] Production test: Login and send email via Vercel app
- [ ] Email arrived in student inbox ✅

---

## FAQ

**Q: What happens if we exceed 300 emails/day?**
A: Brevo stops sending temporarily until the next day. For most schools, 300/day is more than enough. Upgrade if needed.

**Q: Can I use my school's email domain?**
A: Yes! Add it in Brevo "Senders List" and verify via DNS. Then use it in `BREVO_FROM_EMAIL`.

**Q: What if I lose the SMTP password?**
A: No problem! Go back to Brevo → SMTP settings and generate a new one. Update Render environment variables.

**Q: Can teachers send emails from their personal email?**
A: No - all emails go through the shared Brevo account and appear from `noreply@monitormail.com`. This is intentional (security + consistency).

**Q: Is Brevo SMTP secure?**
A: Yes! Uses TLS encryption (port 587). Industry standard security.

**Q: How long does Brevo exist?**
A: Founded 2016, used by 500k+ customers, acquired by Brevo parent company. Very stable.

---

## Reference: Environment Variables Summary

### Render Configuration:
```
BREVO_SMTP_EMAIL = "account@brevo.fr"          # Your Brevo login email
BREVO_SMTP_PASSWORD = "xb..."                  # Your Brevo SMTP password
BREVO_FROM_EMAIL = "noreply@monitormail.com"   # What students see in "From" field
```

### Code Detection (automatic):
```python
USE_BREVO = os.environ.get('BREVO_SMTP_PASSWORD') is not None
# If BREVO_SMTP_PASSWORD exists → uses Brevo
# If not found → falls back to Gmail SMTP (for local dev)
```

---

## Next Steps

1. ✅ Create Brevo account (5 minutes)
2. ✅ Generate SMTP credentials (2 minutes)
3. ✅ Add to Render environment (3 minutes)
4. ✅ Test in production (5 minutes)
5. ✅ Train teachers to use system

**Total setup time: ~15 minutes**

---

## Support

**Brevo Documentation**: https://www.brevo.com/help/
**Brevo Support Email**: support@brevo.com
**Status Page**: https://status.brevo.com

---

**Last Updated**: 2026
**System**: MonitorMail Production Email
**Service**: Brevo SMTP Relay
**Status**: ✅ Production Ready - Free Forever
