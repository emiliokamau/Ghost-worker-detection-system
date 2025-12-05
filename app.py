"""
Main Flask application for Biometric Verification System
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Employee, BiometricTemplate, AttendanceLog, DuplicateAlert, BenefitClaim, AdminUser
from datetime import datetime, timedelta
import os
import json
import uuid
import base64
import random
from werkzeug.utils import secure_filename

# Import utilities
from utils.biometric_matcher import (
    generate_biometric_hash, image_to_hash, detect_duplicate, verify_biometric
)
from utils.fraud_detection import (
    detect_ghost_workers, detect_duplicate_claims, detect_unusual_patterns, analyze_employee_risk
)
from utils.data_generator import generate_employee, generate_attendance_log, generate_benefit_claim

# Initialize Flask app
app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = 'super-secret-key-for-demo-only'  # Change for production
CORS(app, supports_credentials=True)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biometric_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/photos'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db.init_app(app)

# Initialize Login Manager
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'

# @login_manager.user_loader
# def load_user(user_id):
#     return AdminUser.query.get(int(user_id))

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('public', 'dashboard.html')


# ============= AUTHENTICATION ENDPOINTS =============

# @app.route('/api/login', methods=['POST'])
# def login():
#     """Admin login"""
#     data = request.json
#     username = data.get('username')
#     password = data.get('password')
# 
#     user = AdminUser.query.filter_by(username=username).first()
# 
#     if user and user.check_password(password):
#         login_user(user)
# ============= REGISTRATION ENDPOINTS =============

@app.route('/api/register', methods=['POST'])
# @login_required  # Uncomment to enforce login for registration
def register_employee():
    """Register a new employee with biometric data"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        # Check for existing national_id
        if data.get('national_id'):
            existing = Employee.query.filter_by(national_id=data['national_id']).first()
            if existing:
                return jsonify({'error': 'National ID already registered'}), 400
        
        # Generate digital ID
        digital_id = str(uuid.uuid4())
        
        # Process biometric data
        biometric_hash = None
        photo_path = None
        
        if data.get('photo_data'):
            # Save photo
            photo_data = data['photo_data']
            
            # Generate biometric template (returns JSON string of encoding)
            photo_hash = image_to_hash(photo_data)
            biometric_hash = photo_hash
            
            # Save photo file
            try:
                # Extract base64 data
                if ',' in photo_data:
                    photo_data = photo_data.split(',')[1]
                photo_bytes = base64.b64decode(photo_data)
                
                filename = f"{digital_id}.jpg"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'wb') as f:
                    f.write(photo_bytes)
                photo_path = filename
            except Exception as e:
                print(f"Error saving photo: {e}")
        
        # Check for duplicates
        existing_employees = Employee.query.filter_by(status='active').all()
        existing_data = []
        for emp in existing_employees:
            emp_data = {
                'id': emp.id,
                'name': emp.name,
                'national_id': emp.national_id,
                'biometric_hash': emp.biometric_hash
            }
            # Load photo data if exists (needed for deep comparison if hash isn't enough)
            if emp.photo_path:
                photo_file = os.path.join(app.config['UPLOAD_FOLDER'], emp.photo_path)
                if os.path.exists(photo_file):
                    with open(photo_file, 'rb') as f:
                        emp_data['photo_data'] = base64.b64encode(f.read()).decode()
            existing_data.append(emp_data)
        
        new_data = {
            'name': data['name'],
            'national_id': data.get('national_id'),
            'biometric_hash': biometric_hash,
            'photo_data': data.get('photo_data')
        }
        
        duplicates = detect_duplicate(new_data, existing_data)
        
        # Create employee record
        employee = Employee(
            digital_id=digital_id,
            name=data['name'],
            national_id=data.get('national_id'),
            department=data.get('department'),
            position=data.get('position'),
            phone=data.get('phone'),
            email=data.get('email'),
            photo_path=photo_path,
            biometric_hash=biometric_hash,
            created_by=data.get('created_by', 'system')
        )
        
        db.session.add(employee)
        db.session.flush()  # Get employee ID
        
        # Store biometric templates
        if data.get('photo_data'):
            template = BiometricTemplate(
                employee_id=employee.id,
                template_type='facial',
                template_data=json.dumps({'hash': photo_hash, 'photo_data': photo_hash}), # Store encoding
                quality_score=90.0
            )
            db.session.add(template)
        
        if data.get('fingerprint_data'):
            fingerprint_hash = generate_biometric_hash(data['fingerprint_data'])
            template = BiometricTemplate(
                employee_id=employee.id,
                template_type='fingerprint',
                template_data=json.dumps({'hash': fingerprint_hash}),
                quality_score=95.0
            )
            db.session.add(template)
        
        # Create duplicate alerts if found
        duplicate_alerts = []
        for dup in duplicates:
            if dup['similarity_score'] > 80:  # Threshold
                alert = DuplicateAlert(
                    employee_id_1=employee.id,
                    employee_id_2=dup['employee']['id'],
                    similarity_score=dup['similarity_score'],
                    matching_factors=json.dumps(dup['matching_factors'])
                )
                db.session.add(alert)
                duplicate_alerts.append({
                    'existing_employee': dup['employee']['name'],
                    'similarity_score': dup['similarity_score'],
                    'matching_factors': dup['matching_factors']
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'employee': employee.to_dict(),
            'duplicates_found': len(duplicate_alerts),
            'duplicate_alerts': duplicate_alerts
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= VERIFICATION ENDPOINTS =============

@app.route('/api/verify', methods=['POST'])
def verify_identity():
    """Verify employee identity using biometric data"""
    try:
        data = request.json
        
        employee_id = data.get('employee_id')
        verification_data = data.get('biometric_data')
        
        if not employee_id or not verification_data:
            return jsonify({'error': 'Employee ID and biometric data required'}), 400
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Get stored templates
        templates = BiometricTemplate.query.filter_by(employee_id=employee_id).all()
        
        verification_result = {'match': False, 'confidence': 0.0}
        
        for template in templates:
            template_data = json.loads(template.template_data)
            result = verify_biometric(verification_data, template_data)
            
            if result['confidence'] > verification_result['confidence']:
                verification_result = result
        
        return jsonify({
            'employee': employee.to_dict(),
            'verified': verification_result['match'],
            'confidence': verification_result['confidence']
        })
        
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-in', methods=['POST'])
def check_in():
    """Record employee attendance"""
    try:
        data = request.json
        
        employee_id = data.get('employee_id')
        verification_method = data.get('verification_method', 'facial')
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Verify biometric if provided
        confidence = 100.0
        if data.get('biometric_data'):
            verify_result = verify_identity()
            if hasattr(verify_result, 'json'):
                verify_data = verify_result.json
                confidence = verify_data.get('confidence', 100.0)
        
        # Create attendance log
        log = AttendanceLog(
            employee_id=employee_id,
            verification_method=verification_method,
            confidence_score=confidence,
            location=data.get('location', 'Main Office'),
            device_id=data.get('device_id', 'WEB-APP')
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'log': log.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Check-in error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= EMPLOYEE MANAGEMENT =============

@app.route('/api/employees', methods=['GET'])
# @login_required
def get_employees():
    """Get all employees"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status', 'active')
        
        query = Employee.query
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'employees': [emp.to_dict() for emp in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
        
    except Exception as e:
        print(f"Get employees error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/employees/<int:employee_id>', methods=['GET'])
# @login_required
def get_employee(employee_id):
    """Get employee details"""
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Get additional data
        attendance_count = AttendanceLog.query.filter_by(employee_id=employee_id).count()
        benefit_claims = BenefitClaim.query.filter_by(employee_id=employee_id).all()
        
        response = employee.to_dict()
        response['attendance_count'] = attendance_count
        response['benefit_claims'] = [claim.to_dict() for claim in benefit_claims]
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Get employee error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= DUPLICATE DETECTION =============

@app.route('/api/duplicates', methods=['GET'])
# @login_required
def get_duplicates():
    """Get all duplicate alerts"""
    try:
        status = request.args.get('status', 'pending')
        
        query = DuplicateAlert.query
        if status:
            query = query.filter_by(status=status)
        
        alerts = query.order_by(DuplicateAlert.similarity_score.desc()).all()
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts]
        })
        
    except Exception as e:
        print(f"Get duplicates error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/duplicates/<int:alert_id>/resolve', methods=['POST'])
# @login_required
def resolve_duplicate(alert_id):
    """Mark duplicate alert as resolved"""
    try:
        data = request.json
        alert = DuplicateAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        alert.status = data.get('status', 'resolved')
        alert.investigation_notes = data.get('notes')
        alert.resolved_by = data.get('resolved_by', 'admin')
        alert.resolved_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Resolve duplicate error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= FRAUD DETECTION =============

@app.route('/api/fraud/ghost-workers', methods=['GET'])
# @login_required
def get_ghost_workers():
    """Identify potential ghost workers"""
    try:
        days_threshold = request.args.get('days', 30, type=int)
        
        employees = Employee.query.filter_by(status='active').all()
        attendance_logs = AttendanceLog.query.all()
        
        ghosts = detect_ghost_workers(employees, attendance_logs, days_threshold)
        
        return jsonify({
            'ghost_workers': [{
                'employee': ghost['employee'].to_dict(),
                'reason': ghost['reason'],
                'days_since_registration': ghost.get('days_since_registration'),
                'days_since_attendance': ghost.get('days_since_attendance')
            } for ghost in ghosts]
        })
        
    except Exception as e:
        print(f"Ghost workers error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud/suspicious-claims', methods=['GET'])
# @login_required
def get_suspicious_claims():
    """Get suspicious benefit claims"""
    try:
        claims = BenefitClaim.query.all()
        suspicious = detect_duplicate_claims(claims)
        
        return jsonify({
            'suspicious_claims': [{
                'employee_id': item['employee_id'],
                'claims': [claim.to_dict() for claim in item['claims']],
                'time_difference_hours': item['time_difference_hours'],
                'reason': item['reason']
            } for item in suspicious]
        })
        
    except Exception as e:
        print(f"Suspicious claims error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= ANALYTICS =============

@app.route('/api/analytics/dashboard', methods=['GET'])
# @login_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_employees = Employee.query.filter_by(status='active').count()
        total_attendance = AttendanceLog.query.count()
        pending_duplicates = DuplicateAlert.query.filter_by(status='pending').count()
        total_claims = BenefitClaim.query.count()
        
       # Ghost workers
        employees = Employee.query.filter_by(status='active').all()
        attendance_logs = AttendanceLog.query.all()
        ghosts = detect_ghost_workers(employees, attendance_logs, 30)
        
        # Recent activity
        recent_attendance = AttendanceLog.query.order_by(
            AttendanceLog.check_in_time.desc()
        ).limit(10).all()
        
        recent_registrations = Employee.query.order_by(
            Employee.registration_date.desc()
        ).limit(10).all()
        
        return jsonify({
            'total_employees': total_employees,
            'total_attendance': total_attendance,
            'pending_duplicates': pending_duplicates,
            'total_claims': total_claims,
            'ghost_workers_count': len(ghosts),
            'recent_attendance': [log.to_dict() for log in recent_attendance],
            'recent_registrations': [emp.to_dict() for emp in recent_registrations]
        })
        
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= SAMPLE DATA GENERATION =============

@app.route('/api/generate-sample-data', methods=['POST'])
def create_sample_data():
    """Generate sample data for testing"""
    try:
        num_employees = request.json.get('num_employees', 10)
        
        created_employees = []
        
        for _ in range(num_employees):
            emp_data = generate_employee()
            
            employee = Employee(**emp_data)
            db.session.add(employee)
            db.session.flush()
            
            # Generate attendance logs
            logs_data = generate_attendance_log(
                employee.id,
                datetime.utcnow() - timedelta(days=60),
                40
            )
            for log_data in logs_data:
                log = AttendanceLog(**log_data)
                db.session.add(log)
            
            # Generate some benefit claims
            for _ in range(random.randint(0, 3)):
                claim_data = generate_benefit_claim(employee.id)
                claim = BenefitClaim(**claim_data)
                db.session.add(claim)
            
            created_employees.append(employee.to_dict())
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'employees_created': len(created_employees),
            'employees': created_employees
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Sample data error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= INITIALIZE DATABASE =============

@app.route('/api/init-db', methods=['POST'])
def init_database():
    """Initialize database tables"""
    try:
        db.create_all()
        
        # # Create default admin if not exists
        # if not AdminUser.query.filter_by(username='admin').first():
        #     admin = AdminUser(username='admin')
        #     admin.set_password('admin123')
        #     db.session.add(admin)
        #     db.session.commit()
            
        return jsonify({'success': True, 'message': 'Database initialized'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not AdminUser.query.filter_by(username='admin').first():
            print("Creating default admin user...")
            admin = AdminUser(username='admin')
            admin.set_password(password='admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created successfully.")
            
    app.run(debug=True, host='0.0.0.0', port=5000)
