"""
Biometric matching utilities for duplicate detection
"""
import hashlib
import json
from PIL import Image
import io
import base64
import numpy as np

# Try to import face_recognition, fallback if not installed
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition library not found. Using simulation mode.")

def generate_biometric_hash(data_string):
    """Generate a secure hash for biometric data"""
    return hashlib.sha256(data_string.encode()).hexdigest()

def image_to_hash(image_data):
    """
    Convert image to a biometric template
    Returns: JSON string of encoding or hash
    """
    try:
        if isinstance(image_data, str):
            # Base64 encoded image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        if FACE_RECOGNITION_AVAILABLE:
            # Load image for face_recognition
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            
            # Get face encodings
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) > 0:
                # Return the first face encoding as a list (JSON serializable)
                return json.dumps(encodings[0].tolist())
            else:
                print("No face detected in image")
                return None
        else:
            # Fallback to simulation hash
            img = Image.open(io.BytesIO(image_bytes))
            img = img.resize((64, 64)).convert('L')
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            bits = ''.join('1' if p > avg else '0' for p in pixels)
            return hashlib.sha256(bits.encode()).hexdigest()
            
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def calculate_image_similarity(template1, template2):
    """
    Calculate similarity between two biometric templates
    Returns: Percentage (0-100)
    """
    try:
        if not template1 or not template2:
            return 0.0
            
        if FACE_RECOGNITION_AVAILABLE:
            try:
                # Parse encodings
                enc1 = np.array(json.loads(template1))
                enc2 = np.array(json.loads(template2))
                
                # Calculate Euclidean distance
                # face_recognition uses distance < 0.6 as a match
                distance = np.linalg.norm(enc1 - enc2)
                
                # Convert distance to similarity percentage
                # 0.0 distance = 100% match
                # 0.6 distance = ~85% match (threshold)
                # 1.0 distance = 0% match
                similarity = max(0, (1.0 - distance) * 100)
                
                return similarity
            except:
                # Fallback if templates aren't valid JSON arrays (legacy data)
                return 0.0
        else:
            # Simulation: simple string comparison of hashes
            if template1 == template2:
                return 100.0
            return 0.0
            
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

def calculate_name_similarity(name1, name2):
    """
    Calculate name similarity using Levenshtein distance
    Returns similarity percentage
    """
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    
    if name1 == name2:
        return 100.0
    
    # Simple Levenshtein distance
    len1, len2 = len(name1), len(name2)
    if len1 == 0 or len2 == 0:
        return 0.0
    
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if name1[i-1] == name2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )
    
    distance = matrix[len1][len2]
    max_len = max(len1, len2)
    similarity = ((max_len - distance) / max_len) * 100
    
    return similarity

def detect_duplicate(new_employee_data, existing_employees):
    """
    Detect potential duplicates by comparing with existing employees
    """
    duplicates = []
    
    for existing in existing_employees:
        matching_factors = []
        scores = []
        
        # Check national ID (exact match)
        if new_employee_data.get('national_id') and existing.get('national_id'):
            if new_employee_data['national_id'] == existing['national_id']:
                matching_factors.append('national_id')
                scores.append(100.0)
        
        # Check name similarity
        if new_employee_data.get('name') and existing.get('name'):
            name_sim = calculate_name_similarity(new_employee_data['name'], existing['name'])
            if name_sim > 80:  # 80% threshold
                matching_factors.append('name')
                scores.append(name_sim)
        
        # Check biometric similarity
        if new_employee_data.get('biometric_hash') and existing.get('biometric_hash'):
            bio_sim = calculate_image_similarity(
                new_employee_data['biometric_hash'], 
                existing['biometric_hash']
            )
            
            # Threshold depends on method
            threshold = 85.0 if FACE_RECOGNITION_AVAILABLE else 99.0
            
            if bio_sim > threshold:
                matching_factors.append('facial_recognition')
                scores.append(bio_sim)
        
        # If any factors matched, add to duplicates
        if matching_factors:
            overall_score = sum(scores) / len(scores)
            duplicates.append({
                'employee': existing,
                'similarity_score': overall_score,
                'matching_factors': matching_factors
            })
    
    # Sort by similarity score (highest first)
    duplicates.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return duplicates

def verify_biometric(submitted_data, stored_template):
    """
    Verify submitted biometric data against stored template
    """
    try:
        if submitted_data.get('type') == 'fingerprint':
            # Compare fingerprint hashes
            if submitted_data.get('hash') == stored_template.get('hash'):
                return {'match': True, 'confidence': 95.0}
            else:
                return {'match': False, 'confidence': 0.0}
        
        elif submitted_data.get('type') == 'facial':
            # Compare facial features
            if submitted_data.get('photo_data') and stored_template.get('hash'):
                # Convert submitted photo to template
                submitted_template = image_to_hash(submitted_data['photo_data'])
                
                if submitted_template:
                    similarity = calculate_image_similarity(
                        submitted_template,
                        stored_template['hash']
                    )
                    
                    threshold = 85.0 if FACE_RECOGNITION_AVAILABLE else 99.0
                    match = similarity > threshold
                    
                    return {'match': match, 'confidence': similarity}
        
        return {'match': False, 'confidence': 0.0}
    except Exception as e:
        print(f"Error verifying biometric: {e}")
        return {'match': False, 'confidence': 0.0}
