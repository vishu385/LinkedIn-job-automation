import json
import os
from dotenv import load_dotenv
from telegram_utils import send_telegram_alert
from generate_resume import generate_resume
from generate_cover_letter import generate_cover_letter

def process_dream_jobs():
    """
    Scans scored_jobs.json for high-scoring jobs, generates docs, and sends alerts.
    """
    # Load environment
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    scored_jobs_file = "scored_jobs.json"
    dream_score_threshold = int(os.getenv("DREAM_JOB_SCORE", 90))
    
    print("\n" + "="*50)
    print("🌟 PROCESSING DREAM JOBS (Docs & Alerts) 🌟")
    print("="*50)
    
    if not os.path.exists(scored_jobs_file):
        print(f"❌ Error: {scored_jobs_file} not found. Run scoring first (Option 3).")
        return

    with open(scored_jobs_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    if not jobs:
        print("⚠️ No jobs found in scored_jobs.json.")
        return

    print(f"📋 Total Scored Jobs to analyze: {len(jobs)}")
    print(f"🎯 Dream Job Threshold: {dream_score_threshold}")

    dream_jobs_found = 0
    docs_generated = 0
    updated_jobs = []

    # IMPORTANT: First reset ALL jobs to "No" based on current threshold
    # This ensures when threshold changes, old "Yes" values get updated
    for job in jobs:
        score_val = job.get('score', 0)
        if score_val >= dream_score_threshold:
            job['is_dream_job'] = "Yes"
        else:
            job['is_dream_job'] = "No"
    
    for job in jobs:
        # Get score from the new 'score' field or ai_analysis
        score_val = job.get('score', 0)
        
        if score_val >= dream_score_threshold:
            dream_jobs_found += 1
            title = job.get('title', 'Unknown Role')
            company = job.get('companyName', 'Unknown Company')
            
            print(f"\n✨ Dream Job Detected: {title} at {company} (Score: {score_val})")
            
            # 1. Generate Resume if not already present
            if not job.get('ai_resume'):
                print(f"   📝 Generating Resume...")
                resume_path = generate_resume(job)
                if resume_path:
                    job['ai_resume'] = resume_path
                    docs_generated += 1
            else:
                print(f"   ✅ Resume already exists: {job['ai_resume']}")
                
            # 2. Generate Cover Letter if not already present
            if not job.get('ai_cover_letter'):
                print(f"   ✉️ Generating Cover Letter...")
                cl_path = generate_cover_letter(job)
                if cl_path:
                    job['ai_cover_letter'] = cl_path
                    docs_generated += 1
            else:
                print(f"   ✅ Cover Letter already exists: {job['ai_cover_letter']}")
                
            # 3. Send Telegram Alert
            print(f"   📱 Sending Telegram alert...")
            # Preparing simplified job details for telegram_utils which expects specific keys
            alert_details = {
                "title": title,
                "companyName": company,
                "link": job.get("url", "#"),
                "ai_analysis": job.get("ai_analysis", {}),
                "ai_resume": job.get("ai_resume", ""),
                "ai_cover_letter": job.get("ai_cover_letter", "")
            }
            send_telegram_alert(alert_details)
            
            job['is_dream_job'] = "Yes"
        
        updated_jobs.append(job)

    # Save updated jobs
    with open(scored_jobs_file, "w", encoding="utf-8") as f:
        json.dump(updated_jobs, f, indent=2, ensure_ascii=False)
    
    if dream_jobs_found > 0:
        print(f"\n✅ Finished processing {dream_jobs_found} dream job(s).")
    else:
        print(f"\nℹ️ No new dream jobs found with Score >= {dream_score_threshold}.")
        print("   If you want to process lower scores, adjust DREAM_JOB_SCORE in your .env file.")

    # 4. Auto-Sync to Google Sheets
    print(f"\n✅ Dream job processing complete!")


if __name__ == "__main__":
    process_dream_jobs()
