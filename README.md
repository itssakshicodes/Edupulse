# EduPulse — Academic Performance Intelligence Platform

A complete, production-ready Django web application for academic analytics
with role-based access control, interactive Google Charts dashboards,
CSV/Excel import, PDF reports, and email notifications.

---

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites
- Python 3.10+ installed
- pip (Python package manager)

### 2. Clone / Extract the project
```bash
cd edupulse/
```

### 3. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Apply database migrations
```bash
python manage.py migrate
```

### 6. Load demo data (recommended for first run)
```bash
python manage.py create_demo_data
```
This creates:
| Role    | Username  | Password    |
|---------|-----------|-------------|
| Admin   | admin     | admin123    |
| Faculty | faculty1  | faculty123  |
| HOD     | hod1      | hod123      |
| Student | alice21   | student123  |
| Student | bob21     | student123  |
| Student | carol21   | student123  |

### 7. Collect static files
```bash
python manage.py collectstatic --noinput
```

### 8. Run the development server
```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## 📁 Project Structure

```
edupulse/
│
├── edupulse/                  # Django project config
│   ├── settings.py            # All settings (DB, email, static, etc.)
│   ├── urls.py                # Root URL dispatcher
│   └── wsgi.py
│
├── accounts/                  # Authentication + RBAC
│   ├── models.py              # Profile model (extends User)
│   ├── views.py               # Login, logout, user CRUD
│   ├── forms.py               # Login, register, profile forms
│   ├── decorators.py          # @role_required, @admin_required, etc.
│   └── urls.py
│
├── results/                   # Core academic data
│   ├── models.py              # Batch, Subject, Result, UploadLog
│   ├── views.py               # Upload, list, edit, export (CSV/PDF)
│   ├── forms.py               # Upload form, filter form, manual entry
│   ├── utils.py               # CSV/Excel parser + validator
│   └── urls.py
│
├── analytics/                 # Charts and dashboards
│   ├── views.py               # Dashboard views + JSON chart endpoints
│   └── urls.py
│
├── core/                      # Shared utilities
│   ├── views.py               # Role-based dashboard router
│   ├── signals.py             # Email alert on low performance
│   ├── apps.py                # Registers signals
│   └── management/
│       └── commands/
│           └── create_demo_data.py
│
├── templates/                 # All HTML templates
│   ├── base.html              # Master layout with sidebar
│   ├── accounts/
│   ├── results/
│   ├── analytics/
│   └── core/
│
├── static/
│   ├── css/main.css           # Custom design system
│   ├── js/main.js             # Google Charts loader + sidebar JS
│   └── sample_results.csv     # Sample upload file
│
├── media/                     # Uploaded files (runtime)
├── manage.py
└── requirements.txt
```

---

## 👥 User Roles & Access

| Feature                    | Admin | Faculty | HOD | Student |
|----------------------------|:-----:|:-------:|:---:|:-------:|
| Upload CSV/Excel           | ✅    | ✅      | ❌  | ❌      |
| Add result manually        | ✅    | ✅      | ❌  | ❌      |
| View all results           | ✅    | ✅      | ✅  | ❌      |
| Delete results             | ✅    | ❌      | ❌  | ❌      |
| Institution analytics      | ✅    | ✅      | ✅  | ❌      |
| Subject analysis           | ✅    | ✅      | ✅  | ❌      |
| View own results only      | ❌    | ❌      | ❌  | ✅      |
| Download personal PDF      | ❌    | ❌      | ❌  | ✅      |
| Manage users               | ✅    | ❌      | ❌  | ❌      |
| Manage subjects/batches    | ✅    | ❌      | ❌  | ❌      |
| Upload logs                | ✅    | ❌      | ❌  | ❌      |
| Export CSV (all results)   | ✅    | ✅      | ✅  | ❌      |
| Export PDF (all results)   | ✅    | ✅      | ✅  | ❌      |

---

## 📤 CSV Upload Format

Your file must contain these exact column headers (row 1):

```
roll_number, subject_code, semester, batch_name, marks_obtained, remarks
```

- `roll_number` — must match a student profile's roll number
- `subject_code` — must match an existing subject code (e.g. CS301)
- `semester` — integer 1–10
- `batch_name` — must match an existing batch name (e.g. 2021-2025)
- `marks_obtained` — float 0–100
- `remarks` — optional free text

A sample file is available at `/static/sample_results.csv`.

### What happens on upload:
1. File is parsed row by row
2. Each row is validated (missing fields, invalid marks, unknown roll numbers, duplicates)
3. Valid rows are saved; errors are displayed in a detailed error report
4. An `UploadLog` audit entry is created for every upload
5. If a student fails, an email alert is sent automatically (if email is configured)

---

## 📊 Charts (Google Charts)

All charts are **live and filterable via AJAX** — no page reload needed.

| Chart Type    | Data Shown                        | Filters Available              |
|---------------|-----------------------------------|-------------------------------|
| Pie Chart     | Overall Pass vs Fail              | Semester, Batch               |
| Column Chart  | Grade distribution (O/A+/A/…/F)  | Semester, Subject             |
| Line Chart    | Average marks per semester        | Batch, Subject                |
| Bar Chart     | Average marks per subject         | Semester, Batch               |
| Scatter Plot  | Individual student performance    | Semester, Subject             |
| Line Chart    | Personal semester trend (student) | — (auto-filtered by user)     |

---

## 📧 Email Configuration

Email uses Django's console backend by default (prints to terminal).
To send real emails, update `edupulse/settings.py`:

```python
EMAIL_BACKEND     = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST        = 'smtp.gmail.com'
EMAIL_PORT        = 587
EMAIL_USE_TLS     = True
EMAIL_HOST_USER   = 'your-gmail@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Gmail App Password (not regular password)
```

Email alerts fire automatically when:
- A student result is uploaded with `is_pass = False`

---

## 📄 Report Generation

### CSV Export
- URL: `/results/export/csv/`
- Supports filter query params: `?semester=3&batch=1&subject=2`
- Downloads instantly as `results_export.csv`

### PDF Export
- URL: `/results/export/pdf/`
- Generated with ReportLab
- Students get their own results only
- Staff get full institution report
- Downloads as `edupulse_report.pdf`

---

## 🔐 RBAC Decorators

Custom decorators in `accounts/decorators.py`:

```python
from accounts.decorators import (
    role_required,     # @role_required('admin', 'hod')
    admin_required,    # @admin_required
    faculty_required,  # @faculty_required   (admin + faculty)
    hod_required,      # @hod_required       (admin + hod)
    staff_required,    # @staff_required     (admin + faculty + hod)
    student_required,  # @student_required
)
```

Usage:
```python
@staff_required
def my_view(request):
    ...
