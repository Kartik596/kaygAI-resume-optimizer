"""
Batch Suggestion Resume Optimizer Agent
Generates all suggestions at once for user selection
"""
from openai import OpenAI
from typing import Dict, List, Any
import json
from src.config.settings import settings


class ResumeOptimizerAgent:
    """AI agent that generates batch suggestions for resume optimization"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.MODEL_RESUME_MATCHER
        self.current_resume = None
        self.jd_requirements = None
        self.match_analysis = None
        self.all_suggestions = []
        self.selected_suggestions = []
    
    def analyze_and_generate_suggestions(
        self,
        sanitized_resume: Dict,
        jd_requirements: Dict,
        match_analysis: Dict
    ) -> List[Dict]:
        """
        Analyze resume and generate ALL suggestions at once
        
        Returns:
            List of suggestion dictionaries with:
            - id: Unique identifier
            - type: 'add_skill', 'add_achievement', 'modify_text', etc.
            - category: Grouping (Skills, Experience, Profile, etc.)
            - description: What to change
            - action: Exact action to take
            - reason: Why this helps
            - section: Where in JSON
            - value: What to add/change
        """
        
        # Store context
        self.current_resume = sanitized_resume
        self.jd_requirements = jd_requirements
        self.match_analysis = match_analysis
        
        # Build comprehensive prompt
        prompt = self._build_suggestion_prompt()
        
        # Get AI suggestions
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume optimizer. Analyze the resume structure and generate comprehensive, actionable suggestions."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        suggestions = result.get('suggestions', [])
        
        # Validate and enrich suggestions
        self.all_suggestions = self._validate_suggestions(suggestions)
        
        return self.all_suggestions
    
    def _build_suggestion_prompt(self) -> str:
        """Build comprehensive prompt for batch suggestions"""
        
        missing_skills = self.match_analysis['skills_match'].get('missing', [])
        missing_keywords = self.match_analysis['keyword_coverage'].get('missing_keywords', [])
        gaps = self.match_analysis.get('gaps', [])
        
        return f"""Analyze this resume and generate 5-10 specific, actionable suggestions to optimize it for the job description.

**Current Resume Structure:**
{json.dumps(self.current_resume, indent=2)}

**Job Requirements:**
- Role: {self.jd_requirements.get('role_title')}
- Industry: {self.jd_requirements.get('industry')}
- Required Skills: {', '.join(self.jd_requirements.get('required_skills', [])[:10])}
- Keywords: {', '.join(self.jd_requirements.get('keywords', [])[:15])}

**Gap Analysis:**
- Missing Skills: {', '.join(missing_skills[:10])}
- Missing Keywords: {', '.join(missing_keywords[:10])}
- Main Gaps: {'; '.join(gaps[:3])}
- Current Match Score: {self.match_analysis['overall_match_score']}/100

**Your Task:**
Generate 5-10 SMART suggestions that:
1. Understand the resume's CURRENT structure (sections, categories, format)
2. Suggest additions to EXISTING sections/buckets or propose NEW ones
3. Be SPECIFIC about where to add (exact section name, category)
4. Include EXACT text to add for achievements/experience lines
5. Prioritize high-impact changes (skills, keywords, quantifiable achievements)

**Output Format (JSON):**
{{
  "suggestions": [
    {{
      "id": 1,
      "category": "Skills",
      "type": "add_skill_to_existing",
      "description": "Add 'Python' to tools_and_technologies",
      "action": "Append 'Python' to skills.tools_and_technologies array",
      "reason": "Required by JD, improves ATS matching",
      "section": "skills.tools_and_technologies",
      "value": "Python",
      "priority": "high"
    }},
    {{
      "id": 2,
      "category": "Experience",
      "type": "add_achievement",
      "description": "Add AI automation achievement to current role",
      "action": "Add new achievement to experience[0].achievements",
      "reason": "Highlights relevant AI experience mentioned in JD",
      "section": "experience[0].achievements",
      "achievement_category": "AI & Automation",
      "value": "Implemented AI-powered automation reducing manual effort by 50%, aligning with role's focus on process optimization",
      "priority": "high"
    }},
    {{
      "id": 3,
      "category": "Profile",
      "type": "modify_text",
      "description": "Add 'healthcare domain' to profile summary",
      "action": "Insert 'with healthcare domain expertise' in profile",
      "reason": "JD emphasizes healthcare industry experience",
      "section": "profile",
      "value": "with healthcare domain expertise including HIPAA compliance",
      "insert_after": "T-shaped professional",
      "priority": "medium"
    }}
  ]
}}

