"""
Analyze resume against job description from file
Reads: data/job_description.txt
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings
from src.analyzers import PIISanitizer, JDAnalyzer, ResumeMatcher

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🎯 RESUME JD ANALYZER")
    print("="*70)
    
    # Show config
    print(f"\nConfiguration:")
    print(f"  API Key: {settings.OPENAI_API_KEY[:20]}...{settings.OPENAI_API_KEY[-4:]}")
    print(f"  JD Model: {settings.MODEL_JD_ANALYZER}")
    print(f"  Matcher Model: {settings.MODEL_RESUME_MATCHER}")
    
    # Get JD file path
    jd_file = settings.DATA_DIR / "job_description.txt"
    
    # Check file exists
    if not jd_file.exists():
        print(f"\n❌ ERROR: {jd_file} not found!")
        print(f"\nCreate the file and paste your job description in it.")
        sys.exit(1)
    
    # Read JD
    print(f"\n📄 Reading JD from: {jd_file}")
    with open(jd_file, 'r', encoding='utf-8') as f:
        jd_text = f.read().strip()
    
    if not jd_text:
        print(f"\n❌ ERROR: JD file is empty!")
        sys.exit(1)
    
    print(f"✅ JD loaded: {len(jd_text)} characters")
    
    # Show preview
    print(f"\n{'─'*70}")
    print("JD PREVIEW:")
    print(f"{'─'*70}")
    print(jd_text[:500])
    if len(jd_text) > 500:
        print("\n... (truncated)")
    print(f"{'─'*70}\n")
    
    # Load resume
    print(f"📄 Loading resume: {settings.RESUME_MASTER_JSON}")
    with open(settings.RESUME_MASTER_JSON, 'r') as f:
        resume_data = json.load(f)
    
    # Sanitize
    print("🔒 Removing PII...")
    sanitizer = PIISanitizer()
    sanitized_resume = sanitizer.sanitize_resume(resume_data)
    
    # Analyze JD
    print("🔍 Analyzing JD with AI...")
    jd_analyzer = JDAnalyzer()
    jd_requirements = jd_analyzer.analyze_jd(jd_text)
    
    print(f"\n✅ JD Analysis:")
    print(f"   Role: {jd_requirements.get('role_title')}")
    print(f"   Industry: {jd_requirements.get('industry')}")
    print(f"   Skills: {len(jd_requirements.get('required_skills', []))}")
    print(f"   Keywords: {len(jd_requirements.get('keywords', []))}")
    
    # Match
    print("\n🎯 Matching resume vs JD...")
    matcher = ResumeMatcher()
    match_analysis = matcher.calculate_match(sanitized_resume, jd_requirements)
    
    # Results
    print("\n" + "="*70)
    print("📊 RESULTS")
    print("="*70)
    print(f"\n🎯 Overall Match Score: {match_analysis['overall_match_score']}/100\n")
    
    print(f"Skills Match: {match_analysis['skills_match']['score']}/100")
    print(f"  Matched: {len(match_analysis['skills_match']['matched'])}")
    print(f"  Missing: {len(match_analysis['skills_match']['missing'])}")
    
    if match_analysis['skills_match']['missing']:
        print(f"\n  ⚠️ Missing Skills:")
        for skill in match_analysis['skills_match']['missing'][:5]:
            print(f"     • {skill}")
    
    print(f"\n💡 Top Suggestions:")
    for i, sug in enumerate(match_analysis['improvement_suggestions'][:3], 1):
        print(f"  {i}. {sug}")
    
    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = settings.OUTPUT_DIR / f"analysis_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'jd_requirements': jd_requirements,
            'match_analysis': match_analysis
        }, f, indent=2)
    
    print(f"\n💾 Full report: {output_file}")
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
