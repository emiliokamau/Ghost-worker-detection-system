"""
Generate sample data for testing
"""
import random
from datetime import datetime, timedelta
import uuid


FIRST_NAMES = [
    'John', 'Mary', 'James', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
    'Matthew', 'Betty', 'Anthony', 'Margaret', 'Donald', 'Sandra'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White'
]

DEPARTMENTS = [
    'Finance', 'Human Resources', 'IT', 'Operations', 'Marketing',
    'Sales', 'Customer Service', 'Administration', 'Legal', 'Procurement'
]

POSITIONS = [
    'Manager', 'Assistant', 'Director', 'Coordinator', 'Specialist',
    'Analyst', 'Officer', 'Supervisor', 'Executive', 'Administrator'
]

BENEFIT_TYPES = [
    'Health Insurance', 'Pension', 'Housing Allowance', 'Transport Allowance',
    'Education Grant', 'Medical Reimbursement', 'Annual Bonus'
]


def generate_national_id():
    """Generate a fake national ID"""
    return f"{random.randint(100000, 999999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def generate_phone():
    """Generate a fake phone number"""
    return f"+254{random.randint(700000000, 799999999)}"


def generate_email(name):
    """Generate email from name"""
    name_parts = name.lower().split()
    if len(name_parts) >= 2:
        return f"{name_parts[0]}.{name_parts[1]}@gov.ke"
    return f"{name_parts[0]}@gov.ke"


def generate_employee():
    """Generate a random employee"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    
    registration_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
    
    return {
        'digital_id': str(uuid.uuid4()),
        'name': name,
        'national_id': generate_national_id(),
        'department': random.choice(DEPARTMENTS),
        'position': random.choice(POSITIONS),
        'phone': generate_phone(),
        'email': generate_email(name),
        'registration_date': registration_date,
        'status': 'active'
    }


def generate_attendance_log(employee_id, start_date, num_days):
    """Generate attendance logs for an employee"""
    logs = []
    current_date = start_date
    
    for _ in range(num_days):
        # Skip some days randomly (weekends, absences)
        if random.random() > 0.3:  # 70% attendance rate
            # Random check-in time between 7 AM and 9 AM
            hour = random.randint(7, 9)
            minute = random.randint(0, 59)
            check_in = current_date.replace(hour=hour, minute=minute)
            
            logs.append({
                'employee_id': employee_id,
                'check_in_time': check_in,
                'verification_method': random.choice(['fingerprint', 'facial', 'id_card']),
                'confidence_score': random.uniform(85, 99),
                'location': random.choice(['Main Office', 'Branch A', 'Branch B']),
                'device_id': f"DEVICE-{random.randint(1, 5)}"
            })
        
        current_date += timedelta(days=1)
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=2)
    
    return logs


def generate_benefit_claim(employee_id):
    """Generate a benefit claim"""
    claim_date = datetime.utcnow() - timedelta(days=random.randint(1, 90))
    benefit_type = random.choice(BENEFIT_TYPES)
    
    # Generate amount based on benefit type
    amount_ranges = {
        'Health Insurance': (5000, 15000),
        'Pension': (10000, 30000),
        'Housing Allowance': (8000, 20000),
        'Transport Allowance': (3000, 8000),
        'Education Grant': (10000, 25000),
        'Medical Reimbursement': (2000, 10000),
        'Annual Bonus': (15000, 50000)
    }
    
    min_amt, max_amt = amount_ranges.get(benefit_type, (1000, 10000))
    amount = random.uniform(min_amt, max_amt)
    
    return {
        'employee_id': employee_id,
        'benefit_type': benefit_type,
        'amount': round(amount, 2),
        'claim_date': claim_date,
        'status': random.choice(['pending', 'approved', 'paid']),
        'verified_by_biometric': random.choice([True, False])
    }
