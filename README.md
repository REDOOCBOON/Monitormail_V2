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

## ✅ Getting Started

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

3. Run the backend

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

2. Run the frontend

```powershell
npm start
```

The UI should open in your browser at `http://localhost:3000` (or another port if 3000 is busy).

---

## 🔐 Security Notes

- **Always set `SECRET_KEY`** for production so JWT tokens remain valid across restarts.
- **Run behind HTTPS** to prevent token/session interception.
- Use strong passwords and consider using App Passwords for Gmail.

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
