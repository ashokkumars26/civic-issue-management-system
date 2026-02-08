## Dark-Themed AI-Assisted Civic Issue Management System (Chennai)

This project is a **Flask-based full-stack prototype** for a dark-themed, AI-assisted civic issue management system for the **Chennai Metropolitan City**.  
Citizens can report civic issues, track their status, receive email notifications, and download government-style PDF reports. Admins can manage issues, update statuses, upload after-fix images, and view basic analytics.

### 1. Features Overview

- **Dark, modern UI**
  - Colorful dark theme with subtle gradients and glow effects.
  - Smooth card/timeline animations and micro-interactions.
  - Separate **Citizen** and **Admin** dashboards.

- **Citizen (User) Capabilities**
  - Report issues via a guided form:
    - Choose from **10 predefined civic issue types** + **“Other”**.
    - Mandatory **issue description**.
    - Location selection from **19 Chennai areas** (including **Poonamallee**).
    - Manual input for **street name** and **nearby landmark**.
    - Optional **image upload** (before-fix photo).
  - View **list of reported issues** with:
    - Status pill and **status timeline**.
    - AI-generated summary of severity and priority.
    - **Before/after image comparison** (if after-image uploaded by admin).
    - **PDF report download** for each issue.
  - After an issue is resolved:
    - Provide **feedback and rating (1–5)** with optional comments.

- **Admin Capabilities**
  - Admin dashboard with:
    - **Total / Pending / Resolved** issue counts.
    - Filter issues by **status**.
  - For each issue:
    - View details, AI analysis, and location.
    - Update **status** (Pending / In Progress / Resolved).
    - Add **authority remarks**.
    - Upload an **after-fix image**.

- **Email Notifications**
  - On **issue submission** (to citizen’s email, if provided).
  - On **status updates** from admin (if citizen email is present).

- **PDF Reports**
  - Per-issue downloadable **government-style PDF**:
    - Citizen details.
    - Issue description.
    - Location details.
    - AI analysis summary.
    - Status timeline.
    - Authority remarks.
    - Latest feedback (if any).
    - Layout includes **before/after image slots**.
    - Footer clearly states **digitally generated, no manual signature required**.

- **Backend & Data**
  - **Flask** backend (`app.py`).
  - **SQLite** database via **Flask-SQLAlchemy**.
  - Structured tables:
    - `User`, `Issue`, `IssueStatusLog`, `Feedback`.
  - Secure(ish) file upload handling with basic checks and dedicated upload folder.

---

### 2. Project Structure

Key files/directories:

- `app.py` – Main Flask application, routes, email sending, issue flows.
- `models.py` – SQLAlchemy models (`User`, `Issue`, `IssueStatusLog`, `Feedback`).
- `utils.py` – AI-like analysis helper and PDF generation logic.
- `templates/`
  - `base.html` – Base layout, dark theme shell, nav, flash messages.
  - `user_dashboard.html` – Citizen dashboard + issue reporting and tracking.
  - `admin_dashboard.html` – Admin dashboard + analytics + issue management.
- `static/css/style.css` – Dark-theme styling, animations, layout.
- `static/js/main.js` – Small client-side enhancements/micro-interactions.
- `requirements.txt` – Python dependencies.

---

### 3. What to Download / Install

You need:

- **Python 3.10+**
- **pip** (Python package manager)

Project dependencies (installed automatically via `requirements.txt`):

- **Flask**
- **Flask-SQLAlchemy**
- **Flask-Mail**
- **reportlab** (for PDF generation)

Optional (for development convenience):

- A virtual environment tool:
  - `venv` (bundled with Python) or
  - `virtualenv` / `conda` (if you prefer)

#### Install dependencies

From the project root (`C:\Users\ASHOK KUMAR\OneDrive\Desktop\se`):

```bash
python -m venv venv
venv\Scripts\activate  # On Windows PowerShell or CMD

pip install -r requirements.txt
```

---

### 4. Configuring Email (Flask-Mail)

In `app.py`, the mail configuration is defined as:

```python
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'you@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
app.config['MAIL_DEFAULT_SENDER'] = ('Chennai CivicCare AI', 'you@example.com')
```

To enable real email sending:

1. Replace `smtp.example.com`, `you@example.com`, and `your-password` with **real SMTP server details**.
2. For common providers (e.g., Gmail), you may need to:
   - Enable **App Passwords** (recommended) or
   - Allow less secure app access (not recommended for production).
