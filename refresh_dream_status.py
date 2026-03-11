"""
Refresh Dream Job Status Based on Current Threshold
This script re-evaluates ALL jobs in scored_jobs.json based on the current 
DREAM_JOB_SCORE threshold and updates their is_dream_job status accordingly.
"""
import json
import os
from dotenv import load_dotenv

def refresh_dream_status():
    # Load environment
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    scored_jobs_file = "scored_jobs.json"
    dream_score_threshold = int(os.getenv("DREAM_JOB_SCORE", 90))
    
    print("\n" + "="*50)
    print("🔄 REFRESHING DREAM JOB STATUS")
    print("="*50)
    print(f"🎯 Current Threshold: {dream_score_threshold}")
    
    if not os.path.exists(scored_jobs_file):
        print(f"❌ Error: {scored_jobs_file} not found.")
        return
    
    with open(scored_jobs_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    if not jobs:
        print("⚠️ No jobs found.")
        return
    
    print(f"📋 Total Jobs: {len(jobs)}")
    
    # Count changes
    changed_yes_to_no = 0
    changed_no_to_yes = 0
    dream_jobs_count = 0
    
    for job in jobs:
        score = job.get('score', 0)
        old_status = job.get('is_dream_job', 'No')
        
        # Determine new status based on current threshold
        if score >= dream_score_threshold:
            new_status = "Yes"
            dream_jobs_count += 1
        else:
            new_status = "No"
        
        # Track changes
        if old_status == "Yes" and new_status == "No":
            changed_yes_to_no += 1
            title = job.get('title', 'Unknown')
            print(f"   ⬇️ Demoted: {title} (Score: {score}) - Below threshold")
        elif old_status == "No" and new_status == "Yes":
            changed_no_to_yes += 1
            title = job.get('title', 'Unknown')
            print(f"   ⬆️ Promoted: {title} (Score: {score}) - Meets threshold")
        
        job['is_dream_job'] = new_status
    
    # Save updated jobs
    with open(scored_jobs_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Refresh Complete!")
    print(f"   📊 Dream Jobs with Score >= {dream_score_threshold}: {dream_jobs_count}")
    print(f"   ⬇️ Changed Yes → No: {changed_yes_to_no}")
    print(f"   ⬆️ Changed No → Yes: {changed_no_to_yes}")
    print(f"\n💡 Now run Option 5 (Sync to Sheets) to update Google Sheet.")

if __name__ == "__main__":
    refresh_dream_status()
