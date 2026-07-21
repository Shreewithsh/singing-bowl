"""
Singing Bowl Export Desk
Database Models - SQLAlchemy ORM
"""
from datetime import datetime
from services.database import db


class Lead(db.Model):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(255), nullable=True)
    owner_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(500), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    score = db.Column(db.Integer, default=0)
    contacted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_contacted = db.Column(db.DateTime, nullable=True)
    email_status = db.Column(db.String(50), default='pending')  # pending, sent, failed, skipped

    def to_dict(self):
        return {
            'id': self.id,
            'business_name': self.business_name or '',
            'owner_name': self.owner_name or '',
            'email': self.email,
            'phone': self.phone or '',
            'country': self.country or '',
            'website': self.website or '',
            'source_url': self.source_url or '',
            'score': self.score,
            'contacted': self.contacted,
            'email_status': self.email_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'last_contacted': self.last_contacted.strftime('%Y-%m-%d %H:%M') if self.last_contacted else ''
        }


class Campaign(db.Model):
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    total_sent = db.Column(db.Integer, default=0)
    total_failed = db.Column(db.Integer, default=0)
    total_skipped = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='draft')  # draft, running, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'total_sent': self.total_sent,
            'total_failed': self.total_failed,
            'total_skipped': self.total_skipped,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else ''
        }


class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(key, default=None):
        setting = Settings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = Settings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
