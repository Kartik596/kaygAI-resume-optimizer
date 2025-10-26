"""
Professional Resume Builder - FULLY ADAPTIVE
Handles ANY resume structure dynamically
"""
import json
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.platypus.flowables import Flowable


class CenteredNameHeader(Flowable):
    """Header with vertically centered name"""
    def __init__(self, name, width, height):
        Flowable.__init__(self)
        self.name = name
        self.width = width
        self.height = height
    
    def draw(self):
        self.canv.setFillColor(colors.HexColor('#1a7f7a'))
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        self.canv.setFillColor(colors.white)
        self.canv.setFont('Helvetica-Bold', 20)
        
        font_size = 20
        font_descent = font_size * 0.2
        center_y = (self.height / 2) - (font_size / 2) + font_descent
        
        self.canv.drawCentredString(self.width/2, center_y, self.name)


class ModernSectionHeader(Flowable):
    """Section header with teal background"""
    def __init__(self, text, width):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = 18
    
    def draw(self):
        self.canv.setFillColor(colors.HexColor('#1a7f7a'))
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        self.canv.setFillColor(colors.white)
        self.canv.setFont('Helvetica-Bold', 11)
        self.canv.drawString(8, 5, self.text)


def draw_sidebar_background(canvas, doc):
    """Draw light teal background for sidebar area"""
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#e6f4f4'))
    
    page_width = letter[0]
    page_height = letter[1]
    sidebar_width = 2.5 * inch
    sidebar_x = page_width - 0.5*inch - sidebar_width
    
    canvas.rect(sidebar_x, 0.35*inch, sidebar_width, page_height - 0.85*inch, fill=1, stroke=0)
    canvas.restoreState()


