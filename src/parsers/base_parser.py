"""
Main resume parser - orchestrates all parsing modules
"""
from pathlib import Path
from typing import Optional
from src.parsers.pdf_extractor import PDFExtractor
from src.parsers.entity_extractor import EntityExtractor
from src.parsers.section_extractor import SectionExtractor
from src.models.resume_data import ResumeData, ResumeMetadata

class ResumeParser:
    """Main resume parser class"""
    
    def __init__(self, pdf_path: str):
        """Initialize resume parser"""
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")
        
        # Initialize extractors
        self.pdf_extractor = PDFExtractor(str(self.pdf_path))
        self.text: Optional[str] = None
        self.entity_extractor: Optional[EntityExtractor] = None
        self.section_extractor: Optional[SectionExtractor] = None
    
    def parse(self) -> ResumeData:
        """Parse resume and return structured data"""
        print("🔄 Extracting text from PDF...")
        self.text = self.pdf_extractor.extract_text()
        print(f"✅ Extracted {len(self.text)} characters")
        
        # Initialize extractors with text
        self.entity_extractor = EntityExtractor(self.text)
        self.section_extractor = SectionExtractor(self.text)
        
        # Extract basic info
        print("🔄 Extracting contact information...")
        name = self.entity_extractor.extract_name()
        contact = self.entity_extractor.extract_contact_info()
        print(f"✅ Found: {name}")
        
        # Extract sections
        print("🔄 Extracting resume sections...")
        sections = self.section_extractor.extract_all_sections()
        print(f"✅ Found {len(sections)} sections: {', '.join(sections.keys())}")
        
        # Extract summary
        summary = sections.get('summary', '')
        
        # Extract skills
        skills_text = sections.get('skills', '')
        skills = self.entity_extractor.extract_skills(skills_text) if skills_text else []
        print(f"✅ Extracted {len(skills)} skills")
        
        # Extract experience
        experience_text = sections.get('experience', '')
        experience = self.section_extractor.parse_experience_section(experience_text) if experience_text else []
        print(f"✅ Extracted {len(experience)} work experiences")
        
        # Extract education
        education_text = sections.get('education', '')
        education = self.section_extractor.parse_education_section(education_text) if education_text else []
        print(f"✅ Extracted {len(education)} education entries")
        
        # Extract projects
        projects_text = sections.get('projects', '')
        projects = self.section_extractor.parse_projects_section(projects_text) if projects_text else []
        print(f"✅ Extracted {len(projects)} projects")
        
        # Extract certifications
        cert_text = sections.get('certifications', '')
        certifications = self.section_extractor.parse_certifications_section(cert_text) if cert_text else []
        print(f"✅ Extracted {len(certifications)} certifications")
        
        # Create metadata
        metadata = ResumeMetadata(
            source_file=str(self.pdf_path.name),
            parser_version="1.0"
        )
        
        # Create ResumeData object
        resume_data = ResumeData(
            name=name,
            contact=contact,
            summary=summary,
            skills=skills,
            experience=experience,
            education=education,
            projects=projects,
            certifications=certifications,
            metadata=metadata
        )
        
        return resume_data
    
    def parse_and_save(self, output_path: Optional[str] = None) -> ResumeData:
        """Parse resume and save to JSON file"""
        resume_data = self.parse()
        
        if output_path is None:
            output_path = str(self.pdf_path.with_suffix('.json'))
        
        print(f"💾 Saving parsed data to {output_path}...")
        resume_data.save_to_file(output_path)
        print("✅ Saved successfully")
        
        return resume_data
