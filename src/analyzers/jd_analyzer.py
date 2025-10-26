"""
Job Description Analyzer - Extracts requirements from JD using AI
"""
from openai import OpenAI
from typing import Dict
import json
from src.config.settings import settings

class JDAnalyzer:
    """Analyze job descriptions and extract structured requirements"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.MODEL_JD_ANALYZER
        self.temperature = settings.TEMP_JD_ANALYZER
    
    def analyze_jd(self, jd_text: str) -> Dict:
        """
        Extract structured information from job description
        
        Returns:
        {
            'role_title': str,
            'required_skills': List[str],
            'preferred_skills': List[str],
            'required_experience_years': int,
            'required_qualifications': List[str],
            'key_responsibilities': List[str],
            'keywords': List[str],
            'industry': str,
            'job_type': str
        }
        """
        
        prompt = f"""Analyze this job description and extract structured information.

Job Description:
{jd_text}

Extract and return ONLY a valid JSON object with these fields:
- role_title: The job title
- required_skills: List of must-have technical and soft skills
- preferred_skills: List of nice-to-have skills
- required_experience_years: Minimum years of experience (number)
- required_qualifications: Degrees, certifications required
- key_responsibilities: Main job duties (top 5-7)
- keywords: Important keywords for ATS (15-20 keywords)
- industry: Industry/domain (e.g., Healthcare, Finance, Tech)
- job_type: Role category (e.g., Business Analyst, Product Owner, Scrum Master)

Return ONLY the JSON object, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert HR analyst who extracts structured data from job descriptions. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
