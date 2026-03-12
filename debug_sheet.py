import json
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

def check_sheet():
    load_dotenv(override=True)
    
    with open("sheet_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    sid = config.get("spreadsheet_id")
    sname = config.get("sheet_name", "Jobs")
    
    from auth_util import get_gspread_client
    client = get_gspread_client()
    
    sheet = client.open_by_key(sid).worksheet(sname)
    all_values = sheet.get_all_values()
    
    if not all_values:
        print("Empty sheet")
        return
        
    headers = all_values[0]
    print(f"Headers found: {headers}")
    
    # Check for 'id' or 'job_id'
    id_header = "job_id"
    if id_header in headers:
        idx = headers.index(id_header)
        print(f"'{id_header}' found at index {idx}")
        first_ids = [row[idx] for row in all_values[1:6] if len(row) > idx]
        print(f"First 5 IDs in sheet: {first_ids}")
    else:
        print(f"'{id_header}' NOT FOUND in headers")
        # Try to find 'id'
        if "id" in headers:
             idx = headers.index("id")
             print(f"'id' found at index {idx}")
             first_ids = [row[idx] for row in all_values[1:6] if len(row) > idx]
             print(f"First 5 IDs in sheet (using 'id' column): {first_ids}")

    # Check for 'true' values
    resu_header = "Resu_"
    if resu_header in headers:
        idx = headers.index(resu_header)
        rows_with_true = [i+2 for i, row in enumerate(all_values[1:]) if len(row) > idx and str(row[idx]).lower() == 'true']
        print(f"Rows with 'true' in {resu_header}: {rows_with_true}")

if __name__ == "__main__":
    check_sheet()
