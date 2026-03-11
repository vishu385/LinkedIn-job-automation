import requests
import os
import json

def send_telegram_alert(job_details):
    """
    Sends a telegram alert for a dream job.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id or "your_token_here" in token:
        print("⚠️ Telegram credentials not configured properly in .env")
        return False

    title = job_details.get("title", "No Title")
    company = job_details.get("companyName", "Unknown Company")
    link = job_details.get("link", "#")
    
    analysis = job_details.get("ai_analysis", {})
    score_str = analysis.get("AI_Scoring_System", "Score: 0 | Decision: APPLY")
    
    # Extraction Logic
    try:
        if isinstance(score_str, dict): # Handle if it's already a dict
            score_val = score_str.get("Score", "0")
            decision = score_str.get("Decision", "APPLY")
        else:
            score_val = str(score_str).split("|")[0].replace("Score:", "").strip()
            decision = str(score_str).split("|")[1].replace("Decision:", "").strip()
    except:
        score_val = str(score_str)
        decision = "TOP MATCH"

    # Insights from AI
    reason = analysis.get("Reason_Summary", "Highly relevant to your profile!")
    top_skills = analysis.get("Top_3_Skills_Matched", [])
    skills_text = ", ".join(top_skills) if isinstance(top_skills, list) else str(top_skills)

    # Building the Premium Message
    message = (
        f"🚀 *PREMIUM JOB ALERT* 🚀\n\n"
        f"✨ *{title}*\n"
        f"🏢 *{company}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Match Score:* `{score_val}/100`\n"
        f"💎 *Decision:* `{decision}`\n"
    )

    if skills_text and skills_text != "Not Mentioned":
        message += f"✅ *Top Skills:* {skills_text}\n"

    message += (
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 *Why this matches:* \n_{reason}_\n\n"
        f"🔗 [View Official Job Listing]({link})\n"
    )
    
    # Document Links
    resume_link = job_details.get("ai_resume", "")
    cover_letter_link = job_details.get("ai_cover_letter", "")
    
    if resume_link and str(resume_link).lower() not in ["false", "none", ""]:
        message += f"\n📄 [Generated Resume]({resume_link})"
    
    if cover_letter_link and str(cover_letter_link).lower() not in ["false", "none", ""]:
        message += f"\n✍️ [Tailored Cover Letter]({cover_letter_link})"

    message += "\n\n#DreamJob #CareerGrowth #Automation"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"🚀 Premium Telegram Alert Sent: {title}")
            return True
        else:
            print(f"❌ Failed to send alert: {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Telegram API Error: {e}")
        return False
