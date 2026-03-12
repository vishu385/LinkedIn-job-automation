import os
import sys
import importlib
from config_helper import ConfigHelper

# Ensure current directory is in sys.path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
# print(f"DEBUG: sys.path includes {current_dir}")

def print_menu():

    print("\n" + "="*30)
    print("   LINKEDIN JOB AUTOMATION ")
    print("="*30)
    print("1. 🚀 Run Scraper (Get Raw Jobs)")
    print("2. 🔍 Run Filter (Title & Location)")
    print("3. 🧠 Run Universal AI Scoring (Any Provider)")
    print("4. 🌟 Process Dream Jobs (Docs & Alert)")
    print("5. 📊 Sync Results to Google Sheets")
    print("6. 📈 Run All (Scrape -> Filter -> Score -> Docs -> Sync)")
    print("7. ☀️ Start Background Monitor (Auto Resume/CL)")
    print("8. 📝 Auto-Generate All Pending Docs")
    print("9. ❌ Exit")
    print("="*30)

def run_python_script(script_name):
    """Helper function to import, reload, and run a Python script."""
    module_name = script_name.replace(".py", "")
    try:
        module = __import__(module_name)
        importlib.reload(module)
        # Assuming each script has a main function or a specific function to call
        if hasattr(module, 'start_job'): # For run_apify_actor
            module.start_job()
        elif hasattr(module, 'filter_jobs'): # For filter_jobs
            module.filter_jobs()
        elif hasattr(module, 'score_jobs'): # For score_jobs
            module.score_jobs()
        elif hasattr(module, 'save_to_sheets'): # For save_to_sheets
            module.save_to_sheets()
        elif hasattr(module, 'process_dream_jobs'): # For process_dream_jobs
            module.process_dream_jobs()
        elif hasattr(module, 'monitor_sheet'): # For monitor_sheet
            module.monitor_sheet()
        else:
            print(f"⚠️ No specific entry point found for {script_name}. Module loaded.")
    except ImportError as e:
        print(f"❌ Error: Could not import {script_name}: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")

