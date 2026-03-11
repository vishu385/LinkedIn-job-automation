from apify_client import ApifyClient
import os
from dotenv import load_dotenv
import json

# Load API token from .env
load_dotenv()

def start_job():
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("❌ Error: APIFY_API_TOKEN not found in .env file.")
        return

    client = ApifyClient(api_token)

    print("\n--- Apify Run Configuration ---")
    
    # 1. Get Actor ID
    actor_id = os.getenv("APIFY_ACTOR_ID")
    if actor_id:
        print(f"✅ Loaded Actor ID from .env: {actor_id}")
    else:
        actor_id = input("Enter Actor ID: ").strip()
        while not actor_id:
            print("⚠️ Actor ID is required!")
            actor_id = input("Enter Actor ID: ").strip()

    # 2. Get Search URL
    search_url = os.getenv("APIFY_SEARCH_URL")
    if search_url:
        print(f"✅ Loaded Search URL from .env: {search_url}")
    else:
        search_url = input("Enter LinkedIn Search URL: ").strip()
        while not search_url:
            print("⚠️ Search URL is required!")
            search_url = input("Enter LinkedIn Search URL: ").strip()

    # 3. Get Number of jobs
    env_jobs_count = os.getenv("APIFY_MAX_JOBS")
    if env_jobs_count and env_jobs_count.isdigit():
        jobs_count = int(env_jobs_count)
        print(f"✅ Loaded Jobs Count from .env: {jobs_count}")
    else:
        jobs_input = input("Enter Number of jobs to scrape (e.g., 20, 100): ").strip()
        while not jobs_input or not jobs_input.isdigit():
            print("⚠️ Please enter a valid number for jobs count!")
            jobs_input = input("Enter Number of jobs to scrape: ").strip()
        jobs_count = int(jobs_input)

    # Input Structure
    run_input = {
        "count": jobs_count,
        "scrapeCompany": True,
        "splitByLocation": False,
        "urls": [search_url]
    }

    print(f"\n🚀 Running Actor: {actor_id}")
    print(f"🔗 Using URL: {search_url}")
    print(f"🔢 Jobs Count: {jobs_count}")

    # Run logic
    try:
        # Run and wait
        run = client.actor(actor_id).call(run_input=run_input)

        if run['status'] == 'SUCCEEDED':
            print("✅ Success! Fetching results...")
            raw_items = client.dataset(run["defaultDatasetId"]).list_items().items
            
            print(f"\n📊 Scraping Summary:")
            print(f"   - Total jobs found and saved: {len(raw_items)}")
            print(f"✅ SUCCESSFULLY SAVED {len(raw_items)} JOBS TO DATA FILE.")

            output_file = "scraped_data.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(raw_items, f, indent=2)
            
            print(f"📁 Results saved to '{output_file}'.")
        else:
            print(f"⚠️ Actor finished with status: {run['status']}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    start_job()