3. If you just want to **develop/test without sending emails**, you can:
   - Leave as-is and ignore console warnings, or
   - Use a local SMTP debug server (e.g., `python -m smtpd -c DebuggingServer -n localhost:1025`) and set:
     - `MAIL_SERVER = 'localhost'`
     - `MAIL_PORT = 1025`
     - `MAIL_USE_TLS = False`

---

### 5. Running the Application (Local)

1. **Activate virtual environment** (if not already):

```bash
cd C:\Users\ASHOK KUMAR\OneDrive\Desktop\se
venv\Scripts\activate
```

2. **Set Flask app (optional, app uses `if __name__ == '__main__'`)**:

You can run directly:

```bash
python app.py
```

This will:

- Create `civic_issues.db` (SQLite) if not present.
- Start Flask dev server at `http://127.0.0.1:5000/`.

3. Open in browser:

- **Citizen dashboard**: `http://127.0.0.1:5000/user/dashboard`
- **Admin dashboard**: `http://127.0.0.1:5000/admin/dashboard`

---

### 6. Data Model (Database Tables)

- **User**
  - `id` (PK)
  - `name`
  - `email`
  - `phone`
  - `created_at`
  - Relationship: `issues` (one-to-many)

- **Issue**
  - `id` (PK)
  - `user_id` (FK → `User.id`)
  - `issue_type` (one of 10 predefined types or “Other”)
  - `description` (mandatory)
  - `area` (one of 19 Chennai areas, including Poonamallee)
  - `street`
  - `landmark`
  - `before_image` (path)
  - `after_image` (path)
  - `ai_summary`
  - `current_status` (`Pending` / `In Progress` / `Resolved`)
  - `authority_remarks`
  - `created_at`, `updated_at`
  - Relationships: `status_logs`, `feedbacks`

- **IssueStatusLog**
  - `id` (PK)
  - `issue_id` (FK → `Issue.id`)
  - `status`
  - `remarks`
  - `created_at`

- **Feedback**
  - `id` (PK)
  - `issue_id` (FK → `Issue.id`)
  - `rating` (1–5)
  - `comments`
  - `created_at`

---

### 7. AI Analysis Summary

The system uses a **simple, rule-based function** in `utils.py` (`ai_analyze_issue`) to generate an **AI-style summary**:

- Estimates **severity** and **priority** using heuristics:
  - Keywords like “urgent”, “immediately” → higher severity/priority.
  - Mentions of “school” or “hospital” → higher priority.
- Produces a short, structured text block stored with each issue and shown in:
  - Citizen dashboard (per issue).
  - Admin dashboard (per issue).
  - PDF report.

This function is designed so that you could later replace it with a **real ML/NLP service or LLM API** without changing the rest of the system.

---

### 8. PDF Report Generation

Implemented in `utils.py` using **ReportLab**:

- A4-sized, multi-page PDF.
- Sections:
  - Header: Government-style title.
  - Citizen details.
  - Location details.
  - Issue description.
  - AI analysis summary.
  - Status timeline.
  - Authority remarks.
  - Latest feedback.
  - Photo page: **before/after images** side-by-side (if files exist).
  - Footer: **“Digitally generated document – no manual signature required.”**

Each issue has a **Download PDF** button in the citizen dashboard which calls `/issue/<issue_id>/pdf`.

---

### 9. File Upload Handling

- Uploads are stored under:

  - `static/uploads/` (auto-created at app startup).

- Supported formats:
  - `.png`, `.jpg`, `.jpeg`, `.gif`

- Basic security measures:
  - Extension whitelist check (`ALLOWED_EXTENSIONS`).
  - Unique filenames prefixed with `before_` or `after_` and timestamp.

For a production deployment, you would additionally:

- Validate image content type more strictly.
- Consider storing files in cloud storage (S3, etc.).
- Limit file size and apply virus scanning.

---

### 10. Notes and Next Steps

- This is a **prototype** suitable for:
  - Academic projects.
  - Demos and POCs.
  - Starting point for a more production-ready system.
- To extend:
  - Add **user authentication** and role-based access (citizen vs. admin).
  - Integrate **real AI/ML** services for severity prediction.
  - Add **map integration** (e.g., showing issue locations on a map).
  - Build **REST APIs** for mobile apps.