def generate_all_pending():
    """Auto-scan sheet and generate all pending Resume/Cover Letters where 'true' is written"""
    import json
    import gspread
    from dotenv import load_dotenv
    from generate_resume import generate_resume
    from generate_cover_letter import generate_cover_letter
    
    try:
        # Load environment
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        load_dotenv(dotenv_path=env_path, override=True)
        
        scored_jobs_file = "scored_jobs.json"
        config_file = "sheet_config.json"
        
        print("\n" + "="*50)
        print("📝 AUTO-SCAN & GENERATE - ONE TIME")
        print("="*50)
        print("🔍 Scanning sheet for 'true' values...")
        
        # Load config
        with open(config_file, "r", encoding="utf-8") as f:
            sheet_config = json.load(f)
        
        spreadsheet_id = sheet_config.get("spreadsheet_id")
        sheet_name = sheet_config.get("sheet_name", "Jobs")
        
        # Connect to Google Sheets via unified auth_util
        from auth_util import get_gspread_client
        client = get_gspread_client()
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get all values
        all_values = worksheet.get_all_values()
        if not all_values:
            print("⚠️ Sheet is empty!")
            return
        
        # Get headers
        headers = all_values[0]
        
        # DYNAMIC: Find Resume/Cover_Letter columns from sheet_config mapping
        # This works regardless of what header names user sets
        column_mapping = sheet_config.get("column_mapping", {})
        
        # Use ConfigHelper for dynamic lookups
        config = ConfigHelper()
        
        # NOTIFICATION: Alert if headers don't match config
        config.notify_header_changes(headers)
        
        # Find which header maps to ai_resume and ai_cover_letter
        resume_header = config.get_header_for_field("ai_resume")
        cover_letter_header = config.get_header_for_field("ai_cover_letter")
        id_header = config.get_header_for_field("id")
        
        resume_col_idx = headers.index(resume_header) if resume_header and resume_header in headers else -1
        cover_letter_col_idx = headers.index(cover_letter_header) if cover_letter_header and cover_letter_header in headers else -1
        id_col_idx = headers.index(id_header) if id_header and id_header in headers else -1
        
        if resume_col_idx == -1 and cover_letter_col_idx == -1:
            print(f"⚠️ Resume/Cover_Letter columns not found! (Looking for: {resume_header}, {cover_letter_header})")
            return
        
        # Load scored_jobs.json
        with open(scored_jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        
        jobs_by_id = {str(job.get("id", "")): job for job in jobs}
        
        # Count pending items
        pending_resumes = 0
        pending_cls = 0
        for row in all_values[1:]:
            if resume_col_idx != -1 and len(row) > resume_col_idx:
                if str(row[resume_col_idx]).strip().lower() == "true":
                    pending_resumes += 1
            if cover_letter_col_idx != -1 and len(row) > cover_letter_col_idx:
                if str(row[cover_letter_col_idx]).strip().lower() == "true":
                    pending_cls += 1
        
        print(f"\n📊 Found: {pending_resumes} Resumes + {pending_cls} Cover Letters pending")
        
        if pending_resumes == 0 and pending_cls == 0:
            print("✅ No pending documents to generate!")
            return
        
        print("\n🚀 Starting generation...\n")
        
        docs_generated = 0
        
        # Process each row
        for row_idx, row in enumerate(all_values[1:], start=2):
            if len(row) <= max(resume_col_idx, cover_letter_col_idx):
                continue
            
            job_id = row[id_col_idx] if id_col_idx != -1 and len(row) > id_col_idx else None
            
            # Get job data (try local JSON first, then fallback to sheet row)
            job_data = None
            if job_id and job_id in jobs_by_id:
                job_data = jobs_by_id[job_id]
            else:
                # RECONSTRUCT from sheet row if missing locally
                job_data = {
                    "id": job_id or f"SheetRow_{row_idx}",
                    "title": row[headers.index(config.get_header_for_field("title"))] if config.get_header_for_field("title") in headers else "Unknown",
                    "companyName": row[headers.index(config.get_header_for_field("companyName"))] if config.get_header_for_field("companyName") in headers else "Unknown",
                    "location": row[headers.index(config.get_header_for_field("location"))] if config.get_header_for_field("location") in headers else "N/A",
                    "descriptionText": row[headers.index(config.get_header_for_field("descriptionText"))] if config.get_header_for_field("descriptionText") in headers else "N/A",
                    "ai_analysis": {
                        "Reason_Summary": row[headers.index(config.get_header_for_field("Reason_Summary"))] if config.get_header_for_field("Reason_Summary") in headers else "Manual request from sheet"
                    },
                    "url": row[headers.index(config.get_header_for_field("link"))] if config.get_header_for_field("link") in headers else "N/A"
                }

            job_title = job_data.get('title', 'Unknown')
            company = job_data.get('companyName', 'Unknown')
            
            # Check Resume
            if resume_col_idx != -1 and len(row) > resume_col_idx:
                if str(row[resume_col_idx]).strip().lower() == "true":
                    print(f"📝 RESUME: {job_title} at {company}")
                    
                    resume_path = generate_resume(job_data)
                    
                    if resume_path:
                        cell_ref = gspread.utils.rowcol_to_a1(row_idx, resume_col_idx + 1)
                        worksheet.update([[resume_path]], cell_ref)
                        print(f"   ✅ Updated {cell_ref}")
                        job_data["ai_resume"] = resume_path
                        docs_generated += 1
            
            # Check Cover Letter
            if cover_letter_col_idx != -1 and len(row) > cover_letter_col_idx:
                if str(row[cover_letter_col_idx]).strip().lower() == "true":
                    print(f"✉️ COVER LETTER: {job_title} at {company}")
                    
                    cl_path = generate_cover_letter(job_data)
                    
                    if cl_path:
                        cell_ref = gspread.utils.rowcol_to_a1(row_idx, cover_letter_col_idx + 1)
                        worksheet.update([[cl_path]], cell_ref)
                        print(f"   ✅ Updated {cell_ref}")
                        job_data["ai_cover_letter"] = cl_path
                        docs_generated += 1
        
        # Save updated jobs
        if docs_generated > 0:
            with open(scored_jobs_file, "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Done! Generated {docs_generated} document(s)")
        print(f"📁 Files saved in: generated_docs/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    while True:
        print_menu()
        choice = input("Enter your choice (1-9): ").strip()

        if choice == '1':
            print("\nStarting Scraper...")
            run_python_script("run_apify_actor.py")
            
        elif choice == '2':
            print("\nStarting Filter...")
            run_python_script("filter_jobs.py")
            
        elif choice == '3':
            print("\nStarting AI Scoring...")
            run_python_script("score_jobs.py")

        elif choice == '4':
            print("\nProcessing Dream Jobs...")
            run_python_script("process_dream_jobs.py")

        elif choice == '5':
            print("\nSyncing to Google Sheets...")
            run_python_script("save_to_sheets.py")
            
        elif choice == '6':
            print("\nStep 1: Scraping Jobs...")
            run_python_script("run_apify_actor.py")
            
            print("\nStep 2: Filtering Jobs...")
            run_python_script("filter_jobs.py")

            print("\nStep 3: AI Scoring...")
            run_python_script("score_jobs.py")

            print("\nStep 4: Processing Dream Jobs...")
            run_python_script("process_dream_jobs.py")

            print("\nStep 5: Syncing to Google Sheets...")
            run_python_script("save_to_sheets.py")
            
            print("\n✅ Full Pipeline Complete!")
        
        elif choice == '7':
            print("\n🌟 Starting Background Monitor...")
            print("This will watch Google Sheets for 'true' values in Resume/Cover_Letter columns")
            print("Press Ctrl+C to stop the monitor\n")
            run_python_script("monitor_sheet.py")
            
        elif choice == '8':
            generate_all_pending()
            
        elif choice == '9':
            print("Goodbye! 👋")
            break
        else:
            print("⚠️ Invalid choice. Please enter 1-9.")

if __name__ == "__main__":
    main()
