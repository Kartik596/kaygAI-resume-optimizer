"""
Smart PDF Resume Parser - FINAL VERSION
Complete extraction with proper skills handling
"""
import json
import re
from typing import Dict, Any
import PyPDF2
import pdfplumber
from openai import OpenAI
from src.config.settings import settings


class PDFResumeParser:
    """Production-ready parser"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4.1-nano"
    
    def extract_text_and_links_from_pdf(self, pdf_file) -> tuple:
        """Extract text and hyperlinks"""
        text = ""
        links = []
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    if hasattr(page, 'annots') and page.annots:
                        for annot in page.annots:
                            if 'uri' in annot:
                                links.append(annot['uri'])
            
            if not text:
                pdf_file.seek(0)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip(), links
            
        except Exception as e:
            raise ValueError(f"Failed to extract: {str(e)}")
    
    def extract_pii_locally(self, text: str, links: list) -> Dict[str, str]:
        """Extract PII locally"""
        pii = {"name": "", "email": "", "phone": "", "linkedin": "", "location": ""}
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            pii["email"] = email_match.group()
        
        # Phone
        phone_patterns = [
            r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                pii["phone"] = phone_match.group()
                break
        
        # LinkedIn - just ID
        for link in links:
            if 'linkedin.com/in/' in link:
                match = re.search(r'linkedin\.com/in/([\w-]+)', link)
                if match:
                    pii["linkedin"] = match.group(1)
                    break
        
        if not pii["linkedin"]:
            linkedin_patterns = [
                r'(?:https?://)?(?:www\.)?linkedin\.com/in/([\w-]+)',
                r'linkedin[:\s]+([\w-]+)',
            ]
            for pattern in linkedin_patterns:
                linkedin_match = re.search(pattern, text, re.IGNORECASE)
                if linkedin_match and linkedin_match.groups():
                    pii["linkedin"] = linkedin_match.group(1)
                    break
        
        # Name
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:10]:
            if '@' in line or 'http' in line.lower() or any(char.isdigit() for char in line):
                continue
            words = line.split()
            if 2 <= len(words) <= 5 and sum(1 for w in words if w[0].isupper()) >= len(words) - 1:
                pii["name"] = line
                break
        
        # Location
        location_patterns = [
            r'\b[A-Z][a-z]+/[A-Z]{2,}(?:\s*,\s*[A-Z][a-z]+)?\b',
            r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b',
            r'Location[:\s]+([A-Z][A-Za-z/\s,]+)',
        ]
        
        for pattern in location_patterns:
            location_match = re.search(pattern, text)
            if location_match:
                if location_match.groups():
                    pii["location"] = location_match.group(1).strip()
                else:
                    pii["location"] = location_match.group().strip()
                
                if len(pii["location"]) > 50:
                    pii["location"] = pii["location"][:50]
                break
        
        return pii
    
    def sanitize_text(self, text: str, pii: Dict[str, str]) -> str:
        """Remove PII"""
        sanitized = text
        for value in pii.values():
            if value:
                sanitized = sanitized.replace(value, "[REDACTED]")
        return sanitized
    
    def parse_sanitized_resume(self, sanitized_text: str) -> Dict[str, Any]:
        """Parse with COMPLETE extraction - FOCUS ON SKILLS"""
        
        prompt = f"""
You are a resume parser. Extract EVERY detail.

Resume Text:
{sanitized_text}

Return JSON:

{{
  "title": "Most recent job title",
  "profile": "Complete professional summary",
  "skills": {{
    // CRITICAL: Find the SKILLS section in the resume
    // Look for sections like "Tools & Technologies", "Business Analysis", "Soft Skills"
    // Extract EVERY skill listed
    // Example structure:
    // "tools_and_technologies": ["Jira", "Azure DevOps", "Figma", "Balsamiq", "Miro", "MS Visio", "MongoDB", "Selenium", "Python", "PlantUML", "Proto.io", "Visual Paradigm", "ChatGPT"],
    // "business_analysis": ["Requirement Elicitation", "Wireframing", "Process Modeling", "Story Mapping", "Workflow Design", "Data Analysis", "Use Cases", "Gap Analysis", "Product Backlog Grooming", "Proxy PO"],
    // "document_writing": ["BRD", "FRD", "UML diagrams", "Wireframes"],
    // "agile_ceremonies": ["Sprint Planning", "Daily Stand-up", "Sprint Review", "Sprint Retrospective"],
    // "soft_skills": ["Stakeholder Management", "Problem Solving", "Leadership", "Agile Methodologies", "Communication", "Creativity", "Motivational Thinking"]
  }},
  "experience": [
    {{
      "title": "Job title",
      "company": "Company",
      "duration": "Dates",
      "location": "Location",
      "achievements": [
        {{
          "category": "Only if explicitly present, else empty string",
          "description": "Exact text"
        }}
      ]
    }}
  ],
  "education": [...],
  "certifications": [...]
}}

CRITICAL RULES:
1. Skills section is MOST IMPORTANT - extract EVERY skill (aim for 20-50 skills total)
2. Look carefully at the resume for skills sections
3. If skills are bullet points, extract them ALL
4. Group skills by their section names in the resume
5. Extract ALL jobs separately
6. For bullet categories: only use if explicitly present, otherwise use empty string ""
7. Do NOT skip any content

Return only valid JSON.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Extract exactly as written. Focus heavily on extracting ALL skills. Preserve structure. Extract every job."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.05,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def normalize_skills_structure(self, skills: Dict) -> Dict:
        """Normalize skills - DON'T lose data"""
        
        # If no skills, return empty dict (not general_skills)
        if not skills or len(skills) == 0:
            return {}
        
        # If skills exist, keep as-is
        return skills
    
    def parse_pdf_resume(self, pdf_file) -> Dict[str, Any]:
        """Main method"""
        
        resume_text, hyperlinks = self.extract_text_and_links_from_pdf(pdf_file)
        
        if len(resume_text) < 100:
            raise ValueError("PDF appears empty")
        
        pii = self.extract_pii_locally(resume_text, hyperlinks)
        sanitized_text = self.sanitize_text(resume_text, pii)
        parsed_content = self.parse_sanitized_resume(sanitized_text)
        parsed_content['skills'] = self.normalize_skills_structure(parsed_content.get('skills', {}))
        
        linkedin_url = f"linkedin.com/in/{pii['linkedin']}" if pii.get("linkedin") else ""
        
        return {
            "personal_info": {
                "name": pii.get("name") or "Unknown",
                "title": parsed_content.get("title", "Professional"),
                "email": pii.get("email", ""),
                "phone": pii.get("phone", ""),
                "location": pii.get("location", ""),
                "linkedin": linkedin_url
            },
            "profile": parsed_content.get("profile", ""),
            "skills": parsed_content.get("skills", {}),
            "experience": parsed_content.get("experience", []),
            "education": parsed_content.get("education", []),
            "certifications": parsed_content.get("certifications", [])
        }
