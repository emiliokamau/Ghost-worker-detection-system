"""
Database models for the Biometric Verification System
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class AdminUser(UserMixin, db.Model):
    """Admin user model"""
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    """Employee/Beneficiary model"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    digital_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    national_id = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    photo_path = db.Column(db.String(255))
    biometric_hash = db.Column(db.Text)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    created_by = db.Column(db.String(100))
    
    # Relationships
    biometric_templates = db.relationship('BiometricTemplate', backref='employee', lazy=True, cascade='all, delete-orphan')
    attendance_logs = db.relationship('AttendanceLog', backref='employee', lazy=True, cascade='all, delete-orphan')
    benefit_claims = db.relationship('BenefitClaim', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'digital_id': self.digital_id,
            'name': self.name,
            'national_id': self.national_id,
            'department': self.department,
            'position': self.position,
            'phone': self.phone,
            'email': self.email,
            'photo_path': self.photo_path,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'status': self.status
        }


class BiometricTemplate(db.Model):
    """Biometric template storage"""
    __tablename__ = 'biometric_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    template_type = db.Column(db.String(20), nullable=False)  # 'fingerprint' or 'facial'
    template_data = db.Column(db.Text, nullable=False)  # JSON string
    quality_score = db.Column(db.Float)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'template_type': self.template_type,
            'quality_score': self.quality_score,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }


class AttendanceLog(db.Model):
    """Attendance tracking"""
    __tablename__ = 'attendance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    verification_method = db.Column(db.String(20))  # 'fingerprint', 'facial', 'id_card'
    confidence_score = db.Column(db.Float)
    location = db.Column(db.String(200))
    device_id = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'verification_method': self.verification_method,
            'confidence_score': self.confidence_score,
            'location': self.location
        }


class DuplicateAlert(db.Model):
    """Duplicate detection alerts"""
    __tablename__ = 'duplicate_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id_1 = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    employee_id_2 = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    matching_factors = db.Column(db.Text)  # JSON array of what matched
    alert_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'resolved', 'confirmed_duplicate'
    investigation_notes = db.Column(db.Text)
    resolved_by = db.Column(db.String(100))
    resolved_date = db.Column(db.DateTime)
    
    # Relationships
    employee1 = db.relationship('Employee', foreign_keys=[employee_id_1])
    employee2 = db.relationship('Employee', foreign_keys=[employee_id_2])
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id_1': self.employee_id_1,
            'employee_id_2': self.employee_id_2,
            'employee_1_name': self.employee1.name if self.employee1 else None,
            'employee_2_name': self.employee2.name if self.employee2 else None,
            'similarity_score': self.similarity_score,
            'matching_factors': self.matching_factors,
            'alert_date': self.alert_date.isoformat() if self.alert_date else None,
            'status': self.status,
            'investigation_notes': self.investigation_notes
        }


class BenefitClaim(db.Model):
    """Benefit claims tracking"""
    __tablename__ = 'benefit_claims'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    benefit_type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float)
    claim_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    verified_by_biometric = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'benefit_type': self.benefit_type,
            'amount': self.amount,
            'claim_date': self.claim_date.isoformat() if self.claim_date else None,
            'status': self.status,
            'verified_by_biometric': self.verified_by_biometric,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None
        }
