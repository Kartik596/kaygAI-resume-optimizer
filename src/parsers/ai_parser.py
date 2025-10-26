"""
AI-powered resume parser using OpenAI
"""
import os
import json
from typing import Optional
from openai import OpenAI, AzureOpenAI
from pathlib import Path
from src.parsers.pdf_extractor import PDFExtractor
from src.models.resume_data import ResumeData
from src.config.settings import settings

class AIResumeParser:
    """Parse resume using OpenAI GPT-4"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        use_azure: bool = False
    ):
        """
        Initialize AI parser
        
        Args:
            api_key: OpenAI API key (uses settings if not provided)
            model: Model name (uses settings if not provided)
            use_azure: Whether to use Azure OpenAI
        """
        self.use_azure = use_azure or settings.USE_AZURE
        self.model = model or settings.OPENAI_MODEL
        
        if self.use_azure:
            # Initialize Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=api_key or settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
            print(f"🔵 Using Azure OpenAI: {settings.AZURE_OPENAI_ENDPOINT}")
        else:
            # Initialize OpenAI client
            self.api_key = api_key or settings.OPENAI_API_KEY
            if not self.api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file")
            
            self.client = OpenAI(api_key=self.api_key)
            print(f"🤖 Using OpenAI Model: {self.model}")
        
        # Get model info
        self.model_info = settings.get_model_info(self.model)
        print(f"📊 Model: {self.model_info['name']}")
    
    def parse_from_pdf(self, pdf_path: str) -> ResumeData:
        """Parse resume from PDF file"""
        print("📄 Extracting text from PDF...")
        
        # Step 1: Extract text using Python (fast and free)
        extractor = PDFExtractor(pdf_path)
        resume_text = extractor.extract_text()
        
        print(f"✅ Extracted {len(resume_text)} characters")
        print(f"🤖 Sending to {self.model_info['name']} for intelligent parsing...")
        
        # Step 2: Parse using OpenAI (intelligent)
        resume_data = self.parse_text_with_ai(resume_text, pdf_path)
        
        return resume_data
    
    def parse_text_with_ai(self, text: str, source_file: str = "") -> ResumeData:
        """Parse resume text using OpenAI"""
        
        # Create detailed prompt for GPT-4
        prompt = self._create_parsing_prompt(text)
        
        try:
            # Prepare API call parameters
            api_params = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert resume parser. Extract structured information from resumes with high accuracy. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": settings.PARSER_TEMPERATURE,
                "max_tokens": settings.PARSER_MAX_TOKENS,
                "response_format": {"type": "json_object"}
            }
            
            # Add model or deployment based on provider
            if self.use_azure:
                api_params["model"] = self.deployment
            else:
                api_params["model"] = self.model
            
            # Make API call
            response = self.client.chat.completions.create(**api_params)
            
            # Parse JSON response
            json_str = response.choices[0].message.content
            parsed_data = json.loads(json_str)
            
            # Calculate cost (for OpenAI only)
            if not self.use_azure:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._calculate_cost(input_tokens, output_tokens)
                print(f"✅ AI parsing complete! (Cost: ${cost:.4f})")
            else:
                print("✅ AI parsing complete!")
            
            # Add metadata
            if 'metadata' not in parsed_data:
                parsed_data['metadata'] = {}
            parsed_data['metadata']['source_file'] = Path(source_file).name if source_file else "unknown"
            parsed_data['metadata']['parser_version'] = "AI-1.0"
            parsed_data['metadata']['model_used'] = self.deployment if self.use_azure else self.model
            
            # Convert to ResumeData object
            resume_data = ResumeData.from_dict(parsed_data)
            
            return resume_data
            
        except Exception as e:
            print(f"❌ AI parsing failed: {e}")
            raise
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost of API call"""
        input_cost = (input_tokens / 1000) * self.model_info['cost_per_1k_input']
        output_cost = (output_tokens / 1000) * self.model_info['cost_per_1k_output']
        return input_cost + output_cost
    
    def _create_parsing_prompt(self, text: str) -> str:
        """Create detailed prompt for resume parsing"""
        
        prompt = f"""
Parse the following resume and extract all information into a structured JSON format.

RESUME TEXT:
---
{text}
---

Extract the following information and return as JSON with this EXACT structure:

{{
  "name": "Full name of the candidate",
  "contact": {{
    "email": "email@example.com or null",
    "phone": "phone number or null",
    "linkedin": "LinkedIn URL or null",
    "github": "GitHub URL or null",
    "location": "City, State or null",
    "portfolio": "Portfolio URL or null"
  }},
  "summary": "Professional summary/profile section as a single string",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, State or null",
      "start_date": "Month Year or null",
      "end_date": "Month Year or Present",
      "duration": "Full duration string",
      "description": "Job description or null",
      "achievements": ["Achievement 1", "Achievement 2"],
      "technologies": ["Tech1", "Tech2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "Institution name",
      "location": "City, State or null",
      "graduation_date": "Year or null",
      "gpa": "GPA/Percentage or null",
      "relevant_coursework": ["Course1", "Course2"]
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Project description",
      "technologies": ["Tech1", "Tech2"],
      "url": "Project URL or null",
      "duration": "Duration or null",
      "highlights": ["Highlight 1", "Highlight 2"]
    }}
  ],
  "certifications": [
    {{
      "name": "Certification name",
      "issuer": "Issuing organization or null",
      "date": "Year or null",
      "credential_id": "Credential ID or null",
      "url": "Verification URL or null"
    }}
  ],
  "achievements": ["Achievement 1", "Achievement 2"],
  "languages": ["Language1", "Language2"]
}}

IMPORTANT PARSING RULES:
1. Extract ALL bullet points under each job as separate achievements
2. If skills are categorized (e.g., "Tools & Technologies: X, Y, Z"), flatten them into a single skills array
3. Parse dates carefully - use "Present" for current positions
4. For education, extract percentage/GPA if mentioned
5. For certifications, extract certificate numbers if present
6. If information is not found, use null (not empty strings)
7. Preserve all achievements exactly as written
8. Extract technologies/tools mentioned in experience

Return ONLY the JSON object, nothing else.
"""
        
        return prompt


class HybridResumeParser:
    """
    Hybrid parser that uses AI for parsing but can fallback to rule-based
    """
    
    def __init__(
        self, 
        use_ai: bool = True,
        model: Optional[str] = None,
        use_azure: bool = False
    ):
        """
        Initialize hybrid parser
        
        Args:
            use_ai: Whether to use AI parsing
            model: Model name to use (optional)
            use_azure: Whether to use Azure OpenAI
        """
        self.use_ai = use_ai
        
        if use_ai:
            try:
                self.ai_parser = AIResumeParser(
                    model=model,
                    use_azure=use_azure
                )
                print("✅ AI parser initialized")
            except Exception as e:
                print(f"⚠️  AI parser failed to initialize: {e}")
                print("📋 Falling back to rule-based parser")
                self.use_ai = False
    
    def parse(self, pdf_path: str) -> ResumeData:
        """Parse resume using best available method"""
        
        if self.use_ai:
            try:
                return self.ai_parser.parse_from_pdf(pdf_path)
            except Exception as e:
                print(f"⚠️  AI parsing failed: {e}")
                print("📋 Falling back to rule-based parser")
        
        # Fallback to rule-based parser
        from src.parsers.base_parser import ResumeParser
        parser = ResumeParser(pdf_path)
        return parser.parse()
