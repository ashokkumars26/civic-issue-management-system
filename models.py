from datetime import datetime
from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    issues = db.relationship('Issue', backref='user', lazy=True)


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_type = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    area = db.Column(db.String(120), nullable=False)
    street = db.Column(db.String(255), nullable=True)
    landmark = db.Column(db.String(255), nullable=True)
    before_image = db.Column(db.String(255), nullable=True)
    after_image = db.Column(db.String(255), nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    current_status = db.Column(db.String(50), default='Pending')
    authority_remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    status_logs = db.relationship(
        'IssueStatusLog',
        backref='issue',
        lazy=True,
        cascade="all, delete-orphan"
    )
    feedbacks = db.relationship(
        'Feedback',
        backref='issue',
        lazy=True,
        cascade="all, delete-orphan"
    )


class IssueStatusLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


