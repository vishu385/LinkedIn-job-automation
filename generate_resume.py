"""
Generate tailored Resume using Gemini AI with API rotation.
Saves as Google Doc using OAuth or local Markdown file.
"""
import json
import os
from dotenv import load_dotenv
from resume_cl_rotator import get_rotator

def generate_resume(job_data):
    """
    Generate a tailored resume for a specific job.
    
    Args:
        job_data (dict): Job information from scored_jobs.json
        
    Returns:
        str: File path or Google Docs link, or None if failed
    """
    try:
        # Load environment
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        load_dotenv(dotenv_path=env_path, override=True)
        
        company = job_data.get('companyName', 'Company')
        title = job_data.get('title', 'Position')
        
        print(f"\n📝 Generating Resume for: {title} at {company}")
        
        # Load resume template
        with open("resume.json", "r", encoding="utf-8") as f:
            base_resume = json.load(f)
        
        # Load prompt template
        prompt_file = "resume_prompt.txt"
        if not os.path.exists(prompt_file):
            print(f"❌ Error: {prompt_file} not found")
            return None
            
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Format prompt with job data
        ai_analysis_data = job_data.get('ai_analysis', {})
        reason_summary = ai_analysis_data.get('Reason_Summary', 'N/A')
        
        # Get personal info for placeholders
        personal = base_resume.get('personal_info', {})
        
        prompt = prompt_template.format(
            title=title,
            company=company,
            location=job_data.get('location', 'N/A'),
            description=job_data.get('descriptionText', 'N/A')[:2000],
            skills_from_step_1=reason_summary,
            ai_analysis=reason_summary,
            base_resume=json.dumps(base_resume, indent=2),
            name=personal.get('name', 'CANDIDATE NAME'),
            phone=personal.get('phone', 'PHONE NUMBER'),
            email=personal.get('email', 'EMAIL ADDRESS'),
            user_location=personal.get('location', 'LOCATION')
        )
        
        # Generate using AI with rotation (Gemini/DeepSeek)
        rotator = get_rotator()
        resume_content = rotator.generate(prompt)
        
        print(f"✅ Resume content generated!")
        
        # Save as Markdown file (Google Docs has issues, this works 100%)
        docs_folder = "generated_docs"
        os.makedirs(docs_folder, exist_ok=True)
        
        # Clean filename
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        
        filename = f"Resume_{safe_company}_{safe_title}.md"
        filepath = os.path.join(docs_folder, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Resume - {title} at {company}\n\n")
            f.write(f"**Generated for:** {job_data.get('url', 'N/A')}\n\n")
            f.write("---\n\n")
            f.write(resume_content)
        
        print(f"💾 Saved local backup to: {filepath}")
        
        # --- NEW: Upload to Google Docs ---
        try:
            from google_docs_service import create_doc_from_markdown
            doc_title = f"Resume - {title} at {company}"
            gdoc_url = create_doc_from_markdown(doc_title, resume_content)
            if gdoc_url:
                print(f"🌐 Google Doc available at: {gdoc_url}")
                return gdoc_url
        except Exception as ge:
            print(f"⚠️ Google Docs upload failed, using local path: {ge}")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Error generating resume: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test with a sample job
    with open("scored_jobs.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)
        if jobs:
            link = generate_resume(jobs[0])
            print(f"\n🎉 Resume: {link}")
