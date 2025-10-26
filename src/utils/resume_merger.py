"""
Resume Merger - Merges sanitized changes back with PII
"""
import json
import copy
from typing import Dict, Any
from pathlib import Path

class ResumeMerger:
    """Merge sanitized resume changes back with original PII"""
    
    @staticmethod
    def merge(
        original_resume: Dict[str, Any],
        sanitized_updated: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge updated sanitized resume with original PII
        
        Args:
            original_resume: Original resume with PII (from resume_master.json)
            sanitized_updated: Updated resume (sanitized, no PII)
        
        Returns:
            Updated resume with PII restored
        """
        
        # Start with updated resume structure
        merged = copy.deepcopy(sanitized_updated)
        
        # Restore personal information
        if 'personal_info' in original_resume:
            merged['personal_info'] = copy.deepcopy(original_resume['personal_info'])
        
        # Restore company names in experience
        if 'experience' in original_resume and 'experience' in merged:
            for i in range(min(len(original_resume['experience']), len(merged['experience']))):
                orig_exp = original_resume['experience'][i]
                updated_exp = merged['experience'][i]
                
                # Restore company name
                updated_exp['company'] = orig_exp['company']
                
                # Restore location if exists
                if 'location' in orig_exp:
                    updated_exp['location'] = orig_exp['location']
        
        # Restore education institution names
        if 'education' in original_resume and 'education' in merged:
            for i in range(min(len(original_resume['education']), len(merged['education']))):
                orig_edu = original_resume['education'][i]
                updated_edu = merged['education'][i]
                
                # Restore institution name
                updated_edu['institution'] = orig_edu['institution']
        
        # Remove metadata if it exists (from sanitized version)
        if '_metadata' in merged and '_metadata' not in original_resume:
            del merged['_metadata']
        
        return merged
    
    @staticmethod
    def add_metadata(
        resume: Dict[str, Any],
        company_name: str,
        match_score_before: int,
        changes_count: int
    ) -> Dict[str, Any]:
        """Add metadata to track tailoring"""
        from datetime import datetime
        
        resume_with_meta = copy.deepcopy(resume)
        resume_with_meta['_metadata'] = {
            'source': 'resume_master.json',
            'tailored_for': company_name,
            'created_at': datetime.now().isoformat(),
            'match_score_before': match_score_before,
            'changes_applied': changes_count
        }
        
        return resume_with_meta
    
    @staticmethod
    def save_resume(resume: Dict[str, Any], filepath: Path):
        """Save resume to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(resume, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved: {filepath}")
