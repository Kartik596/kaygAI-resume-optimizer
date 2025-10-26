"""
Resume Matcher - Compares sanitized resume against JD requirements
"""
from openai import OpenAI
from typing import Dict, Any
import json
from src.config.settings import settings

class ResumeMatcher:
    """Match resume against job description and provide gap analysis"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.MODEL_RESUME_MATCHER
        self.temperature = settings.TEMP_MATCHER
    
    def calculate_match(
        self, 
        sanitized_resume: Dict[str, Any], 
        jd_requirements: Dict[str, Any]
    ) -> Dict:
        """
        Compare resume vs JD and return match analysis
        
        Returns comprehensive match analysis with scores and suggestions
        """
        
        prompt = f"""You are an expert ATS system and resume reviewer. Compare this resume against job requirements.

**SANITIZED RESUME** (PII removed):
{json.dumps(sanitized_resume, indent=2)}

**JOB REQUIREMENTS**:
{json.dumps(jd_requirements, indent=2)}

Analyze the match and return ONLY a valid JSON object with these fields:

1. overall_match_score: Overall fit score (0-100)

2. skills_match:
   - matched: Skills from resume that match JD requirements
   - missing: Required skills not found in resume
   - score: Skills match score (0-100)

3. experience_match:
   - has_years: Years of relevant experience in resume
   - required_years: Years required by JD
   - meets_requirement: true/false
   - score: Experience match score (0-100)

4. keyword_coverage:
   - matched_keywords: JD keywords found in resume
   - missing_keywords: JD keywords NOT in resume
   - score: Keyword match score (0-100)

5. strengths: List of 3-5 resume strengths for this role

6. gaps: List of 3-5 areas where resume falls short

7. improvement_suggestions: 5-7 specific, actionable suggestions to improve resume
   (DO NOT include any PII or specific company names in suggestions)

Return ONLY the JSON object, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert ATS analyzer and career coach. Provide detailed, actionable feedback. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