```

---

## 🗄️ Database Models

### Profile (extends User)
- `role`: admin | faculty | hod | student
- `department`, `phone`, `roll_number`, `bio`
- Auto-created via `post_save` signal on User

### Batch
- `name`, `department`, `start_year`, `end_year`
- Unique constraint: `(name, department)`

### Subject
- `code` (unique), `name`, `department`, `semester`
- `max_marks` (default 100), `pass_marks` (default 40), `credits`

### Result
- FK to: `student` (User), `subject`, `batch`
- `marks_obtained`, `semester`
- **Auto-calculated**: `grade` (O/A+/A/B+/B/C/F), `is_pass`
- Unique constraint: `(student, subject, semester, batch)` — no duplicates

### UploadLog
- Audit trail: file name, uploader, total/success/error rows, status, timestamp

---

## 🧪 Testing the Application

After running `create_demo_data`:

1. **Admin view**: Login as `admin/admin123` → full dashboard with all 4 charts
2. **Upload test**: Go to Results → Upload → upload `static/sample_results.csv`
3. **Filter test**: Results list → apply semester/batch/grade filters
4. **Analytics**: Analytics → Institution → use dropdown filters to refresh charts live
5. **Student view**: Login as `alice21/student123` → personal trend chart + results table
6. **PDF report**: Any role → Results → Export PDF

---

## ⚙️ Customisation

### Add a new role
1. Add to `Profile.ROLE_CHOICES` in `accounts/models.py`
2. Add a decorator in `accounts/decorators.py`
3. Add a case in `core/views.py → dashboard()`
4. Create a template: `templates/core/dashboard_<role>.html`
5. Update sidebar in `templates/base.html`

### Change pass mark threshold globally
Edit `Subject.pass_marks` default in `results/models.py`.
Or update per-subject via Admin or the Subjects management page.

### Change grade boundaries
Edit `Result.calculate_grade()` in `results/models.py`.

---

## 🛠️ Common Management Commands

```bash
# Create demo data (first time setup)
python manage.py create_demo_data

# Create a superuser manually
python manage.py createsuperuser

# Make + apply migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Open Django shell
python manage.py shell

# Collect static files for production
python manage.py collectstatic
```

---

## 🚀 Deployment Notes (Production)

1. Set `DEBUG = False` in `settings.py`
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL instead of SQLite for production
5. Use Gunicorn + Nginx
6. Set `EMAIL_BACKEND` to SMTP
7. Run `collectstatic` and serve `/staticfiles/` via Nginx

---

## 📦 Dependencies

| Package     | Version  | Purpose                        |
|-------------|----------|-------------------------------|
| Django      | ≥ 4.2    | Web framework                  |
| openpyxl    | ≥ 3.1    | Excel (.xlsx) file parsing     |
| reportlab   | ≥ 4.0    | PDF report generation          |
| Pillow      | ≥ 10.0   | Image handling (avatars)       |

---

## 💡 Architecture Decisions

- **SQLite3**: Zero-config default — swap to PostgreSQL for production
- **Class vs Function views**: Functions used throughout for simplicity and decorator clarity
- **Google Charts via AJAX**: All chart data served as JSON from dedicated endpoints — decoupled from page renders
- **Signal-based emails**: Low-performance alerts fire via Django signals — no manual calls in views
- **Two-stage upload**: Parse → show errors → save atomically — prevents partial bad data
- **Auto-grade calculation**: `Result.save()` computes grade and pass/fail — never stored manually

---

*Built with Django 4.2, Bootstrap 5, Google Charts — EduPulse © 2024*
# edupulse
