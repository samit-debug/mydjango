# Hiti Library and Study Center

## Run

```powershell
cd C:\Users\HP\Desktop\mydjango
python .\manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## PostgreSQL Setup

1. Install Python dependencies:

```powershell
.\myenv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Create `.env` in the project root:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and set your PostgreSQL password:

```env
DATABASE_ENGINE=postgresql
POSTGRES_DB=hiti_library
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=8388
```

3. Create database `hiti_library` in PostgreSQL, then run:

```powershell
.\myenv\Scripts\python.exe manage.py migrate
.\myenv\Scripts\python.exe manage.py loaddata data_backup.json
```

After this, website data will come from PostgreSQL.

## Seat Admissions

- Student admission form: `/study-center/`
- Staff admissions dashboard: `/study-center/admissions/`
- Auto create seats: `/study-center/seat-setup/`
- Django admin records: `/admin/main/seatbooking/`
- Support/owner profile: `/support/`

Seat admissions store student photo, admission number, student details, guardian contact, seat number, joining date, month-end date, payment status, QR payment proof, reminder status, approval status, and admin notes. Online admissions stay pending until owner/admin approval.

## Owner/Admin Panel

- Owner control center: `/owner/`
- Django admin: `/admin/`
- Website profile and colors: `/admin/main/libraryprofile/`
- Owner photo, support number, helpline, UPI, payment QR: `/admin/main/libraryprofile/`
- Books and copies: `/admin/main/book/`
- Student admissions: `/admin/main/seatbooking/`
- Contact leads: `/admin/main/contactmessage/`

The owner panel gives quick access to data, website content, admissions, monthly alerts, prices, facilities, notices, and user/staff records.

## Render Hosting

This project is ready for Render with:

- Service name: `hiti-library`
- Build command: `bash build.sh`
- Start command: `gunicorn myproject.wsgi:application`
- Python version: `3.14.3`
- PostgreSQL env: `DATABASE_URL`

If you are not using the `render.yaml` blueprint, add these Render environment variables manually:

```env
DEBUG=False
PYTHON_VERSION=3.14.3
ALLOWED_HOSTS=mydjango-f5uc.onrender.com,hiti-library.onrender.com
CSRF_TRUSTED_ORIGINS=https://mydjango-f5uc.onrender.com,https://hiti-library.onrender.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SERVE_MEDIA_FILES=True
SECRET_KEY=<generate-a-long-secret-key>
DATABASE_URL=<your-render-postgres-internal-url>
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=owner@hiti-library.local
DJANGO_SUPERUSER_PASSWORD=<owner-admin-password>
```

For uploaded student photos, owner photo, and QR images, use a Render persistent disk or cloud storage if the site must keep uploads after redeploys.

## Main Files

- `main/views.py`
- `main/urls.py`
- `main/forms.py`
- `main/templates/main/`
- `main/static/main/css/styles.css`
- `main/static/main/js/site.js`