class CompactStreamlinedBuilder:
    """Fully adaptive resume builder - works with ANY JSON structure"""
    
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self.data = self._load_json()
        self._normalize_data()
        self.styles = self._create_styles()
    
    def _load_json(self) -> Dict[str, Any]:
        """Load resume data from JSON"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _normalize_data(self):
        """Normalize resume data to handle different structures"""
        
        # Handle personal_info vs contact
        if 'contact' in self.data and 'personal_info' not in self.data:
            self.data['personal_info'] = {'contact': self.data['contact']}
        
        if 'personal_info' not in self.data:
            self.data['personal_info'] = {
                'name': 'Unknown',
                'contact': {
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': ''
                }
            }
        
        # Ensure contact exists inside personal_info
        if 'contact' not in self.data['personal_info']:
            self.data['personal_info']['contact'] = {
                'email': self.data['personal_info'].get('email', ''),
                'phone': self.data['personal_info'].get('phone', ''),
                'location': self.data['personal_info'].get('location', ''),
                'linkedin': self.data['personal_info'].get('linkedin', '')
            }
        
        # Ensure skills is a dict
        if 'skills' not in self.data or not isinstance(self.data['skills'], dict):
            self.data['skills'] = {}
        
        # Ensure experience is a list
        if 'experience' not in self.data:
            self.data['experience'] = []
        
        # Ensure education and certifications
        if 'education' not in self.data:
            self.data['education'] = []
        if 'certifications' not in self.data:
            self.data['certifications'] = []
    
    def _create_styles(self):
        """Create paragraph styles"""
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='CompactSidebarText',
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=1.5,
            leading=11.5,
            fontName='Helvetica',
            wordWrap='CJK',
            splitLongWords=1,
        ))
        
        styles.add(ParagraphStyle(
            name='CompactSkills',
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=3,
            leading=11.5,
            fontName='Helvetica',
            wordWrap='CJK',
            splitLongWords=1,
        ))
        
        styles.add(ParagraphStyle(
            name='CompactMainText',
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=3,
            leading=11.5,
            textColor=colors.HexColor('#2a2a2a'),
            fontName='Helvetica',
            wordWrap='CJK'
        ))
        
        styles.add(ParagraphStyle(
            name='CompactJobTitle',
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=1,
            fontName='Helvetica-Bold',
            leading=11.5,
            wordWrap='CJK'
        ))
        
        styles.add(ParagraphStyle(
            name='CompactCompanyDate',
            fontSize=9.5,
            textColor=colors.HexColor('#555555'),
            spaceAfter=1,
            fontName='Helvetica-Oblique',
            leading=11,
            wordWrap='CJK'
        ))
        
        styles.add(ParagraphStyle(
            name='CompactBulletPoint',
            fontSize=10,
            leftIndent=12,
            spaceAfter=1.5,
            alignment=TA_JUSTIFY,
            leading=11.5,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica',
            bulletIndent=8,
            wordWrap='CJK',
            splitLongWords=1
        ))
        
        return styles
    
    def generate_pdf(self, output_path: str) -> str:
        """Generate adaptive professional resume"""
        print(f"📄 Generating resume from: {self.json_path}")
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.35*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        
        # Header
        name = self.data['personal_info'].get('name', 'Unknown')
        header_box = CenteredNameHeader(name, 7.5*inch, 0.5*inch)
        
        header_table = Table([[header_box]], colWidths=[7.5*inch],
            style=TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
        
        story.append(header_table)
        story.append(Spacer(1, 0.08*inch))
        
        # Build main and sidebar
        left_main = self._build_main()
        right_sidebar = self._build_sidebar()
        
        main_table = Table([[left_main, right_sidebar]], colWidths=[5.0*inch, 2.5*inch],
            style=TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (0,0), 10),
                ('LEFTPADDING', (1,0), (1,0), 10),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
        
        story.append(main_table)
        doc.build(story, onFirstPage=draw_sidebar_background, onLaterPages=draw_sidebar_background)
        
        print(f"✅ Resume PDF generated: {output_path}")
        return output_path
    
    def _build_main(self):
        """LEFT - Main content"""
        elements = []
        
        # Professional Summary
        if self.data.get('profile'):
            elements.append(ModernSectionHeader('PROFESSIONAL SUMMARY', 4.9*inch))
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph(self.data['profile'], self.styles['CompactMainText']))
            elements.append(Spacer(1, 0.05*inch))
        
        # Work History
        if self.data.get('experience'):
            elements.append(ModernSectionHeader('WORK HISTORY', 4.9*inch))
            elements.append(Spacer(1, 0.05*inch))
            
            for i, exp in enumerate(self.data['experience']):
                elements.append(Paragraph(
                    f"<b>{exp.get('title', 'Position')}</b> - {exp.get('company', 'Company')}", 
                    self.styles['CompactJobTitle']
                ))
                
                elements.append(Paragraph(
                    f"{exp.get('location', 'Remote')} | {exp.get('duration', 'Dates')}", 
                    self.styles['CompactCompanyDate']
                ))
                
                # ✅ FINAL FIX: Use font tag for explicit bold
                achievements = exp.get('achievements', [])
                for ach in achievements:
                    if isinstance(ach, dict):
                        category = ach.get('category', '').strip()
                        description = ach.get('description', '').strip()
                        
                        # Use <font> tag for ReportLab bold
                        if category and category != '':
                            text = f"• <font name='Helvetica-Bold'>{category}:</font> {description}"
                        else:
                            text = f"• {description}"
                    else:
                        text = f"• {str(ach)}"
                    
                    elements.append(Paragraph(text, self.styles['CompactBulletPoint']))
                
                if i < len(self.data['experience']) - 1:
                    elements.append(Spacer(1, 0.03*inch))
        
        return Table([[elem] for elem in elements], colWidths=[4.95*inch], style=TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'), 
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0), 
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0)
        ]))
    
    def _build_sidebar(self):
        """RIGHT - Sidebar (FULLY ADAPTIVE)"""
        elements = []
        contact = self.data['personal_info'].get('contact', {})
        
        elements.append(Spacer(1, 0.05*inch))
        
        # CONTACT
        elements.append(ModernSectionHeader('CONTACT', 2.2*inch))
        elements.append(Spacer(1, 0.04*inch))
        
        if contact.get('email'):
            email = contact['email']
            elements.append(Paragraph(
                f'<b>Email:</b> <a href="mailto:{email}" color="#1a7f7a"><u>{email}</u></a>', 
                self.styles['CompactSidebarText']
            ))
        
        if contact.get('phone'):
            elements.append(Paragraph(f"<b>Phone:</b> {contact['phone']}", self.styles['CompactSidebarText']))
        
        if contact.get('location'):
            elements.append(Paragraph(f"<b>Location:</b> {contact['location']}", self.styles['CompactSidebarText']))
        
        # ✅ FIXED: LinkedIn URL handling
        if contact.get('linkedin'):
            linkedin_value = contact['linkedin']
            
            if linkedin_value.startswith('http'):
                linkedin_url = linkedin_value
            elif linkedin_value.startswith('linkedin.com/in/'):
                linkedin_url = f"https://www.{linkedin_value}"
            else:
                linkedin_url = f"https://www.linkedin.com/in/{linkedin_value}"
            
            elements.append(Paragraph(
                f'<b>LinkedIn:</b> <a href="{linkedin_url}" color="#1a7f7a"><u>Profile</u></a>', 
                self.styles['CompactSidebarText']
            ))
        
        elements.append(Spacer(1, 0.04*inch))
        
        # SKILLS - FULLY ADAPTIVE
        skills_data = self.data.get('skills', {})
        
        if skills_data:
            elements.append(ModernSectionHeader('SKILLS', 2.2*inch))
            elements.append(Spacer(1, 0.04*inch))
            
            for category_key, skills_list in skills_data.items():
                if skills_list:
                    category_display = category_key.replace('_', ' ').title()
                    
                    if isinstance(skills_list, list):
                        skills_text = ', '.join(str(s) for s in skills_list)
                    else:
                        skills_text = str(skills_list)
                    
                    elements.append(Paragraph(
                        f"<b>{category_display}:</b> {skills_text}", 
                        self.styles['CompactSkills']
                    ))
            
            elements.append(Spacer(1, 0.04*inch))
        
        # EDUCATION
        if self.data.get('education'):
            elements.append(ModernSectionHeader('EDUCATION', 2.2*inch))
            elements.append(Spacer(1, 0.04*inch))
            
            for edu in self.data['education']:
                institution = edu.get('institution', 'Institution')
                degree = edu.get('degree', 'Degree')
                
                elements.append(Paragraph(f"<b>{institution}</b>", self.styles['CompactSidebarText']))
                elements.append(Paragraph(degree, self.styles['CompactSidebarText']))
                
                if 'year' in edu:
                    elements.append(Paragraph(str(edu['year']), self.styles['CompactSidebarText']))
                elif 'start_year' in edu and 'end_year' in edu:
                    elements.append(Paragraph(f"{edu['start_year']}-{edu['end_year']}", self.styles['CompactSidebarText']))
                
                elements.append(Spacer(1, 0.02*inch))
        
        # CERTIFICATIONS
        if self.data.get('certifications'):
            elements.append(ModernSectionHeader('CERTIFICATIONS', 2.2*inch))
            elements.append(Spacer(1, 0.04*inch))
            
            for cert in self.data['certifications']:
                name = cert.get('name', 'Certification')
                elements.append(Paragraph(f"<b>{name}</b>", self.styles['CompactSidebarText']))
                
                if 'date' in cert:
                    elements.append(Paragraph(str(cert['date']), self.styles['CompactSidebarText']))
                elif 'year' in cert:
                    elements.append(Paragraph(str(cert['year']), self.styles['CompactSidebarText']))
                
                elements.append(Spacer(1, 0.02*inch))
        
        return Table([[elem] for elem in elements], colWidths=[2.3*inch], style=TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'), 
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0)
        ]))


# Export
ResumeBuilder = CompactStreamlinedBuilder
