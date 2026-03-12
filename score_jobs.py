import json
import os
import time
from telegram_utils import send_telegram_alert
from dotenv import load_dotenv
from llm_hub import UnifiedRotator

def score_jobs():
    # 0. Load environment
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    # 1. Determine Keys
    llm_keys = os.getenv("LLM_API_KEYS", "")
    
    # Fallback: Check for individual provider keys if LLM_API_KEYS is missing
    if not llm_keys:
        provider_keys = []
        for env_var in ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"]:
            val = os.getenv(env_var)
            if val:
                provider_keys.append(val)
        llm_keys = ",".join(provider_keys)

    if not llm_keys:
        print("❌ Error: No API keys found. Please set LLM_API_KEYS or provider-specific keys (e.g., GEMINI_API_KEY) in .env")
        return

    # File Paths
    prompt_file = "ai_prompt.txt"
    resume_file = "resume.json"
    input_file = "filtered_jobs.json"
    output_file = "scored_jobs.json"

    # 2. Validation & Loading
    if not all(os.path.exists(f) for f in [prompt_file, resume_file, input_file]):
        print("❌ Error: Missing required files.")
        return

    with open(prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    with open(resume_file, "r", encoding="utf-8") as f:
        resume_data = json.load(f)
        resume_text = resume_data.get("resume_text", json.dumps(resume_data))
    with open(input_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    if not jobs:
        print("⚠️ No jobs found to score.")
        return

    # 3. Initialize Unified Rotator
    rotation_limit = int(os.getenv("LLM_ROTATION_LIMIT", 8))
    dream_score_threshold = int(os.getenv("DREAM_JOB_SCORE", 90))
    
    llm = UnifiedRotator(llm_keys, limit=rotation_limit, state_file=".llm_scoring_state.json")

    print(f"\n🧠 Starting Universal AI Analysis for {len(jobs)} jobs...")
    
    scored_results = []
    for i, job in enumerate(jobs):
        title = job.get('title', 'Unknown')
        # Initialize new fields for sheet sync
        job['dream_reason'] = ""
        job['cover_letter'] = ""
        job['resume'] = ""
        job['is_dream_job'] = "No"
        
        print(f"   [{i+1}/{len(jobs)}] Analyzing: {title}...")
        
        try:
            user_input = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{job.get('descriptionText', '')}"
            raw_response = llm.generate(system_prompt, user_input)
            
            if "Error" in raw_response:
                raise Exception(raw_response)
                
            raw_text = raw_response.strip()
            if "```json" in raw_text: raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text: raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            try:
                job['ai_analysis'] = json.loads(raw_text)
                
                # Parse score
                analysis = job.get('ai_analysis', {})
                score_str = str(analysis.get('AI_Scoring_System', '0'))
                if "Score:" in score_str:
                    score_val = int(score_str.split('|')[0].replace("Score:", "").strip())
                    job['score'] = score_val
                    if score_val >= dream_score_threshold:
                        job['is_dream_job'] = "Yes"
                else:
                    job['score'] = 0

                scored_results.append(job)
                print(f"      ✅ Done!")
            except json.JSONDecodeError:
                raise Exception(f"Invalid AI output: {raw_text[:100]}")

        except Exception as e:
            print(f"      ❌ Failed: {str(e)[:100]}")
            job['ai_analysis'] = {"error": str(e)}
            scored_results.append(job)

        if len(jobs) > 5: time.sleep(1)

    # 4. Save Results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(scored_results, f, indent=2)

    print(f"\n✅ Analysis Complete! Results in: {output_file}")

if __name__ == "__main__":
    score_jobs()
