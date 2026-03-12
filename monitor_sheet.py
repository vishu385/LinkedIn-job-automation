import json
import os
import time
import gspread
from config_helper import ConfigHelper
from dotenv import load_dotenv
from generate_resume import generate_resume
from generate_cover_letter import generate_cover_letter

def monitor_sheet():
    """
    Background service that monitors Google Sheet for manual generation requests.
    Checks Resume and Cover_Letter columns for "true" values.
    Generates documents and replaces 'true' with the local file path.
    """
    # Load environment
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    config_file = "sheet_config.json"
    config_file = "sheet_config.json"
    scored_jobs_file = "scored_jobs.json"
    
    # Check interval in seconds/minutes (parse string like "120sec", "2min", or just "30")
    raw_interval = os.getenv("MONITOR_CHECK_INTERVAL", "30").lower().strip()
    
    # Simple parser for "sec", "s", "min", "m"
    check_interval = 30 # Default
    try:
        if "min" in raw_interval or raw_interval.endswith("m"):
            val = float("".join(c for c in raw_interval if c.isdigit() or c == "."))
            check_interval = int(val * 60)
        elif "sec" in raw_interval or raw_interval.endswith("s"):
            val = float("".join(c for c in raw_interval if c.isdigit() or c == "."))
            check_interval = int(val)
        else:
            check_interval = int(raw_interval)
    except:
        print(f"⚠️ Warning: Could not parse MONITOR_CHECK_INTERVAL '{raw_interval}'. Using default 30s.")
        check_interval = 30
    
    print("\n" + "="*60)
    print("🔍 BACKGROUND SHEET MONITOR - FULLY AUTOMATIC")
    print("="*60)
    print(f"⏰ Check interval: {check_interval} seconds")
    print("📝 When you write 'true' in Resume/Cover_Letter columns:")
    print("   → Document will be AUTO-GENERATED (no questions asked)")
    print("   → Link will replace 'true' in sheet")
    print("🛑 Press Ctrl+C to stop\n")
    
    try:
        while True:
            try:
                # Load config
                with open(config_file, "r", encoding="utf-8") as f:
                    sheet_config = json.load(f)
                
                spreadsheet_id = sheet_config.get("spreadsheet_id")
                sheet_name = sheet_config.get("sheet_name", "Jobs")
                
                # Connect to Google Sheets via unified auth_util
                from auth_util import get_gspread_client
                client = get_gspread_client()
                
                # Open Spreadsheet (By ID or Name)
                if spreadsheet_id and spreadsheet_id.strip():
                    spreadsheet = client.open_by_key(spreadsheet_id)
                else:
                    spreadsheet_name = sheet_config.get("spreadsheet_name", "LinkedIn Jobs")
                    spreadsheet = client.open(spreadsheet_name)
                    
                worksheet = spreadsheet.worksheet(sheet_name)
                
                # Get all values
                all_values = worksheet.get_all_values()
                if not all_values:
                    print("⚠️ Sheet is empty, waiting...")
                    time.sleep(check_interval)
                    continue
                
                # Get headers
                headers = all_values[0]
                
                # Use ConfigHelper for dynamic column discovery
                config = ConfigHelper()
                
                # NOTIFICATION: Alert if headers don't match config
                config.notify_header_changes(headers)
                
                resume_header = config.get_header_for_field("ai_resume")
                cl_header = config.get_header_for_field("ai_cover_letter")
                id_header = config.get_header_for_field("id")

                # Find column indices
                resume_col_idx = headers.index(resume_header) if resume_header and resume_header in headers else -1
                cover_letter_col_idx = headers.index(cl_header) if cl_header and cl_header in headers else -1
                id_col_idx = headers.index(id_header) if id_header and id_header in headers else -1
                
                if resume_col_idx == -1 and cover_letter_col_idx == -1:
                    print(f"⚠️ Columns '{resume_header}' or '{cl_header}' not found in sheet")
                    time.sleep(check_interval)
                    continue
                
                # Load scored_jobs.json
                with open(scored_jobs_file, "r", encoding="utf-8") as f:
                    jobs = json.load(f)
                
                # Create job lookup by ID
                jobs_by_id = {str(job.get("id", "")): job for job in jobs}
                
                # Track documents generated this cycle
                docs_generated = 0
                
                # Check each row for "true" values
                for row_idx, row in enumerate(all_values[1:], start=2):  # Start from row 2 (skip header)
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
                    
                    # Check Resume column
                    if resume_col_idx != -1 and len(row) > resume_col_idx:
                        cell_value = str(row[resume_col_idx]).strip().lower()
                        if cell_value == "true":
                            print(f"\n🎯 AUTO-GENERATING RESUME")
                            print(f"   📋 Job: {job_title} at {company}")
                            
                            # Generate resume (NO QUESTIONS ASKED!)
                            resume_path = generate_resume(job_data)
                            
                            if resume_path:
                                # Update sheet with file path or URL
                                cell_ref = gspread.utils.rowcol_to_a1(row_idx, resume_col_idx + 1)
                                worksheet.update([[resume_path]], cell_ref)
                                print(f"   ✅ Updated cell {cell_ref} with link: {resume_path}")
                                
                                # Update job data
                                job_data["ai_resume"] = resume_path
                                docs_generated += 1
                    
                    # Check Cover_Letter column
                    if cover_letter_col_idx != -1 and len(row) > cover_letter_col_idx:
                        cell_value = str(row[cover_letter_col_idx]).strip().lower()
                        if cell_value == "true":
                            print(f"\n🎯 AUTO-GENERATING COVER LETTER")
                            print(f"   📋 Job: {job_title} at {company}")
                            
                            # Generate cover letter (NO QUESTIONS ASKED!)
                            cl_path = generate_cover_letter(job_data)
                            
                            if cl_path:
                                # Update sheet with file path or URL
                                cell_ref = gspread.utils.rowcol_to_a1(row_idx, cover_letter_col_idx + 1)
                                worksheet.update([[cl_path]], cell_ref)
                                print(f"   ✅ Updated cell {cell_ref} with link: {cl_path}")
                                
                                # Update job data
                                job_data["ai_cover_letter"] = cl_path
                                docs_generated += 1
                
                # Save updated jobs back to file
                if docs_generated > 0:
                    with open(scored_jobs_file, "w", encoding="utf-8") as f:
                        json.dump(jobs, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Saved {docs_generated} document(s) info to scored_jobs.json")
                
                # Status update
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                if docs_generated > 0:
                    print(f"\n✅ Cycle complete - Generated {docs_generated} document(s) - {timestamp}")
                else:
                    print(f"✅ Check complete - No new requests - {timestamp}")
                print(f"⏳ Next check in {check_interval} seconds...")
                
            except Exception as e:
                print(f"\n❌ Error during monitoring: {e}")
                import traceback
                traceback.print_exc()
                print(f"\n⏳ Retrying in {check_interval} seconds...")
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped by user")
        print("✅ Shutting down gracefully...")

if __name__ == "__main__":
    monitor_sheet()