**Important:**
- Suggest 5-10 changes total
- Mix of skills (2-3), achievements (3-5), profile updates (1-2)
- Be specific with exact text and locations
- Prioritize: high > medium > low
"""
    
    def _validate_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Validate and ensure all suggestions have required fields"""
        
        validated = []
        
        for i, sug in enumerate(suggestions):
            # Ensure required fields
            suggestion = {
                'id': sug.get('id', i + 1),
                'category': sug.get('category', 'Other'),
                'type': sug.get('type', 'add_text'),
                'description': sug.get('description', 'No description'),
                'action': sug.get('action', ''),
                'reason': sug.get('reason', ''),
                'section': sug.get('section', ''),
                'value': sug.get('value', ''),
                'priority': sug.get('priority', 'medium'),
                'selected': False  # User selection flag
            }
            
            # Add type-specific fields
            if 'achievement_category' in sug:
                suggestion['achievement_category'] = sug['achievement_category']
            
            if 'insert_after' in sug:
                suggestion['insert_after'] = sug['insert_after']
            
            validated.append(suggestion)
        
        return validated
    
    def select_suggestions(self, selected_ids: List[int]):
        """Mark suggestions as selected by user"""
        for suggestion in self.all_suggestions:
            if suggestion['id'] in selected_ids:
                suggestion['selected'] = True
                self.selected_suggestions.append(suggestion)
    
    def modify_suggestion(self, suggestion_id: int, new_value: str):
        """Allow user to modify a suggestion's value"""
        for suggestion in self.all_suggestions:
            if suggestion['id'] == suggestion_id:
                suggestion['value'] = new_value
                suggestion['modified'] = True
    
    def get_selected_suggestions(self) -> List[Dict]:
        """Return only selected suggestions"""
        return self.selected_suggestions
    
    def generate_updated_resume(self) -> Dict:
        """Apply selected suggestions to generate updated resume"""
        
        if not self.selected_suggestions:
            return self.current_resume
        
        # Build detailed instructions
        instructions = self._format_suggestions_for_ai()
        
        prompt = f"""Apply these EXACT changes to the resume.

**Current Resume:**
{json.dumps(self.current_resume, indent=2)}

**CHANGES TO APPLY:**
{instructions}

**Rules:**
1. Apply ONLY the changes listed above
2. Keep ALL other content UNCHANGED
3. Maintain exact JSON structure
4. Preserve [REDACTED] placeholders
5. For skills: Add to appropriate array if not present
6. For achievements: Add new object with category and description
7. For text modifications: Make precise edits as specified

Return complete updated resume as JSON."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise JSON editor. Apply only specified changes. Return valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.05,
            response_format={"type": "json_object"}
        )
        
        updated_resume = json.loads(response.choices[0].message.content)
        return updated_resume
    
    def _format_suggestions_for_ai(self) -> str:
        """Format selected suggestions as clear instructions"""
        
        formatted = []
        
        for sug in self.selected_suggestions:
            if sug['type'] in ['add_skill', 'add_skill_to_existing']:
                formatted.append(
                    f"• ADD SKILL: '{sug['value']}'\n"
                    f"  Location: {sug['section']}\n"
                    f"  Action: {sug['action']}"
                )
            
            elif sug['type'] == 'add_achievement':
                formatted.append(
                    f"• ADD ACHIEVEMENT:\n"
                    f"  Category: {sug.get('achievement_category', 'General')}\n"
                    f"  Text: \"{sug['value']}\"\n"
                    f"  Location: {sug['section']}\n"
                    f"  Action: {sug['action']}"
                )
            
            elif sug['type'] == 'modify_text':
                formatted.append(
                    f"• MODIFY TEXT:\n"
                    f"  Location: {sug['section']}\n"
                    f"  Change: {sug['description']}\n"
                    f"  New text: \"{sug['value']}\"\n"
                    f"  Action: {sug['action']}"
                )
        
        return "\n\n".join(formatted)
