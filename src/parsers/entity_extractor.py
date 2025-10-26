"""
Enhanced Entity extraction for Business Analyst resumes
"""
import re
from typing import Optional, List, Dict
from src.utils.pattern_matcher import PatternMatcher
from src.utils.text_cleaner import TextCleaner
from src.models.resume_data import ContactInfo

class EntityExtractor:
    """Extract entities like name, contact info, etc."""
    
    def __init__(self, text: str):
        """Initialize entity extractor"""
        self.text = text
        self.pattern_matcher = PatternMatcher()
        self.text_cleaner = TextCleaner()
    
    def extract_name(self) -> str:
        """Extract candidate name (usually at the top)"""
        lines = self.text_cleaner.extract_lines(self.text)
        
        # Name is usually in first 10 lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip if line contains email, phone, or URLs
            if '@' in line or 'http' in line.lower() or re.search(r'\d{3}', line):
                continue
            
            # Skip if line is too long (likely not a name)
            if len(line) > 60:
                continue
            
            # Skip common section headers
            section_keywords = ['PROFILE', 'SUMMARY', 'EXPERIENCE', 'EDUCATION', 
                              'SKILLS', 'CERTIFICATIONS', 'OBJECTIVE']
            if any(keyword in line.upper() for keyword in section_keywords):
                continue
            
            # Check if it looks like a name
            words = line.split()
            
            # Name is typically 2-4 words with capital letters
            if 2 <= len(words) <= 4:
                # Check if words start with capital letters
                if all(w[0].isupper() for w in words if w and len(w) > 1):
                    # Not all caps (avoid section headers)
                    if not line.isupper():
                        return line
        
        # Fallback: look for pattern like "FirstName LastName"
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        match = re.search(name_pattern, '\n'.join(lines[:10]))
        if match:
            return match.group(1)
        
        return "Name Not Found"
    
    def extract_contact_info(self) -> ContactInfo:
        """Extract all contact information"""
        # Look in first 30 lines for contact info
        header_text = '\n'.join(self.text_cleaner.extract_lines(self.text)[:30])
        
        return ContactInfo(
            email=self.pattern_matcher.extract_email(header_text),
            phone=self.pattern_matcher.extract_phone(header_text),
            linkedin=self.pattern_matcher.extract_linkedin(header_text),
            github=self.pattern_matcher.extract_github(header_text),
            location=self._extract_location(header_text)
        )
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location (city, state, country)"""
        # Common location patterns
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})',  # City, ST
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+)',  # City, Country
            r'([A-Z][a-z]+)\s*,\s*([A-Z][a-z]+)\s*,\s*([A-Z][a-z]+)',  # City, State, Country
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def extract_skills_structured(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills organized by categories
        Handles format like:
        Tools & Technologies: Jira, Azure DevOps, Figma...
        Business Analysis: Requirements Elicitation...
        """
        structured_skills = {}
        
        # Split by lines
        lines = text.split('\n')
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a category header (ends with colon)
            if ':' in line:
                parts = line.split(':', 1)
                category = parts[0].strip()
                skills_text = parts[1].strip() if len(parts) > 1 else ""
                
                # This is a category header
                current_category = category
                
                # Extract skills from the same line
                if skills_text:
                    skills = self._parse_skill_list(skills_text)
                    structured_skills[current_category] = skills
            elif current_category:
                # Continuation of previous category
                skills = self._parse_skill_list(line)
                if current_category in structured_skills:
                    structured_skills[current_category].extend(skills)
                else:
                    structured_skills[current_category] = skills
        
        return structured_skills
    
    def _parse_skill_list(self, text: str) -> List[str]:
        """Parse a list of skills from text"""
        # Remove bullet points
        text = re.sub(r'^[•\-\*]\s*', '', text)
        
        # Split by commas
        skills = [s.strip() for s in text.split(',')]
        
        # Filter out empty and very short items
        skills = [s for s in skills if len(s) > 1]
        
        return skills
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract flat list of all skills"""
        structured = self.extract_skills_structured(text)
        
        # Flatten all skills into a single list
        all_skills = []
        for category, skills in structured.items():
            all_skills.extend(skills)
        
        return all_skills
