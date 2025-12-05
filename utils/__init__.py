"""
Utility package initialization
"""
from .biometric_matcher import (
    generate_biometric_hash,
    image_to_hash,
    calculate_image_similarity,
    detect_duplicate,
    verify_biometric
)
from .fraud_detection import (
    detect_ghost_workers,
    detect_duplicate_claims,
    detect_unusual_patterns,
    analyze_employee_risk
)
from .data_generator import (
    generate_employee,
    generate_attendance_log,
    generate_benefit_claim
)

__all__ = [
    'generate_biometric_hash',
    'image_to_hash',
    'calculate_image_similarity',
    'detect_duplicate',
    'verify_biometric',
    'detect_ghost_workers',
    'detect_duplicate_claims',
    'detect_unusual_patterns',
    'analyze_employee_risk',
    'generate_employee',
    'generate_attendance_log',
    'generate_benefit_claim'
]
