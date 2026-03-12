import json
import os
import gspread
from dotenv import load_dotenv
from config_helper import ConfigHelper

def save_to_sheets():
    # 0. Load environment
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    # File Paths
    input_file = "scored_jobs.json"
    config_file = "sheet_config.json"

    # 1. Validation
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found. Run scoring first!")
        return

    if not os.path.exists(config_file):
        print(f"❌ Error: {config_file} not found.")
        return

    # 2. Load Data & Config
    with open(input_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    with open(config_file, "r", encoding="utf-8") as f:
        sheet_config = json.load(f)

    # 2.5 AUTO-REFRESH: Re-evaluate is_dream_job based on current threshold
    dream_score_threshold = int(os.getenv("DREAM_JOB_SCORE", 90))
    print(f"🎯 Auto-refreshing Dream Job status (Threshold: {dream_score_threshold})...")
    
    changes_made = 0
    for job in jobs:
        score = job.get('score', 0)
        old_status = job.get('is_dream_job', 'No')
        new_status = "Yes" if score >= dream_score_threshold else "No"
        
        if old_status != new_status:
            changes_made += 1
            job['is_dream_job'] = new_status
    
    if changes_made > 0:
        # Save changes back to scored_jobs.json
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Updated {changes_made} jobs' dream status")
    else:
        print(f"   ✅ All dream statuses are correct")

    spreadsheet_id = sheet_config.get("spreadsheet_id")
    spreadsheet_name = sheet_config.get("spreadsheet_name", "LinkedIn Jobs")
    sheet_name = sheet_config.get("sheet_name", "Sheet1")
    mapping = sheet_config.get("column_mapping", {})

    if not mapping:
        print("❌ Error: No column mapping found in sheet_config.json")
        return

    print(f"📊 Syncing {len(jobs)} jobs to Google Sheets...")


    # 3. Authenticate & Connect
    try:
        from auth_util import get_gspread_client
        client = get_gspread_client()
        
        # Open Spreadsheet (By ID or Name)
        if spreadsheet_id and spreadsheet_id.strip():
            print(f"🔗 Opening Spreadsheet by ID: {spreadsheet_id}")
            spreadsheet = client.open_by_key(spreadsheet_id)
        else:
            try:
                print(f"🔍 Searching for Spreadsheet by name: {spreadsheet_name}")
                spreadsheet = client.open(spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                print(f"📝 Creating new Spreadsheet: {spreadsheet_name}")
                spreadsheet = client.create(spreadsheet_name)
                print(f"✅ Success! Spreadsheet ID: {spreadsheet.id}")

        # Open WorkSheet
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")

        # 4. Prepare Headers & Data
        headers = list(mapping.keys())
        
        # Get existing values
        current_values = worksheet.get_all_values()
        
        # Get existing headers from Row 1
        current_headers = []
        if current_values and current_values[0]:
            # Take all non-empty values from the first row to detect columns that need deletion
            current_headers = [str(val).strip() for val in current_values[0] if str(val).strip() != ""]


        # Compare headers (case-aware check)
        # We need to find columns present in sheet but NOT in config
        header_keys_lower = [h.lower() for h in headers]
        indices_to_delete = []
        
        if current_headers:
            for i, ch in enumerate(current_headers):
                if ch.lower() not in header_keys_lower and ch.strip() != "":
                    # Column index is 1-based
                    indices_to_delete.append(i + 1)
        
        if indices_to_delete or headers != current_headers:
            print(f"🔄 [SYNC] Headers mismatch detected.")
            
            # 1. Delete removed columns (in reverse order to maintain indices)
            if indices_to_delete:
                for col_idx in sorted(indices_to_delete, reverse=True):
                    header_name = current_headers[col_idx-1]
                    print(f"🧹 Removing obsolete column '{header_name}' (Index: {col_idx})...")
                    worksheet.delete_columns(col_idx)
            
            # 2. Update Row 1 with new headers
            print("📝 Updating headers structure...")
            worksheet.update(values=[headers], range_name='1:1')
            
            # 3. Handle trailing columns if sheet is wider than config
            # Refresh headers after deletion
            refreshed_values = worksheet.get_all_values()
            refreshed_headers = refreshed_values[0] if refreshed_values else []
            if len(refreshed_headers) > len(headers):
                print(f"🧹 Cleaning {len(refreshed_headers) - len(headers)} trailing columns...")
                worksheet.delete_columns(len(headers) + 1, len(refreshed_headers))

            # Refresh values for deduplication logic
            current_values = worksheet.get_all_values()
            print(f"✅ Sheet structure synchronized with config.")
        else:
            print("✅ Headers are up to date.")



        # 5. Map Data & Update/Append Logic
        rows_to_append = []
        rows_to_update = [] # List of (row_idx, row_data)
        
        # Map existing IDs to ALL their row indices (1-based)
        id_to_rows = {} # job_id -> list of {"row_idx": int, "current_data": list}
        
        # DYNAMIC: Get 'id' header name from config (not hardcoded!)
        config = ConfigHelper()
        id_header = config.get_header_for_field("id")
        
        id_col_index = -1
        if id_header and id_header in headers:
            id_col_index = headers.index(id_header)
        
        # NOTIFICATION: Alert user if headers don't match config
        config.notify_header_changes(headers)
        
        if current_values and id_col_index != -1:
            for i, r in enumerate(current_values):
                row_idx = i + 1
                if len(r) > id_col_index:
                    job_id = str(r[id_col_index]).strip()
                    # Skip if it's the header row itself
                    if job_id and job_id != id_header:
                        if job_id not in id_to_rows:
                            id_to_rows[job_id] = []
                        id_to_rows[job_id].append({"row_idx": row_idx, "current_data": r})
        
        print(f"📊 Analyzing {len(jobs)} jobs for updates or additions...")
        
        # Import generation modules (only if needed)
        try:
            from generate_resume import generate_resume
            from generate_cover_letter import generate_cover_letter
            generation_available = True
        except ImportError:
            generation_available = False
            print("⚠️ Resume/Cover letter generation modules not available")
        
        for job in jobs:
            job_id = str(job.get("id", "")).strip()
            is_dream_job = job.get("is_dream_job", False)
            
            # Map current job data to a row based on headers
            new_row = []
            for header in headers:
                field_path = mapping[header]
                
                # DYNAMIC: Check by field_path (mapping value), not header name
                # This way user can rename headers in sheet_config.json
                if field_path == "ai_resume":
                    value = job.get("ai_resume")
                    if not value or str(value).lower() in ["false", "none", ""]:
                        value = "false"
                elif field_path == "ai_cover_letter":
                    value = job.get("ai_cover_letter")
                    if not value or str(value).lower() in ["false", "none", ""]:
                        value = "false"
                else:
                    # Normal field mapping
                    value = job
                    for part in field_path.split('.'):
                        if isinstance(value, dict):
                            value = value.get(part)
                        else:
                            value = None
                            break
                
                if isinstance(value, (list, dict)):
                    if not value or (isinstance(value, list) and all(str(v).strip() == "" for v in value)):
                        value = "Not Mentioned"
                    else:
                        if isinstance(value, list):
                            value = " | ".join([str(v) for v in value if str(v).strip() != ""])
                        else:
                            value = json.dumps(value, ensure_ascii=False)
                
                if value is None or str(value).strip() == "" or str(value).lower() == "none":
                    value = "Not Mentioned"
                
                new_row.append(str(value).strip())

            # Decision: Update or Append?
            if job_id in id_to_rows:
                # Update ALL rows matching this ID
                for info in id_to_rows[job_id]:
                    current_row_data = info["current_data"]
                    
                    # PRESERVE MANUAL ENTRIES: For ai_resume and ai_cover_letter,
                    # if JSON has "false" but sheet has real value, keep sheet value
                    final_row = []
                    for i, header in enumerate(headers):
                        field_path = mapping[header]
                        new_val = new_row[i] if i < len(new_row) else ""
                        old_val = str(current_row_data[i]).strip() if i < len(current_row_data) else ""
                        
                        # Check if this is ai_resume or ai_cover_letter
                        if field_path in ["ai_resume", "ai_cover_letter"]:
                            # If new value is "false" but old value is not "false" and not empty
                            if new_val.lower() == "false" and old_val.lower() not in ["false", "", "not mentioned"]:
                                final_row.append(old_val)  # Keep manual entry
                            else:
                                final_row.append(new_val)
                        else:
                            final_row.append(new_val)
                    
                    truncated_current = [str(v).strip() for v in current_row_data[:len(final_row)]]
                    if truncated_current != final_row:
                        rows_to_update.append((info["row_idx"], final_row))
            else:
                rows_to_append.append(new_row)
        
        # Save updated job data back to scored_jobs.json if any dream jobs were processed
        if generation_available:
            with open(input_file, "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)

        # 6. Perform Updates
        if rows_to_update:
            print(f"🔄 Updating {len(rows_to_update)} rows with latest data (including duplicates)...")
            # Sort by row_idx to be clean, though not strictly necessary for batch updates
            # For efficiency we could batch these, but gspread.update is okay for small counts
            for row_idx, row_data in sorted(rows_to_update, key=lambda x: x[0]):
                worksheet.update(values=[row_data], range_name=f"{row_idx}:{row_idx}")
            print(f"✅ Updates complete.")

        # 7. Append New Data
        if rows_to_append:
            worksheet.append_rows(rows_to_append)
            print(f"✅ Successfully added {len(rows_to_append)} new jobs.")
        
        if not rows_to_update and not rows_to_append:
            print("✨ Everything is already up to date! No changes needed.")
        else:
            print("✨ No new jobs to add. Everything is up to date!")

    except Exception as e:
        print(f"❌ Google Sheets Error: {e}")

if __name__ == "__main__":
    save_to_sheets()
