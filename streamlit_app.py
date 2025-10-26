"""
Resume Optimizer - Complete Production Version
Features: AI suggestions, drag-and-drop, live preview, detailed analysis
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

# CSS
st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 8px; height: 3em; font-weight: 600;}
    .stTextArea textarea {font-size: 14px;}
    .priority-high {border-left-color: #ff4444;}
    .priority-medium {border-left-color: #ffaa00;}
    .priority-low {border-left-color: #44ff44;}
    @media (max-width: 768px) {.stDeployButton, footer {display: none;}}
</style>
""", unsafe_allow_html=True)


# Initialize
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
    
    steps = ["Setup", "Analysis", "Select", "Edit", "Live Preview", "Download"]
    current_step = st.session_state.get('step', 1)
    
    st.write("**Progress:**")
    for i, step_name in enumerate(steps, 1):
        if i < current_step:
            st.write(f"✅ {step_name}")
        elif i == current_step:
            st.write(f"🔵 **{step_name}** ← Current")
        else:
            st.write(f"⚪ {step_name}")
    
    st.markdown("---")
    
    if st.session_state.match_analysis:
        st.metric("Match Score", f"{st.session_state.match_analysis['overall_match_score']}/100")
    
    st.markdown("---")
    
    if st.button("🔄 Start Over"):
        reset_app()


