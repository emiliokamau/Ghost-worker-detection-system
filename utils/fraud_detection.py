"""
Fraud detection utilities
"""
from datetime import datetime, timedelta
from collections import defaultdict


def detect_ghost_workers(employees, attendance_logs, days_threshold=30):
    """
    Identify potential ghost workers (registered but never attend)
    
    Args:
        employees: list of employee records
        attendance_logs: list of attendance records
        days_threshold: number of days of no attendance to flag as ghost
    
    Returns:
        list of potential ghost workers
    """
    ghost_workers = []
    
    # Create attendance map
    attendance_map = defaultdict(list)
    for log in attendance_logs:
        attendance_map[log.employee_id].append(log)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
    
    for employee in employees:
        if employee.status != 'active':
            continue
        
        attendances = attendance_map.get(employee.id, [])
        
        # Check if registered before cutoff
        if employee.registration_date < cutoff_date:
            # Check if no attendance or old attendance
            if not attendances:
                ghost_workers.append({
                    'employee': employee,
                    'reason': 'No attendance records',
                    'days_since_registration': (datetime.utcnow() - employee.registration_date).days
                })
            else:
                # Check last attendance
                last_attendance = max(attendances, key=lambda x: x.check_in_time)
                if last_attendance.check_in_time < cutoff_date:
                    ghost_workers.append({
                        'employee': employee,
                        'reason': f'No attendance in {days_threshold} days',
                        'last_attendance': last_attendance.check_in_time,
                        'days_since_attendance': (datetime.utcnow() - last_attendance.check_in_time).days
                    })
    
    return ghost_workers


def detect_duplicate_claims(benefit_claims, time_window_hours=24):
    """
    Detect multiple benefit claims in short time period
    
    Args:
        benefit_claims: list of benefit claim records
        time_window_hours: time window to check for duplicates
    
    Returns:
        list of suspicious claim patterns
    """
    suspicious_claims = []
    
    # Group claims by employee
    claims_by_employee = defaultdict(list)
    for claim in benefit_claims:
        claims_by_employee[claim.employee_id].append(claim)
    
    for employee_id, claims in claims_by_employee.items():
        # Sort by date
        claims = sorted(claims, key=lambda x: x.claim_date)
        
        # Check for claims in short time windows
        for i in range(len(claims) - 1):
            time_diff = claims[i + 1].claim_date - claims[i].claim_date
            hours_diff = time_diff.total_seconds() / 3600
            
            if hours_diff < time_window_hours:
                suspicious_claims.append({
                    'employee_id': employee_id,
                    'claims': [claims[i], claims[i + 1]],
                    'time_difference_hours': hours_diff,
                    'reason': f'Multiple claims within {time_window_hours} hours'
                })
    
    return suspicious_claims


def detect_unusual_patterns(attendance_logs):
    """
    Detect unusual attendance patterns
    
    Returns:
        list of unusual patterns (weekend check-ins, late night, etc.)
    """
    unusual_patterns = []
    
    for log in attendance_logs:
        check_in = log.check_in_time
        
        # Check for weekend attendance (might be unusual for some organizations)
        if check_in.weekday() >= 5:  # Saturday = 5, Sunday = 6
            unusual_patterns.append({
                'type': 'weekend_checkin',
                'log': log,
                'reason': 'Check-in on weekend'
            })
        
        # Check for late night/early morning (midnight to 5 AM)
        if check_in.hour < 5:
            unusual_patterns.append({
                'type': 'unusual_hour',
                'log': log,
                'reason': f'Check-in at unusual hour: {check_in.hour}:00'
            })
        
        # Check for very low confidence scores
        if log.confidence_score and log. confidence_score < 70:
            unusual_patterns.append({
                'type': 'low_confidence',
                'log': log,
                'reason': f'Low verification confidence: {log.confidence_score}%'
            })
    
    return unusual_patterns


def analyze_employee_risk(employee, attendance_logs, benefit_claims, duplicates):
    """
    Calculate overall fraud risk score for an employee
    
    Returns:
        dict with risk_score (0-100) and risk_factors
    """
    risk_score = 0
    risk_factors = []
    
    # Check for duplicate alerts
    employee_duplicates = [d for d in duplicates if 
                          d.employee_id_1 == employee.id or d.employee_id_2 == employee.id]
    if employee_duplicates:
        pending_duplicates = [d for d in employee_duplicates if d.status == 'pending']
        if pending_duplicates:
            risk_score += 40
            risk_factors.append(f'{len(pending_duplicates)} pending duplicate alerts')
    
    # Check attendance patterns
    employee_attendance = [log for log in attendance_logs if log.employee_id == employee.id]
    if len(employee_attendance) == 0 and employee.status == 'active':
        days_since_reg = (datetime.utcnow() - employee.registration_date).days
        if days_since_reg > 7:
            risk_score += 30
            risk_factors.append(f'No attendance in {days_since_reg} days')
    
    # Check benefit claims
    employee_claims = [claim for claim in benefit_claims if claim.employee_id == employee.id]
    unverified_claims = [c for c in employee_claims if not c.verified_by_biometric]
    if len(unverified_claims) > 0:
        risk_score += 20
        risk_factors.append(f'{len(unverified_claims)} unverified benefit claims')
    
    # Check for multiple claims
    if len(employee_claims) > 5:
        risk_score += 10
        risk_factors.append(f'High number of benefit claims ({len(employee_claims)})')
    
    risk_level = 'low'
    if risk_score >= 70:
        risk_level = 'critical'
    elif risk_score >= 40:
        risk_level = 'high'
    elif risk_score >= 20:
        risk_level = 'medium'
    
    return {
        'employee_id': employee.id,
        'risk_score': min(100, risk_score),
        'risk_level': risk_level,
        'risk_factors': risk_factors
    }
