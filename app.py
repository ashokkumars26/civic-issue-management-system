from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_mail import Message
from datetime import datetime
import os
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///civic_issues.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration placeholders (to be configured in README)
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'you@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
app.config['MAIL_DEFAULT_SENDER'] = (' Civic Issue Management System', 'you@example.com')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

from extensions import db, mail  # noqa: E402
db.init_app(app)
mail.init_app(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


from models import User, Issue, IssueStatusLog, Feedback  # noqa: E402
from utils import generate_issue_pdf, ai_analyze_issue  # noqa: E402


CHENNAI_AREAS = [
    "T. Nagar", "Adyar", "Anna Nagar", "Velachery", "Tambaram",
    "Poonamallee", "Mylapore", "Kodambakkam", "Nungambakkam", "Guindy",
    "Perambur", "Royapettah", "Chromepet", "Thiruvanmiyur", "Porur",
    "Saidapet", "Ambattur", "Washermanpet", "Besant Nagar"
]

ISSUE_TYPES = [
    "Potholes / Road Damage",
    "Garbage / Waste Management",
    "Street Light Not Working",
    "Water Logging / Drainage",
    "Illegal Parking / Encroachment",
    "Public Toilet Maintenance",
    "Tree Fall / Pruning Required",
    "Water Supply Issue",
    "Noise Pollution",
    "Construction Debris",
    "Other"
]


@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not username or not password or not role:
            flash('All fields are required.', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username, role=role).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username, password, or role.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    # For simplicity, all issues are shown as if for a single demo user
    issues = Issue.query.order_by(Issue.created_at.desc()).all()
    return render_template(
        'user_dashboard.html',
        issues=issues,
        areas=CHENNAI_AREAS,
        issue_types=ISSUE_TYPES
    )


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please log in as an admin to access this page.', 'error')
        return redirect(url_for('login'))

    status_filter = request.args.get('status')
    query = Issue.query
    if status_filter:
        query = query.filter_by(current_status=status_filter)
    issues = query.order_by(Issue.created_at.desc()).all()

    total = Issue.query.count()
    pending = Issue.query.filter_by(current_status='Pending').count()
    resolved = Issue.query.filter_by(current_status='Resolved').count()

    return render_template(
        'admin_dashboard.html',
        issues=issues,
        total=total,
        pending=pending,
        resolved=resolved
    )


@app.route('/issue/report', methods=['POST'])
def report_issue():
    if 'user_id' not in session:
        flash('Please log in to report issues.', 'error')
        return redirect(url_for('login'))

    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    issue_type = request.form.get('issue_type')
    issue_description = request.form.get('issue_description')
    area = request.form.get('area')
    street = request.form.get('street')
    landmark = request.form.get('landmark')

    if not issue_description or not area or not issue_type:
        flash('Please fill in all mandatory fields.', 'error')
        return redirect(url_for('user_dashboard'))

    user = User.query.get(session['user_id'])
    # Update user details if provided
    if name:
        user.name = name
    if email:
        user.email = email
    if phone:
        user.phone = phone

    before_image_path = None
    file = request.files.get('before_image')
    if file and file.filename and allowed_file(file.filename):
        filename = f"before_{datetime.utcnow().timestamp()}_{file.filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        before_image_path = save_path

    ai_summary = ai_analyze_issue(issue_type, issue_description)

    issue = Issue(
        user_id=user.id,
        issue_type=issue_type,
        description=issue_description,
        area=area,
        street=street,
        landmark=landmark,
        before_image=before_image_path,
        ai_summary=ai_summary,
        current_status='Pending'
    )
    db.session.add(issue)
    db.session.flush()

    status_log = IssueStatusLog(
        issue_id=issue.id,
        status='Pending',
        remarks='Issue reported by citizen.'
    )
    db.session.add(status_log)
    db.session.commit()

    try:
        if email:
            msg = Message(
                subject=f"Issue #{issue.id} Submitted - Chennai CivicCare AI",
                recipients=[email]
            )
            msg.body = (
                f"Dear {name or 'Citizen'},\n\n"
                f"Your issue (ID: {issue.id}) has been submitted successfully.\n"
                f"Issue Type: {issue.issue_type}\n"
                f"Location: {issue.area}, {issue.street} - {issue.landmark}\n\n"
                "You will receive updates as the status changes.\n\n"
                "Regards,\nChennai CivicCare AI"
            )
            mail.send(msg)
    except Exception:
        # Fail silently in demo mode
        pass

    flash('Issue reported successfully!', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/admin/issue/<int:issue_id>/update', methods=['POST'])
def update_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    new_status = request.form.get('status')
    remarks = request.form.get('remarks')

    after_image_path = issue.after_image
    file = request.files.get('after_image')
    if file and file.filename and allowed_file(file.filename):
        filename = f"after_{datetime.utcnow().timestamp()}_{file.filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        after_image_path = save_path

    if new_status:
        issue.current_status = new_status
    if remarks:
        issue.authority_remarks = remarks
    issue.after_image = after_image_path

    log = IssueStatusLog(
        issue_id=issue.id,
        status=new_status or issue.current_status,
        remarks=remarks or ''
    )
    db.session.add(log)
    db.session.commit()

    try:
        if issue.user and issue.user.email:
            msg = Message(
                subject=f"Issue #{issue.id} Status Updated - Chennai CivicCare AI",
                recipients=[issue.user.email]
            )
            msg.body = (
                f"Dear {issue.user.name or 'Citizen'},\n\n"
                f"The status of your issue (ID: {issue.id}) has been updated to: {issue.current_status}.\n"
                f"Remarks: {remarks or 'No additional remarks.'}\n\n"
                "Regards,\nChennai CivicCare AI"
            )
            mail.send(msg)
    except Exception:
        pass

    flash('Issue updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/issue/<int:issue_id>/feedback', methods=['POST'])
def submit_feedback(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    rating = int(request.form.get('rating', 0))
    comments = request.form.get('comments')

    feedback = Feedback(
        issue_id=issue.id,
        rating=rating,
        comments=comments
    )
    db.session.add(feedback)
    db.session.commit()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/issue/<int:issue_id>/pdf')
def download_issue_pdf(issue_id):
    print(f"PDF download requested for issue {issue_id}")
    if 'user_id' not in session:
        print("No user in session")
        flash('Please log in to download reports.', 'error')
        return redirect(url_for('login'))
    issue = Issue.query.get_or_404(issue_id)
    print(f"Issue found: {issue.id}")
    # Allow download if user is admin or the issue belongs to the user (but since all issues are shown, allow for now)
    try:
        pdf_bytes = generate_issue_pdf(issue)
        print(f"PDF generated, size: {len(pdf_bytes.getvalue())} bytes")
        pdf_bytes.seek(0)
        return send_file(
            pdf_bytes,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'issue_{issue_id}_report.pdf'
        )
    except Exception as e:
        print(f"Error generating PDF: {e}")
        flash('Error generating PDF report.', 'error')
        return redirect(url_for('user_dashboard'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if user is logged in as admin to allow role selection
    can_register_admin = 'user_id' in session and session.get('role') == 'admin'

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'user')  # Default to user if not specified
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        if not username or not password or not confirm_password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        # Only admins can register admin accounts
        if role == 'admin' and not can_register_admin:
            flash('Only administrators can register admin accounts.', 'error')
            return redirect(url_for('register'))

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password_hash=hashed_password,
            role=role,
            name=name,
            email=email,
            phone=phone
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', can_register_admin=can_register_admin)


def create_sample_users():
    """Create sample users and a sample issue if they don't exist"""
    # Create admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            name='System Administrator',
            email='admin@civiccare.com'
        )
        db.session.add(admin_user)

    # Create regular user
    regular_user = User.query.filter_by(username='user').first()
    if not regular_user:
        regular_user = User(
            username='user',
            password_hash=generate_password_hash('password'),
            role='user',
            name='Demo User',
            email='user@civiccare.com'
        )
        db.session.add(regular_user)

    # Create a sample issue if none exist
    if Issue.query.count() == 0 and regular_user:
        sample_issue = Issue(
            user_id=regular_user.id,
            issue_type='Potholes / Road Damage',
            description='Large pothole on the main road causing traffic issues.',
            area='T. Nagar',
            street='Anna Salai',
            landmark='Near T. Nagar Bus Stand',
            ai_summary=ai_analyze_issue('Potholes / Road Damage', 'Large pothole on the main road causing traffic issues.'),
            current_status='Pending'
        )
        db.session.add(sample_issue)
        db.session.flush()

        status_log = IssueStatusLog(
            issue_id=sample_issue.id,
            status='Pending',
            remarks='Sample issue created for demo.'
        )
        db.session.add(status_log)

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_users()
    app.run(debug=True)