# STEP 1
if st.session_state.step == 1:
    st.title("🚀 Resume Optimizer")
    st.markdown("Optimize your resume for any job!")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Your Resume")
        if settings.RESUME_MASTER_JSON.exists():
            st.success(f"✅ {settings.RESUME_MASTER_JSON.name}")
            with open(settings.RESUME_MASTER_JSON, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
            st.info(f"👤 {resume_data['personal_info']['name']}")
            st.session_state.original_resume = resume_data
        else:
            st.error("❌ Resume not found")
            st.stop()
    
    with col2:
        st.subheader("📋 Job Description")
        jd_text = st.text_area("Paste JD", height=300, placeholder="Paste job description...", key="jd_input")
        st.session_state.jd_text = jd_text
    
    st.markdown("---")
    
    if st.button("🔍 Analyze", type="primary", use_container_width=True):
        if not jd_text.strip():
            st.error("⚠️ Please paste a job description!")
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


# STEP 2
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


# STEP 3
elif st.session_state.step == 3:
    st.title("✏️ Edit Suggestions")
    
    selected_suggestions = [s for s in st.session_state.suggestions if s['id'] in st.session_state.selected_ids]
    
    st.subheader("🔄 Reorder")
    suggestion_texts = [f"{s['id']}. [{s['category']}] {s['description']}" for s in selected_suggestions]
    ordered_texts = sort_items(suggestion_texts, direction='vertical', key='reorder')
    ordered_ids = [int(text.split('.')[0]) for text in ordered_texts]
    
    st.markdown("---")
    st.subheader("📝 Edit")
    
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


# STEP 4
elif st.session_state.step == 4:
    st.title("👁️ Live Preview")
    
    if st.session_state.preview_resume is None:
        with st.spinner("Preparing..."):
            for sug_id, edited_value in st.session_state.edited_suggestions.items():
                st.session_state.agent.modify_suggestion(sug_id, edited_value)
            
            st.session_state.agent.select_suggestions(st.session_state.selected_ids)
            updated_sanitized = st.session_state.agent.generate_updated_resume()
            
            merger = ResumeMerger()
            st.session_state.preview_resume = merger.merge(st.session_state.original_resume, updated_sanitized)
    
    col_edit, col_preview = st.columns([1, 1])
    
    with col_edit:
        st.subheader("📝 Edit")
        
        with st.expander("📄 Summary", expanded=True):
            profile = st.text_area("Profile", value=st.session_state.preview_resume['profile'], height=150, key="live_profile", label_visibility="collapsed")
            st.session_state.preview_resume['profile'] = profile
        
        with st.expander("🛠️ Tools", expanded=True):
            tools_str = ', '.join(st.session_state.preview_resume['skills']['tools_and_technologies'])
            tools = st.text_area("Tools", value=tools_str, height=80, key="live_tools", label_visibility="collapsed")
            st.session_state.preview_resume['skills']['tools_and_technologies'] = [s.strip() for s in tools.split(',') if s.strip()]
        
        with st.expander("💼 Experience", expanded=True):
            for exp_idx, exp in enumerate(st.session_state.preview_resume['experience']):
                st.markdown(f"**{exp['title']}**")
                
                for ach_idx, ach in enumerate(exp['achievements']):
                    col_ach, col_del = st.columns([0.9, 0.1])
                    
                    with col_ach:
                        new_desc = st.text_area(f"Ach {ach_idx + 1}", value=ach['description'], height=80, key=f"live_ach_{exp_idx}_{ach_idx}", label_visibility="collapsed")
                        exp['achievements'][ach_idx]['description'] = new_desc
                    
                    with col_del:
                        if st.button("🗑️", key=f"del_{exp_idx}_{ach_idx}"):
                            exp['achievements'].pop(ach_idx)
                            st.rerun()
                
                if exp_idx == 0 and st.button("➕", key=f"add_{exp_idx}"):
                    exp['achievements'].append({'category': 'General', 'description': 'New...'})
                    st.rerun()
                
                if exp_idx < len(st.session_state.preview_resume['experience']) - 1:
                    st.markdown("---")
    
    with col_preview:
        st.subheader("👁️ Preview")
        
        with st.spinner("Rendering..."):
            pdf_base64 = generate_pdf_preview(st.session_state.preview_resume)
        
        if pdf_base64:
            st.markdown(f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="900px" style="border:1px solid #ddd;"></iframe>', unsafe_allow_html=True)
        
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


# STEP 5 - WITH DETAILED ANALYSIS
elif st.session_state.step == 5:
    st.title("🎉 Download & Analysis")
    
    st.subheader("📝 Name Resume")
    company_name = st.text_input("Job name", placeholder="e.g., google-engineer")
    if not company_name:
        company_name = "custom-job"
    company_name = company_name.lower().replace(' ', '-').replace('_', '-')
    
    st.markdown("---")
    
    if st.button("💾 Generate", type="primary", use_container_width=True):
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
                
                st.session_state.final_pdf_path = final_pdf
                st.session_state.final_json_path = final_json
                
                st.success("✅ Done!")
                st.balloons()
                
                # DETAILED ANALYSIS
                st.markdown("---")
                st.subheader("📊 Before vs After Analysis")
                
                with st.spinner("Analyzing..."):
                    sanitizer = PIISanitizer()
                    matcher = ResumeMatcher()
                    
                    new_sanitized = sanitizer.sanitize_resume(st.session_state.preview_resume)
                    new_match = matcher.calculate_match(new_sanitized, st.session_state.jd_requirements)
                    
                    old_match = st.session_state.match_analysis
                    
                    # Overall
                    st.markdown("### 🎯 Overall Score")
                    col1, col2, col3 = st.columns(3)
                    
                    old_score = old_match['overall_match_score']
                    new_score = new_match['overall_match_score']
                    improvement = new_score - old_score
                    
                    with col1:
                        st.metric("Before", f"{old_score}/100")
                    with col2:
                        st.metric("After", f"{new_score}/100")
                    with col3:
                        st.metric("Improvement", f"+{improvement}", delta=f"{improvement} pts")
                    
                    # Breakdown
                    st.markdown("---")
                    st.markdown("### 📈 Detailed Breakdown")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🛠️ Skills**")
                        old_skills = old_match['skills_match']['score']
                        new_skills = new_match['skills_match']['score']
                        st.metric("Skills Score", f"{new_skills}/100", f"+{new_skills - old_skills}")
                        
                        with st.expander("Matched skills"):
                            matched = new_match['skills_match'].get('matched', [])
                            st.write(f"✅ {len(matched)} matched")
                            for s in matched[:10]:
                                st.write(f"• {s}")
                            
                            missing = new_match['skills_match'].get('missing', [])
                            if missing:
                                st.write(f"❌ {len(missing)} missing")
                                for s in missing[:5]:
                                    st.write(f"• {s}")
                    
                    with col2:
                        st.markdown("**🔑 Keywords**")
                        old_kw = old_match['keyword_coverage']['score']
                        new_kw = new_match['keyword_coverage']['score']
                        st.metric("Keyword Score", f"{new_kw}/100", f"+{new_kw - old_kw}")
                        
                        with st.expander("Matched keywords"):
                            matched_kw = new_match['keyword_coverage'].get('matched_keywords', [])
                            st.write(f"✅ {len(matched_kw)} matched")
                            for k in matched_kw[:10]:
                                st.write(f"• {k}")
                            
                            missing_kw = new_match['keyword_coverage'].get('missing_keywords', [])
                            if missing_kw:
                                st.write(f"❌ {len(missing_kw)} missing")
                                for k in missing_kw[:5]:
                                    st.write(f"• {k}")
                    
                    # Changes
                    st.markdown("---")
                    st.markdown("### ✨ Applied Changes")
                    
                    for i, sug_id in enumerate(st.session_state.selected_ids[:5], 1):
                        sug = next(s for s in st.session_state.suggestions if s['id'] == sug_id)
                        st.write(f"{i}. **[{sug['category']}]** {sug['description']}")
                    
                    if len(st.session_state.selected_ids) > 5:
                        st.write(f"... +{len(st.session_state.selected_ids) - 5} more")
                    
                    # Recommendations
                    st.markdown("---")
                    st.markdown("### 💡 Assessment")
                    
                    if new_score >= 85:
                        st.success("🎉 Excellent! Well-optimized.")
                    elif new_score >= 70:
                        st.info("👍 Good match!")
                    else:
                        st.warning("⚠️ Room for improvement.")
                    
                    # Save report
                    report = {
                        "timestamp": datetime.now().isoformat(),
                        "job": company_name,
                        "before": old_score,
                        "after": new_score,
                        "improvement": improvement,
                        "changes": len(st.session_state.selected_ids),
                        "breakdown": {
                            "skills": {"before": old_skills, "after": new_skills},
                            "keywords": {"before": old_kw, "after": new_kw}
                        }
                    }
                    
                    report_path = output_dir / f"analysis_{company_name}_{timestamp}.json"
                    with open(report_path, 'w') as f:
                        json.dump(report, f, indent=2)
                    
                    st.session_state.report_path = report_path
                
                # Downloads
                st.markdown("---")
                st.subheader("📥 Download")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    with open(final_pdf, 'rb') as f:
                        st.download_button("📄 PDF", f, file_name=final_pdf.name, mime="application/pdf", use_container_width=True)
                
                with col2:
                    with open(final_json, 'r') as f:
                        st.download_button("📋 JSON", f, file_name=final_json.name, mime="application/json", use_container_width=True)
                
                with col3:
                    if hasattr(st.session_state, 'report_path'):
                        with open(st.session_state.report_path, 'r') as f:
                            st.download_button("📊 Report", f, file_name=st.session_state.report_path.name, mime="application/json", use_container_width=True)
                
                st.markdown("---")
                
                if st.button("🔄 New Resume", use_container_width=True):
                    reset_app()
                
            except Exception as e:
                st.error(f"❌ {e}")
