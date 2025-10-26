"""
Enhanced Section extraction for Business Analyst resumes
"""
import re
from typing import Dict, Optional, List, Tuple
from src.config.settings import settings
from src.utils.text_cleaner import TextCleaner
from src.utils.pattern_matcher import PatternMatcher
from src.models.resume_data import Experience, Education, Project, Certification

class SectionExtractor:
    """Extract different sections from resume text"""
    
    def __init__(self, text: str):
        """Initialize section extractor"""
        self.text = text
        self.text_cleaner = TextCleaner()
        self.pattern_matcher = PatternMatcher()
    
    def extract_section(self, section_name: str) -> Optional[str]:
        """Extract a specific section by name"""
        keywords = settings.SECTION_HEADERS.get(section_name, [])
        if not keywords:
            return None
        
        # Find section start
        section_pattern = '|'.join([re.escape(kw) for kw in keywords])
        match = re.search(
            rf'(?:^|\n)\s*({section_pattern})\s*\n',
            self.text,
            re.IGNORECASE | re.MULTILINE
        )
        
        if not match:
            return None
        
        start_pos = match.end()
        
        # Find next section (end of current section)
        # Look for next all-caps or title-case header
        next_section = re.search(
            r'\n\s*(?:[A-Z][A-Z\s&/]{2,}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\n',
            self.text[start_pos:]
        )
        
        if next_section:
            end_pos = start_pos + next_section.start()
        else:
            end_pos = len(self.text)
        
        section_text = self.text[start_pos:end_pos].strip()
        return section_text
    
    def extract_all_sections(self) -> Dict[str, str]:
        """Extract all known sections"""
        sections = {}
        
        for section_name in settings.SECTION_HEADERS.keys():
            section_text = self.extract_section(section_name)
            if section_text:
                sections[section_name] = section_text
        
        return sections
    
    def parse_experience_section(self, text: str) -> List[Experience]:
        """
        Parse experience section into structured format
        Handles format like:
        Job Title | Company
        Date - Date
        • Bullet point 1
        • Bullet point 2
        """
        if not text:
            return []
        
        experiences = []
        
        # Split by double newlines or when we see a new job title pattern
        # Pattern: Line followed by line with pipe or date
        entries = self._split_experience_entries(text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if len(lines) < 2:
                continue
            
            # First line: Job Title | Company
            first_line = lines[0]
            title = ""
            company = ""
            
            if '|' in first_line:
                parts = first_line.split('|')
                title = parts[0].strip()
                company = parts[1].strip()
            else:
                title = first_line
                company = lines[1] if len(lines) > 1 else ""
            
            # Second line: Date range
            date_line = lines[1] if '|' in first_line else (lines[2] if len(lines) > 2 else "")
            duration = self._extract_duration_from_line(date_line)
            
            # Extract start and end dates
            start_date, end_date = self._parse_date_range(duration) if duration else (None, None)
            
            # Rest are bullet points (achievements)
            achievements = []
            for line in lines[2:] if '|' in first_line else lines[3:]:
                # Check if it's a bullet point or sub-section
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    # Remove bullet and add
                    achievement = re.sub(r'^[•\-\*]\s*', '', line)
                    achievements.append(achievement)
                elif ':' in line and len(line) < 100:
                    # This might be a category like "Requirements Engineering:"
                    achievements.append(line)
                elif line and not line.isupper():
                    # Continuation of previous bullet
                    if achievements:
                        achievements[-1] += ' ' + line
            
            # Create experience object
            exp = Experience(
                title=title,
                company=company,
                start_date=start_date,
                end_date=end_date,
                duration=duration,
                achievements=achievements
            )
            
            experiences.append(exp)
        
        return experiences
    
    def _split_experience_entries(self, text: str) -> List[str]:
        """Split experience text into individual job entries"""
        # Look for patterns that indicate a new job entry
        # Usually: Job title followed by company (with |) and date range
        
        entries = []
        current_entry = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if this line looks like a job title (contains | or is followed by date)
            is_new_entry = False
            if '|' in line_stripped and i < len(lines) - 1:
                # Check if next line has a date pattern
                next_line = lines[i + 1].strip()
                if re.search(r'\d{4}', next_line):
                    is_new_entry = True
            
            if is_new_entry and current_entry:
                # Start new entry
                entries.append('\n'.join(current_entry))
                current_entry = [line]
            else:
                current_entry.append(line)
        
        # Add last entry
        if current_entry:
            entries.append('\n'.join(current_entry))
        
        return entries
    
    def _extract_duration_from_line(self, line: str) -> Optional[str]:
        """Extract duration from a line"""
        # Pattern: Month Year - Month Year or Present
        pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*[-–—]\s*((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})|Present|Current)'
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return match.group(0)
        
        # Pattern: Just years
        pattern = r'(\d{4})\s*[-–—]\s*(\d{4}|Present|Current)'
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return match.group(0)
        
        return None
    
    def _parse_date_range(self, duration: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse start and end dates from duration string"""
        if not duration:
            return None, None
        
        parts = re.split(r'\s*[-–—]\s*', duration)
        start_date = parts[0].strip() if len(parts) > 0 else None
        end_date = parts[1].strip() if len(parts) > 1 else None
        
        return start_date, end_date
    
    def parse_education_section(self, text: str) -> List[Education]:
        """
        Parse education section
        Format:
        Institution Name
        Degree - Percentage
        Year - Year
        """
        if not text:
            return []
        
        education_list = []
        entries = re.split(r'\n\s*\n', text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if not lines:
                continue
            
            # First line: Institution or Degree
            # Second line: Degree or Institution
            institution = ""
            degree = ""
            gpa = None
            graduation_date = None
            
            # Try to identify which line is which
            for line in lines:
                # Check if line has percentage
                if '%' in line or 'GPA' in line.upper():
                    # This line has the degree and percentage
                    degree_parts = line.split('-')
                    degree = degree_parts[0].strip()
                    if len(degree_parts) > 1:
                        gpa = degree_parts[1].strip()
                elif re.search(r'\d{4}', line):
                    # This line has dates
                    dates = self.pattern_matcher.extract_dates(line)
                    graduation_date = dates[-1] if dates else None
                elif not institution and not any(kw in line.upper() for kw in ['CERTIFICATE', 'DIPLOMA', 'DEGREE', 'B.TECH', 'M.TECH', 'PGDM', 'MBA']):
                    # This is likely the institution
                    institution = line
                elif not degree:
                    # This is likely the degree
                    degree = line
            
            edu = Education(
                degree=degree,
                institution=institution,
                graduation_date=graduation_date,
                gpa=gpa
            )
            
            education_list.append(edu)
        
        return education_list
    
    def parse_certifications_section(self, text: str) -> List[Certification]:
        """
        Parse certifications section
        Format:
        Certification Name
        Year - Candidate Number: XXXXX
        Certificate Number: XXXXX
        """
        if not text:
            return []
        
        certifications = []
        
        # Split by double newlines or certification patterns
        entries = re.split(r'\n\s*\n', text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if not lines:
                continue
            
            # First line is certification name
            name = lines[0]
            
            # Extract other details
            issuer = None
            date = None
            credential_id = None
            
            for line in lines[1:]:
                # Extract year
                if re.search(r'\d{4}', line) and not date:
                    dates = self.pattern_matcher.extract_dates(line)
                    date = dates[0] if dates else None
                
                # Extract certificate/candidate number
                if 'Certificate Number' in line or 'Candidate Number' in line:
                    match = re.search(r':\s*([A-Za-z0-9]+)', line)
                    if match:
                        credential_id = match.group(1)
                
                # Extract issuer (usually after a dash or in parentheses)
                if not issuer and ('(' in line or '-' in line):
                    match = re.search(r'[\(\-]\s*([A-Za-z\s&]+)[\)\-]?', line)
                    if match:
                        issuer = match.group(1).strip()
            
            # Try to extract issuer from name if not found
            if not issuer:
                # Common patterns: "Name (Issuer)" or "Name - Issuer"
                match = re.search(r'\(([^)]+)\)$', name)
                if match:
                    issuer = match.group(1)
                    name = re.sub(r'\s*\([^)]+\)$', '', name)
            
            cert = Certification(
                name=name,
                issuer=issuer,
                date=date,
                credential_id=credential_id
            )
            
            certifications.append(cert)
        
        return certifications
