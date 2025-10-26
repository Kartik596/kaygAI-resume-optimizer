"""
PII Sanitizer - Removes sensitive personal information before AI processing
"""
import json
import copy
from typing import Dict, Any

class PIISanitizer:
    """Sanitize resume JSON by removing PII before sending to AI"""
    
    @staticmethod
    def sanitize_resume(resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove PII from resume data
        
        Removes:
        - Name, email, phone, location, LinkedIn
        - Company names (keeps role titles and achievements)
        - Education institution names (keeps degrees and years)
        
        Keeps:
        - Profile summary
        - Skills
        - Role titles and achievements (anonymized companies)
        - Years of experience
        - Certifications (names only, not org details)
        """
        sanitized = copy.deepcopy(resume_data)
        
        # Remove personal info
        if 'personal_info' in sanitized:
            sanitized['personal_info'] = {
                'name': '[REDACTED]',
                'contact': {
                    'email': '[REDACTED]',
                    'phone': '[REDACTED]',
                    'location': '[REDACTED]',
                    'linkedin': '[REDACTED]'
                }
            }
        
        # Anonymize company names in experience
        if 'experience' in sanitized:
            for i, exp in enumerate(sanitized['experience']):
                exp['company'] = f'Company_{chr(65+i)}'  # Company_A, Company_B, etc.
                if 'location' in exp:
                    exp['location'] = '[LOCATION]'
        
        # Anonymize education institutions
        if 'education' in sanitized:
            for i, edu in enumerate(sanitized['education']):
                edu['institution'] = f'University_{chr(65+i)}'
        
        # Keep: profile, skills, achievements, certifications (name only)
        return sanitized
    
    @staticmethod
    def get_sanitized_json_string(resume_data: Dict[str, Any]) -> str:
        """Return sanitized resume as formatted JSON string"""
        sanitized = PIISanitizer.sanitize_resume(resume_data)
        return json.dumps(sanitized, indent=2)
