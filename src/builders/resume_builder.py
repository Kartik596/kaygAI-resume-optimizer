"""
Professional Resume Builder - DUAL-TONE with Dynamic Skills from JSON
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
    """Build dual-tone resume with dynamic skills from JSON"""
    
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self.data = self._load_json()
        self.styles = self._create_styles()
    
    def _load_json(self) -> Dict[str, Any]:
        """Load resume data from provided JSON path"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
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
        """Generate dual-tone professional resume"""
        print(f"📄 Generating dual-tone resume from: {self.json_path}")
        
        # Debug info
        skills_count = len(self.data.get('skills', {}).get('tools_and_technologies', []))
        print(f"📊 Skills count: {skills_count}")
        print(f"📝 Profile length: {len(self.data.get('profile', ''))} chars")
        print(f"💼 Achievements: {len(self.data.get('experience', [{}])[0].get('achievements', []))}")
        
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
        header_box = CenteredNameHeader(self.data['personal_info']['name'], 7.5*inch, 0.5*inch)
        
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
        
        # Build main content and sidebar
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
        elements.append(ModernSectionHeader('PROFESSIONAL SUMMARY', 4.9*inch))
        elements.append(Spacer(1, 0.05*inch))
        elements.append(Paragraph(self.data['profile'], self.styles['CompactMainText']))
        elements.append(Spacer(1, 0.05*inch))
        
        # Work History
        elements.append(ModernSectionHeader('WORK HISTORY', 4.9*inch))
        elements.append(Spacer(1, 0.05*inch))
        
        for i, exp in enumerate(self.data['experience']):
            elements.append(Paragraph(
                f"<b>{exp['title']}</b> - {exp['company']}", 
                self.styles['CompactJobTitle']
            ))
            
            elements.append(Paragraph(
                f"{exp.get('location', 'Remote')} | {exp['duration']}", 
                self.styles['CompactCompanyDate']
            ))
            
            for ach in exp['achievements']:
                if isinstance(ach, dict):
                    text = f"• <b>{ach['category']}:</b> {ach['description']}"
                else:
                    text = f"• {ach}"
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
        """RIGHT - Sidebar with DYNAMIC skills from JSON"""
        elements = []
        contact = self.data['personal_info']['contact']
        
        elements.append(Spacer(1, 0.05*inch))
        
        # CONTACT
        elements.append(ModernSectionHeader('CONTACT', 2.2*inch))
        elements.append(Spacer(1, 0.04*inch))
        
        email = contact['email']
        elements.append(Paragraph(
            f'<b>Email:</b> <a href="mailto:{email}" color="#1a7f7a"><u>{email}</u></a>', 
            self.styles['CompactSidebarText']
        ))
        elements.append(Paragraph(f"<b>Phone:</b> {contact['phone']}", self.styles['CompactSidebarText']))
        elements.append(Paragraph(f"<b>Location:</b> {contact['location']}", self.styles['CompactSidebarText']))
        
        if contact.get('linkedin'):
            linkedin_url = contact['linkedin']
            if not linkedin_url.startswith('http'):
                linkedin_url = f"https://www.linkedin.com/in/{linkedin_url}"
            elements.append(Paragraph(
                f'<b>LinkedIn:</b> <a href="{linkedin_url}" color="#1a7f7a"><u>Profile</u></a>', 
                self.styles['CompactSidebarText']
            ))
        
        elements.append(Spacer(1, 0.04*inch))
        
        # ✅ SKILLS - READ FROM JSON (DYNAMIC)
        elements.append(ModernSectionHeader('SKILLS', 2.2*inch))
        elements.append(Spacer(1, 0.04*inch))
        
        skills_data = self.data.get('skills', {})
        
        # Tools & Technologies
        if 'tools_and_technologies' in skills_data and skills_data['tools_and_technologies']:
            tools_list = ', '.join(skills_data['tools_and_technologies'])
            elements.append(Paragraph(
                f"<b>Tools & Technologies:</b> {tools_list}", 
                self.styles['CompactSkills']
            ))
        
        # Business Analysis
        if 'business_analysis' in skills_data and skills_data['business_analysis']:
            ba_list = ', '.join(skills_data['business_analysis'])
            elements.append(Paragraph(
                f"<b>Business Analysis:</b> {ba_list}", 
                self.styles['CompactSkills']
            ))
        
        # Document Writing
        if 'document_writing' in skills_data and skills_data['document_writing']:
            doc_list = ', '.join(skills_data['document_writing'])
            elements.append(Paragraph(
                f"<b>Document Writing:</b> {doc_list}", 
                self.styles['CompactSkills']
            ))
        
        # Agile Ceremonies
        if 'agile_ceremonies' in skills_data and skills_data['agile_ceremonies']:
            agile_list = ', '.join(skills_data['agile_ceremonies'])
            elements.append(Paragraph(
                f"<b>Agile Ceremonies:</b> {agile_list}", 
                self.styles['CompactSkills']
            ))
        
        # Soft Skills
        if 'soft_skills' in skills_data and skills_data['soft_skills']:
            soft_list = ', '.join(skills_data['soft_skills'])
            elements.append(Paragraph(
                f"<b>Soft Skills:</b> {soft_list}", 
                self.styles['CompactSkills']
            ))
        
        elements.append(Spacer(1, 0.04*inch))
        
        # EDUCATION
        elements.append(ModernSectionHeader('EDUCATION', 2.2*inch))
        elements.append(Spacer(1, 0.04*inch))
        for edu in self.data['education']:
            elements.append(Paragraph(f"<b>{edu['institution']}</b>", self.styles['CompactSidebarText']))
            elements.append(Paragraph(edu['degree'], self.styles['CompactSidebarText']))
            elements.append(Paragraph(f"{edu['start_year']}-{edu['end_year']}", self.styles['CompactSidebarText']))
            elements.append(Spacer(1, 0.02*inch))
        
        # CERTIFICATIONS
        elements.append(ModernSectionHeader('CERTIFICATIONS', 2.2*inch))
        elements.append(Spacer(1, 0.04*inch))
        for cert in self.data['certifications']:
            elements.append(Paragraph(f"<b>{cert['name']}</b>", self.styles['CompactSidebarText']))
            elements.append(Paragraph(f"{cert['date']}", self.styles['CompactSidebarText']))
            elements.append(Spacer(1, 0.02*inch))
        
        return Table([[elem] for elem in elements], colWidths=[2.3*inch], style=TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'), 
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0)
        ]))


# Export as ResumeBuilder for backward compatibility
ResumeBuilder = CompactStreamlinedBuilder
