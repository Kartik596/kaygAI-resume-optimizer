"""
Resume Optimizer - Complete Production Version with PDF Upload
Features: PDF parsing, AI suggestions, drag-and-drop, live preview, detailed analysis
"""
import streamlit as st
from streamlit_sortables import sort_items
import json
from pathlib import Path
from datetime import datetime
import base64

from src.config.settings import settings
from src.analyzers import PIISanitizer, JDAnalyzer, ResumeMatcher
from src.agents import ResumeOptimizerAgent
from src.utils import ResumeMerger
from src.builders.resume_builder import ResumeBuilder


# Page config
st.set_page_config(
    page_title="Resume Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mobile-optimized CSS
st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 8px; height: 3em; font-weight: 600;}
    .stTextArea textarea {font-size: 14px;}
    @media (max-width: 768px) {
        .stDeployButton, footer {display: none;}
        .row-widget.stHorizontal {flex-direction: column !important;}
        .row-widget.stHorizontal > div {width: 100% !important; margin-bottom: 1rem;}
        .stButton>button {height: 3.5em; font-size: 18px;}
        .stTextArea textarea {font-size: 17px !important; min-height: 120px;}
        [data-testid="stMetricValue"] {font-size: 1.8rem !important;}
        iframe {height: 70vh !important;}
        .block-container {padding: 1rem !important;}
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.jd_text = ""
    st.session_state.suggestions = []
    st.session_state.selected_ids = []
    st.session_state.edited_suggestions = {}
    st.session_state.agent = None
    st.session_state.match_analysis = None
    st.session_state.original_resume = None
    st.session_state.sanitized_resume = None
    st.session_state.jd_requirements = None
    st.session_state.preview_resume = None


def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def safe_str(value):
    if isinstance(value, list):
        return ', '.join(str(v) for v in value)
    return str(value)


def generate_pdf_preview(resume_data):
    try:
        temp_json = settings.OUTPUT_DIR / "preview_temp.json"
        with open(temp_json, 'w', encoding='utf-8') as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)
        
        temp_pdf = settings.OUTPUT_DIR / "preview_temp.pdf"
        builder = ResumeBuilder(str(temp_json))
        builder.generate_pdf(str(temp_pdf))
        
        with open(temp_pdf, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        st.error(f"Preview error: {e}")
        return None


# SIDEBAR
with st.sidebar:
    st.title("📄 Resume Optimizer")
    st.markdown("---")
    
    steps = ["Setup", "Analysis", "Select", "Edit", "Preview", "Download"]
    current_step = st.session_state.get('step', 1)
    
    st.write("**Progress:**")
    for i, step_name in enumerate(steps, 1):
        if i < current_step:
            st.write(f"✅ {step_name}")
        elif i == current_step:
            st.write(f"🔵 **{step_name}**")
        else:
            st.write(f"⚪ {step_name}")
    
    st.markdown("---")
    
    if st.session_state.match_analysis:
        st.metric("Match Score", f"{st.session_state.match_analysis['overall_match_score']}/100")
    
    st.markdown("---")
    
    if st.button("🔄 Start Over"):
        reset_app()

# STEP 1 - FIXED with caching
if st.session_state.step == 1:
    st.title("🚀 Resume Optimizer")
    st.markdown("Optimize your resume for any job!")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Your Resume")
        
        uploaded_pdf = st.file_uploader(
            "Upload your resume (PDF)", 
            type=['pdf'],
            help="🔒 Your personal info is extracted locally - never sent to AI",
            key="pdf_uploader"
        )
        
        # ✅ CACHE LOGIC - Only parse if NOT already parsed
        if uploaded_pdf and 'uploaded_file_name' not in st.session_state:
            # First time upload
            st.session_state.uploaded_file_name = uploaded_pdf.name
            
            with st.spinner("🤖 Parsing resume... (10-15 seconds)"):
                try:
                    from src.parsers.pdf_to_json import PDFResumeParser
                    
                    parser = PDFResumeParser()
                    resume_data = parser.parse_pdf_resume(uploaded_pdf)
                    
                    st.success(f"✅ Parsed: {resume_data['personal_info']['name']}")
                    st.session_state.original_resume = resume_data
                    
                    st.info("🔒 Your name, email, and phone were extracted **locally** (no AI)")
                    
                    with st.expander("👀 Preview extracted data"):
                        st.json(resume_data)
                
                except Exception as e:
                    st.error(f"❌ Failed to parse: {str(e)}")
                    st.info("💡 Try a clearer PDF")
                    # Clear cache on error
                    if 'uploaded_file_name' in st.session_state:
                        del st.session_state.uploaded_file_name
                    st.stop()
        
        elif uploaded_pdf and st.session_state.uploaded_file_name == uploaded_pdf.name:
            # Already parsed - just show cached result
            if st.session_state.original_resume:
                st.success(f"✅ Using cached: {st.session_state.original_resume['personal_info']['name']}")
                
                with st.expander("👀 View parsed data"):
                    st.json(st.session_state.original_resume)
        
        elif uploaded_pdf and st.session_state.uploaded_file_name != uploaded_pdf.name:
            # Different file uploaded - reparse
            st.session_state.uploaded_file_name = uploaded_pdf.name
            
            with st.spinner("🤖 Parsing new resume... (10-15 seconds)"):
                try:
                    from src.parsers.pdf_to_json import PDFResumeParser
                    
                    parser = PDFResumeParser()
                    resume_data = parser.parse_pdf_resume(uploaded_pdf)
                    
                    st.success(f"✅ Parsed: {resume_data['personal_info']['name']}")
                    st.session_state.original_resume = resume_data
                    
                    st.info("🔒 Your name, email, and phone were extracted **locally** (no AI)")
                    
                    with st.expander("👀 Preview extracted data"):
                        st.json(resume_data)
                
                except Exception as e:
                    st.error(f"❌ Failed to parse: {str(e)}")
                    st.info("💡 Try a clearer PDF")
                    st.stop()
        
        elif settings.RESUME_MASTER_JSON.exists():
            # Fallback for local dev
            with open(settings.RESUME_MASTER_JSON, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
            st.info(f"👤 Using saved: {resume_data['personal_info']['name']}")
            st.session_state.original_resume = resume_data
        
        else:
            st.warning("⚠️ Please upload your resume PDF")
            st.stop()
    
    with col2:
        st.subheader("📋 Job Description")
        jd_text = st.text_area("Paste JD", height=300, placeholder="Paste job description...", key="jd_input")
        st.session_state.jd_text = jd_text
    
    st.markdown("---")
    
    if st.button("🔍 Analyze", type="primary", use_container_width=True):
        if not st.session_state.original_resume:
            st.error("⚠️ Upload resume first!")
        elif not jd_text.strip():
            st.error("⚠️ Paste job description!")
        else:
            with st.spinner("🤖 Analyzing (20-30s)..."):
                try:
                    sanitizer = PIISanitizer()
                    st.session_state.sanitized_resume = sanitizer.sanitize_resume(st.session_state.original_resume)
                    
                    jd_analyzer = JDAnalyzer()
                    jd_requirements = jd_analyzer.analyze_jd(jd_text)
                    st.session_state.jd_requirements = jd_requirements
                    
                    matcher = ResumeMatcher()
                    match_analysis = matcher.calculate_match(st.session_state.sanitized_resume, jd_requirements)
                    st.session_state.match_analysis = match_analysis
                    
                    agent = ResumeOptimizerAgent()
                    suggestions = agent.analyze_and_generate_suggestions(
                        st.session_state.sanitized_resume, jd_requirements, match_analysis
                    )
                    
                    st.session_state.agent = agent
                    st.session_state.suggestions = suggestions
                    st.session_state.step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

# STEP 2 - Analysis & Selection
elif st.session_state.step == 2:
    st.title("📋 AI Suggestions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall", f"{st.session_state.match_analysis['overall_match_score']}/100")
    with col2:
        st.metric("Skills", f"{st.session_state.match_analysis['skills_match']['score']}/100")
    with col3:
        st.metric("Keywords", f"{st.session_state.match_analysis['keyword_coverage']['score']}/100")
    
    st.markdown("---")
    st.subheader("✅ Select Suggestions")
    
    categories = {}
    for sug in st.session_state.suggestions:
        cat = sug['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(sug)
    
    for category, suggestions in categories.items():
        with st.expander(f"📁 {category} ({len(suggestions)})", expanded=True):
            for sug in suggestions:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                
                selected = st.checkbox(
                    f"{priority_emoji[sug['priority']]} {sug['description'][:80]}",
                    key=f"select_{sug['id']}",
                    value=sug['id'] in st.session_state.selected_ids,
                    help=f"💡 {sug['reason']}"
                )
                
                if selected and sug['id'] not in st.session_state.selected_ids:
                    st.session_state.selected_ids.append(sug['id'])
                elif not selected and sug['id'] in st.session_state.selected_ids:
                    st.session_state.selected_ids.remove(sug['id'])
                
                value = safe_str(sug['value'])
                if len(value) > 100:
                    value = value[:100] + "..."
                st.caption(f"✏️ {value}")
                st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ All"):
            st.session_state.selected_ids = [s['id'] for s in st.session_state.suggestions]
            st.rerun()
    with col2:
        if st.button("🔴 High"):
            st.session_state.selected_ids = [s['id'] for s in st.session_state.suggestions if s['priority'] == 'high']
            st.rerun()
    with col3:
        if st.button("❌ Clear"):
            st.session_state.selected_ids = []
            st.rerun()
    
    st.markdown("---")
    st.info(f"✅ {len(st.session_state.selected_ids)} selected")
    
    if st.button("➡️ Continue", type="primary", use_container_width=True):
        if not st.session_state.selected_ids:
            st.warning("⚠️ Select at least one")
        else:
            st.session_state.step = 3
            st.rerun()


# STEP 3 - Edit Suggestions
elif st.session_state.step == 3:
    st.title("✏️ Edit Suggestions")
    
    selected_suggestions = [s for s in st.session_state.suggestions if s['id'] in st.session_state.selected_ids]
    
    st.subheader("🔄 Reorder")
    suggestion_texts = [f"{s['id']}. [{s['category']}] {s['description']}" for s in selected_suggestions]
    ordered_texts = sort_items(suggestion_texts, direction='vertical', key='reorder')
    ordered_ids = [int(text.split('.')[0]) for text in ordered_texts]
    
    st.markdown("---")
    st.subheader("📝 Edit Content")
    
    for sug_id in ordered_ids:
        sug = next(s for s in selected_suggestions if s['id'] == sug_id)
        
        with st.expander(f"✏️ [{sug['category']}] {sug['description'][:50]}...", expanded=False):
            original = safe_str(sug['value'])
            st.markdown(f"**Original:** {original}")
            
            edited = st.text_area("Edit:", value=st.session_state.edited_suggestions.get(sug_id, original), key=f"edit_{sug_id}", height=100)
            st.session_state.edited_suggestions[sug_id] = edited
            
            if edited != original:
                st.info("✏️ Modified")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("➡️ Preview", type="primary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

# STEP 4 - Live Preview
elif st.session_state.step == 4:
    st.title("👁️ Live Preview")
    
    # Generate preview if not exists
    if st.session_state.preview_resume is None:
        with st.spinner("Preparing..."):
            try:
                for sug_id, edited_value in st.session_state.edited_suggestions.items():
                    st.session_state.agent.modify_suggestion(sug_id, edited_value)
                
                st.session_state.agent.select_suggestions(st.session_state.selected_ids)
                updated_sanitized = st.session_state.agent.generate_updated_resume()
                
                merger = ResumeMerger()
                st.session_state.preview_resume = merger.merge(st.session_state.original_resume, updated_sanitized)
            except Exception as e:
                st.error(f"❌ Failed to generate preview: {str(e)}")
                st.session_state.preview_resume = None
    
    # ✅ CRITICAL: Null check IMMEDIATELY after generation
    if st.session_state.preview_resume is None:
        st.error("❌ Failed to generate preview. Please go back and try again.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Selection"):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("🔄 Start Over"):
                reset_app()
        st.stop()  # STOPS execution here
    
    # NOW safe to use preview_resume
    col_edit, col_preview = st.columns([1, 1])
    
    with col_edit:
        st.subheader("📝 Edit")
        
        # Profile
        profile = st.session_state.preview_resume.get('profile', '')
        if profile:
            with st.expander("📄 Summary", expanded=True):
                new_profile = st.text_area("Profile", value=profile, height=150, key="live_profile", label_visibility="collapsed")
                st.session_state.preview_resume['profile'] = new_profile
        
        # Skills
        skills_dict = st.session_state.preview_resume.get('skills', {})
        if skills_dict:
            with st.expander("🛠️ Skills", expanded=True):
                for category_name, skills_list in skills_dict.items():
                    display_name = category_name.replace('_', ' ').title()
                    skills_str = ', '.join(skills_list) if isinstance(skills_list, list) else str(skills_list)
                    
                    edited_skills = st.text_area(
                        display_name,
                        value=skills_str,
                        height=80,
                        key=f"live_skills_{category_name}",
                        label_visibility="visible"
                    )
                    
                    st.session_state.preview_resume['skills'][category_name] = [
                        s.strip() for s in edited_skills.split(',') if s.strip()
                    ]
        
        # Experience
        experiences = st.session_state.preview_resume.get('experience', [])
        if experiences:
            with st.expander("💼 Experience", expanded=True):
                for exp_idx, exp in enumerate(experiences):
                    title = exp.get('title', 'Position')
                    company = exp.get('company', 'Company')
                    
                    st.markdown(f"**{title}** at {company}")
                    
                    achievements = exp.get('achievements', [])
                    for ach_idx, ach in enumerate(achievements):
                        col_ach, col_del = st.columns([0.9, 0.1])
                        
                        with col_ach:
                            if isinstance(ach, dict):
                                desc = ach.get('description', '')
                            else:
                                desc = str(ach)
                            
                            new_desc = st.text_area(
                                f"Achievement {ach_idx + 1}",
                                value=desc,
                                height=80,
                                key=f"live_ach_{exp_idx}_{ach_idx}",
                                label_visibility="collapsed"
                            )
                            
                            if isinstance(ach, dict):
                                exp['achievements'][ach_idx]['description'] = new_desc
                            else:
                                exp['achievements'][ach_idx] = new_desc
                        
                        with col_del:
                            if st.button("🗑️", key=f"del_{exp_idx}_{ach_idx}"):
                                exp['achievements'].pop(ach_idx)
                                st.rerun()
                    
                    # ADD button
                    if st.button(f"➕ Add Achievement to {company}", key=f"add_ach_{exp_idx}", use_container_width=True):
                        exp['achievements'].append({
                            "category": "",
                            "description": "New achievement - edit this text"
                        })
                        st.rerun()
                    
                    if exp_idx < len(experiences) - 1:
                        st.markdown("---")
    
    with col_preview:
        st.subheader("👁️ Preview")
        
        with st.spinner("Rendering..."):
            pdf_base64 = generate_pdf_preview(st.session_state.preview_resume)
        
        if pdf_base64:
            st.markdown(f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="900px" style="border:1px solid #ddd;"></iframe>', unsafe_allow_html=True)
        else:
            st.error("❌ Failed to generate PDF preview")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("🔄 Reset"):
            st.session_state.preview_resume = None
            st.rerun()
    with col3:
        if st.button("✅ Download", type="primary"):
            st.session_state.step = 5
            st.rerun()

# STEP 5 - Download & Analysis
elif st.session_state.step == 5:
    st.title("🎉 Download & Analysis")
    
    st.subheader("📝 Name Your Resume")
    company_name = st.text_input("Job name", placeholder="e.g., google-engineer")
    if not company_name:
        company_name = "custom-job"
    company_name = company_name.lower().replace(' ', '-').replace('_', '-')
    
    st.markdown("---")
    
    if st.button("💾 Generate Final Resume", type="primary", use_container_width=True):
        with st.spinner("Generating..."):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = settings.OUTPUT_DIR
                output_dir.mkdir(parents=True, exist_ok=True)
                
                final_json = output_dir / f"resume_final_{company_name}_{timestamp}.json"
                final_pdf = output_dir / f"resume_final_{company_name}_{timestamp}.pdf"
                
                with open(final_json, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.preview_resume, f, indent=2, ensure_ascii=False)
                
                builder = ResumeBuilder(str(final_json))
                builder.generate_pdf(str(final_pdf))
                
                st.success("✅ Resume Generated!")
                st.balloons()
                
                # Download buttons
                with open(final_pdf, 'rb') as f:
                    st.download_button(
                        "📥 Download PDF",
                        f.read(),
                        file_name=f"resume_{company_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                with open(final_json, 'r') as f:
                    st.download_button(
                        "📥 Download JSON",
                        f.read(),
                        file_name=f"resume_{company_name}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                # Before/After Analysis
                st.markdown("---")
                st.subheader("📊 Before vs After Analysis")
                
                with st.spinner("Analyzing improvement..."):
                    sanitizer = PIISanitizer()
                    matcher = ResumeMatcher()
                    
                    new_sanitized = sanitizer.sanitize_resume(st.session_state.preview_resume)
                    new_match = matcher.calculate_match(new_sanitized, st.session_state.jd_requirements)
                    
                    old_match = st.session_state.match_analysis
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Overall Match",
                            f"{new_match['overall_match_score']}/100",
                            f"+{new_match['overall_match_score'] - old_match['overall_match_score']}"
                        )
                    
                    with col2:
                        st.metric(
                            "Skills Match",
                            f"{new_match['skills_match']['score']}/100",
                            f"+{new_match['skills_match']['score'] - old_match['skills_match']['score']}"
                        )
                    
                    with col3:
                        st.metric(
                            "Keyword Coverage",
                            f"{new_match['keyword_coverage']['score']}/100",
                            f"+{new_match['keyword_coverage']['score'] - old_match['keyword_coverage']['score']}"
                        )
                    
                    st.success(f"🎯 Your resume match improved by {new_match['overall_match_score'] - old_match['overall_match_score']} points!")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    
    if st.button("🔄 Optimize Another Resume"):
        reset_app()
