#!/usr/bin/env python3
"""
Resume Builder - Generate PDF from JSON
"""

import sys
from pathlib import Path
from src.builders.resume_builder import ResumeBuilder
from datetime import datetime

def main():
    """Main entry point"""
    print("=" * 70)
    print("📄 RESUME BUILDER")
    print("=" * 70)
    print()
    
    # Paths
    json_file = "data/resume_master.json"
    
    # Use timestamped filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/resume_{timestamp}.pdf"
    
    print(f"🕐 Timestamp: {timestamp}")
    print(f"📁 Output: {output_file}")
    print()
    
    # Check if JSON exists
    if not Path(json_file).exists():
        print(f"❌ Error: {json_file} not found!")
        print("   Please create your resume JSON first.")
        return 1
    
    try:
        # Build resume
        builder = ResumeBuilder(json_file)
        pdf_path = builder.generate_pdf(output_file)
        
        print()
        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"📁 NEW Resume saved to: {pdf_path}")
        print()
        print("🔍 Look for the newest file in output/ folder:")
        print(f"   {Path(pdf_path).name}")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
