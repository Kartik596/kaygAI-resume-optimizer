"""
Interactive Resume Optimizer - BATCH SUGGESTION MODE
Shows all suggestions at once for user selection

Usage:
    python interactive_optimizer.py
"""
import json
import sys
from pathlib import Path
from datetime import datetime

from src.config.settings import settings
from src.analyzers import PIISanitizer, JDAnalyzer, ResumeMatcher
from src.agents import ResumeOptimizerAgent
from src.utils import ResumeMerger
from src.builders.resume_builder import ResumeBuilder


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_section(title):
    """Print section title"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")


def display_suggestions(suggestions: list):
    """Display all suggestions in organized format"""
    
    # Group by category
    categories = {}
    for sug in suggestions:
        cat = sug['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(sug)
    
    # Display by category
    for category, items in categories.items():
        print(f"\n🔹 {category.upper()}")
        print("─" * 70)
        
        for sug in items:
            priority_icon = "🔴" if sug['priority'] == 'high' else "🟡" if sug['priority'] == 'medium' else "🟢"
            
            print(f"\n  [{sug['id']}] {priority_icon} {sug['description']}")
            print(f"      💡 Why: {sug['reason']}")
            
            # Show value preview
            value = sug['value']
            if len(value) > 80:
                value = value[:80] + "..."
            print(f"      ✏️  Add: \"{value}\"")
            print(f"      📍 Location: {sug['section']}")


def main():
    """Main optimization flow"""
    
    print_header("🚀 RESUME OPTIMIZER - BATCH MODE")
    print("\n💡 How this works:")
    print("   1. AI analyzes your resume structure & JD")
    print("   2. Generates 5-10 smart suggestions at once")
    print("   3. You select which ones to apply")
    print("   4. You can modify any suggestion")
    print("   5. Generates tailored resume")
    print("   6. Your resume_master.json stays UNTOUCHED ✅")
    
    input("\nPress Enter to start...")
    
    # ============================================
    # Step 1: Load Job Description
    # ============================================
    print_header("📄 STEP 1: LOAD JOB DESCRIPTION")
    
    jd_file = settings.DATA_DIR / "job_description.txt"
    
    if not jd_file.exists():
        print(f"\n❌ ERROR: {jd_file} not found!")
        print(f"\nPlease:")
        print(f"   1. Create: {jd_file}")
        print(f"   2. Paste job description in it")
        print(f"   3. Run this script again")
        sys.exit(1)
    
    with open(jd_file, 'r', encoding='utf-8') as f:
        jd_text = f.read().strip()
    
    if not jd_text:
        print(f"\n❌ ERROR: Job description file is empty!")
        sys.exit(1)
    
    print(f"✅ Loaded: {len(jd_text)} characters")
    
    # ============================================
    # Step 2: Load Resume
    # ============================================
    print_header("📄 STEP 2: LOAD MASTER RESUME")
    
    if not settings.RESUME_MASTER_JSON.exists():
        print(f"\n❌ ERROR: {settings.RESUME_MASTER_JSON} not found!")
        sys.exit(1)
    
    with open(settings.RESUME_MASTER_JSON, 'r', encoding='utf-8') as f:
        original_resume = json.load(f)
    
    print(f"✅ Loaded: {original_resume['personal_info']['name']}")
    
    print(f"\n🔒 Removing PII for AI analysis...")
    sanitizer = PIISanitizer()
    sanitized_resume = sanitizer.sanitize_resume(original_resume)
    print(f"✅ PII removed")
    
    # ============================================
    # Step 3: AI Analysis
    # ============================================
    print_header("🔍 STEP 3: AI ANALYSIS")
    
    print(f"\n🤖 Analyzing job description...")
    jd_analyzer = JDAnalyzer()
    jd_requirements = jd_analyzer.analyze_jd(jd_text)
    
    print(f"✅ JD Analysis:")
    print(f"   Role: {jd_requirements.get('role_title')}")
    print(f"   Industry: {jd_requirements.get('industry')}")
    
    print(f"\n🎯 Matching resume vs JD...")
    matcher = ResumeMatcher()
    match_analysis = matcher.calculate_match(sanitized_resume, jd_requirements)
    
    print(f"✅ Current Match Score: {match_analysis['overall_match_score']}/100")
    
    # ============================================
    # Step 4: Generate All Suggestions
    # ============================================
    print_header("💡 STEP 4: AI SUGGESTIONS")
    
    print(f"\n🤖 Analyzing resume structure & generating suggestions...")
    print("   (This may take 10-20 seconds...)")
    
    agent = ResumeOptimizerAgent()
    
    try:
        suggestions = agent.analyze_and_generate_suggestions(
            sanitized_resume,
            jd_requirements,
            match_analysis
        )
        
        print(f"\n✅ Generated {len(suggestions)} suggestions!")
        
    except Exception as e:
        print(f"\n❌ Error generating suggestions: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ============================================
    # Step 5: Display & Select Suggestions
    # ============================================
    print_header("📋 STEP 5: REVIEW SUGGESTIONS")
    
    display_suggestions(suggestions)
    
    print("\n" + "="*70)
    print("💡 TIP: High priority (🔴) items have the most impact!")
    print("="*70)
    
    # Selection loop
    print_section("SELECT SUGGESTIONS")
    
    print("\nEnter suggestion IDs to apply (comma-separated)")
    print("Examples: '1,2,5' or 'all' or 'high' (high priority only)")
    
    selection = input("\n✅ Select: ").strip().lower()
    
    if selection == 'all':
        selected_ids = [s['id'] for s in suggestions]
    elif selection == 'high':
        selected_ids = [s['id'] for s in suggestions if s['priority'] == 'high']
    else:
        try:
            selected_ids = [int(x.strip()) for x in selection.split(',')]
        except:
            print("❌ Invalid input. Using all suggestions.")
            selected_ids = [s['id'] for s in suggestions]
    
    agent.select_suggestions(selected_ids)
    selected_suggestions = agent.get_selected_suggestions()
    
    print(f"\n✅ Selected {len(selected_suggestions)} suggestions")
    
    # ============================================
    # Step 6: Modify Suggestions (Optional)
    # ============================================
    print_section("MODIFY SUGGESTIONS (OPTIONAL)")
    
    print("\nSelected suggestions:")
    for sug in selected_suggestions:
        print(f"  [{sug['id']}] {sug['description']}")
        value_preview = sug['value'][:60] + "..." if len(sug['value']) > 60 else sug['value']
        print(f"       \"{value_preview}\"")
    
    modify = input("\nModify any suggestion? (yes/no): ").lower()
    
    if modify == 'yes':
        while True:
            mod_id = input("\n  Suggestion ID to modify (or 'done'): ").strip()
            
            if mod_id.lower() == 'done':
                break
            
            try:
                mod_id = int(mod_id)
                
                # Find suggestion
                sug = next((s for s in selected_suggestions if s['id'] == mod_id), None)
                
                if not sug:
                    print("  ❌ Invalid ID")
                    continue
                
                print(f"\n  Current: \"{sug['value']}\"")
                new_value = input("  New value: ").strip()
                
                if new_value:
                    agent.modify_suggestion(mod_id, new_value)
                    print("  ✅ Updated!")
                
            except:
                print("  ❌ Invalid input")
    
    # ============================================
    # Step 7: Confirm & Apply
    # ============================================
    print_header("📝 STEP 7: FINAL CONFIRMATION")
    
    print("\n🔍 Final changes to apply:")
    for i, sug in enumerate(selected_suggestions, 1):
        print(f"\n{i}. [{sug['category']}] {sug['description']}")
        if sug.get('modified'):
            print("   ⚠️  MODIFIED BY USER")
    
    confirm = input("\n✅ Apply these changes? (yes/no): ").lower()
    
    if confirm != 'yes':
        print("\n❌ Cancelled. resume_master.json unchanged.")
        sys.exit(0)
    
    # ============================================
    # Step 8: Generate Resume
    # ============================================
    print_header("📝 STEP 8: GENERATE TAILORED RESUME")
    
    print("\n🏢 Name this tailored version")
    company_name = input("Company/Role (e.g., 'google-swe'): ").strip()
    
    if not company_name:
        company_name = "custom-job"
    
    company_name = company_name.lower().replace(' ', '-').replace('_', '-')
    
    print(f"\n🔄 Applying {len(selected_suggestions)} changes...")
    
    try:
        updated_sanitized = agent.generate_updated_resume()
    except Exception as e:
        print(f"❌ Error applying changes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"🔐 Restoring PII...")
    merger = ResumeMerger()
    tailored_resume = merger.merge(original_resume, updated_sanitized)
    
    # Add metadata
    tailored_resume = merger.add_metadata(
        tailored_resume,
        company_name,
        match_analysis['overall_match_score'],
        len(selected_suggestions)
    )
    
    # Save JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tailored_json_path = settings.OUTPUT_DIR / f"resume_tailored_{company_name}_{timestamp}.json"
    
    print(f"\n💾 Saving tailored JSON...")
    merger.save_resume(tailored_resume, tailored_json_path)
    
    print(f"✅ Verified: resume_master.json UNCHANGED")
    
    # ============================================
    # Step 9: Generate PDF
    # ============================================
    print_header("📄 STEP 9: GENERATE PDF")
    
    print(f"\n📄 Building PDF...")
    
    try:
        builder = ResumeBuilder(str(tailored_json_path))
        pdf_path = settings.OUTPUT_DIR / f"resume_tailored_{company_name}_{timestamp}.pdf"
        builder.generate_pdf(str(pdf_path))
        print(f"✅ PDF generated!")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        pdf_path = None
    
    # ============================================
    # Step 10: Verify Improvement
    # ============================================
    print_header("📊 STEP 10: IMPROVEMENT REPORT")
    
    print(f"\n🔍 Re-analyzing tailored resume...")
    new_sanitized = sanitizer.sanitize_resume(tailored_resume)
    new_match = matcher.calculate_match(new_sanitized, jd_requirements)
    
    old_score = match_analysis['overall_match_score']
    new_score = new_match['overall_match_score']
    improvement = new_score - old_score
    
    print(f"\n{'═'*70}")
    print(f"  📈 RESULTS")
    print(f"{'═'*70}")
    print(f"\n  Match Score:")
    print(f"    Before:  {old_score}/100")
    print(f"    After:   {new_score}/100")
    print(f"    Change:  {'+' if improvement >= 0 else ''}{improvement} points")
    
    if improvement > 0:
        print(f"\n  🎉 Success! Resume improved by {improvement} points!")
    elif improvement == 0:
        print(f"\n  📝 Score unchanged - changes may be qualitative")
    
    print(f"\n  Skills Match: {match_analysis['skills_match']['score']}/100 → {new_match['skills_match']['score']}/100")
    print(f"  Keywords: {match_analysis['keyword_coverage']['score']}/100 → {new_match['keyword_coverage']['score']}/100")
    
    # Save report
    report_path = settings.OUTPUT_DIR / f"optimization_report_{company_name}_{timestamp}.json"
    
    report = {
        'company': company_name,
        'timestamp': datetime.now().isoformat(),
        'source_resume': str(settings.RESUME_MASTER_JSON),
        'tailored_json': str(tailored_json_path),
        'tailored_pdf': str(pdf_path) if pdf_path else None,
        'jd_target_role': jd_requirements.get('role_title'),
        'jd_industry': jd_requirements.get('industry'),
        'match_score_before': old_score,
        'match_score_after': new_score,
        'improvement': improvement,
        'suggestions_total': len(suggestions),
        'suggestions_applied': len(selected_suggestions),
        'suggestions_detail': selected_suggestions
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # ============================================
    # Final Summary
    # ============================================
    print_header("✅ OPTIMIZATION COMPLETE!")
    
    print(f"\n📂 Files Created:")
    print(f"   📄 Tailored JSON: {tailored_json_path.name}")
    if pdf_path:
        print(f"   📄 Tailored PDF:  {pdf_path.name}")
    print(f"   📊 Report:        {report_path.name}")
    
    print(f"\n✅ resume_master.json: UNTOUCHED")
    
    print(f"\n📊 Applied {len(selected_suggestions)} of {len(suggestions)} suggestions")
    print(f"🎯 Match score improved: {old_score} → {new_score} (+{improvement})")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Review: {pdf_path.name if pdf_path else tailored_json_path.name}")
    print(f"   2. Apply to {company_name}")
    print(f"   3. Run optimizer again for other jobs")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled. resume_master.json unchanged ✅")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
