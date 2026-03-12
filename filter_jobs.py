import json
import os

def filter_jobs():
    input_file = "scraped_data.json"
    output_file = "filtered_jobs.json"

    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found. Please run the scraper first.")
        return

    # Load raw data
    with open(input_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # 1. TARGET TITLES LIST (Deduplicated from user input)
    TARGET_TITLES = [
        "Senior Marketing Manager", "Senior Manager – Marketing", "Senior Manager, Marketing",
        "Senior Manager – B2B Marketing", "Senior Marketing Lead", "Marketing Head",
        "Marketing Lead", "Growth Marketing Manager", "Growth Manager",
        "Growth & Marketing Manager", "Growth Lead", "Growth Marketing Lead",
        "Content & Growth Manager", "Performance Marketing Manager", "Performance Marketer",
        "Performance Marketing Lead", "Paid Media Manager", "Digital Performance Manager",
        "Paid Marketing Manager", "Digital Marketing Manager", "Digital Marketing Lead",
        "Digital Marketing Head", "Digital Marketing Manager (Google Ads)", "Online Marketing Manager",
        "Digital Growth Manager", "Brand Marketing Manager", "Brand Manager",
        "Brand & Communications Manager", "Marketing Communications Manager", "Creative Marketing Manager",
        "Campaign Manager (Brand)", "Marketing Manager – Growth", "Growth Manager – Marketing",
        "Marketing Growth Manager", "Demand Generation Manager", "Demand Gen Manager",
        "Demand Generation Lead", "Growth Demand Manager", "B2B Demand Generation Manager",
        "Paid Acquisition Manager", "Acquisition Marketing Manager", "Paid User Acquisition Manager",
        "Performance Acquisition Manager", "Channel Marketing Manager", "Partner Marketing Manager",
        "Product Marketing Manager", "Product Marketing Lead", "Senior Product Marketing Manager",
        "PMM (Product Marketing Manager)", "Go-To-Market Manager", "Marketing Operations Manager",
        "Marketing Ops Manager", "Marketing Operations Lead", "Revenue Operations Manager",
        "Growth Operations Manager", "User Acquisition Manager", "UA Manager",
        "Growth Acquisition Manager", "Mobile Marketing Manager", "Content Marketing Manager",
        "Content Lead", "Content Strategy Manager", "Content Marketing Lead",
        "Social Media Manager", "Social Media Lead", "Social Media & Content Manager",
        "Community Manager", "Digital Community Manager", "Marketing Analytics Manager",
        "Marketing Data Manager", "Event Marketing Manager", "Field Marketing Manager",
        "Events & Partnerships Manager", "B2B Marketing Manager", "B2B Growth Manager",
        "SaaS Marketing Manager", "Enterprise Marketing Manager"
    ]

    # 2. TARGET LOCATIONS (Example: ["Delhi", "Remote"])
    TARGET_LOCATIONS = [] 

    # 3. BLACKLIST KEYWORDS (These will be EXCLUDED, e.g., Internship, Trainee)
    BLACKLIST_KEYWORDS = ["intern", "internship", "trainee", "freshman", "student", "steward"]

    # 4. SALARY FILTER (Set your minimum expected salary, e.g., 50000 or 500000)
    # If a job says "40k - 100k" and you set 50000, it stays (because 100k > 50k).
    # If a job has NO salary mentioned, it ALSO stays.
    MIN_SALARY_THRESHOLD = 0  # Set to 0 to disable. Example: 40000

    def extract_salaries(salary_str):
        if not salary_str: return []
        import re
        # Find all numbers (handles 40k, 50,000, 1.2L etc.)
        nums = []
        # Find numbers like 40, 50.5, 1,00,000
        matches = re.findall(r'(\d+(?:[.,]\d+)?)', salary_str.replace(',', ''))
        for m in matches:
            val = float(m)
            # Basic multiplier detection
            low_str = salary_str.lower()
            if 'k' in low_str and val < 1000: val *= 1000
            elif 'l' in low_str and val < 100: val *= 100000
            elif 'cr' in low_str and val < 10: val *= 10000000
            nums.append(val)
        return nums

    filtered_jobs = []
    lower_titles = [t.lower() for t in TARGET_TITLES]
    lower_locations = [l.lower() for l in TARGET_LOCATIONS]
    lower_blacklist = [b.lower() for b in BLACKLIST_KEYWORDS]

    for job in jobs:
        title = job.get("title", "").lower()
        location = job.get("location", "").lower()
        salary_raw = job.get("salary", "") # Assuming field name is 'salary'

        # Check Title Match (Must match one of these)
        title_match = any(target in title for target in lower_titles)
        
        # Check Blacklist (Must NOT contain any of these)
        is_blacklisted = any(black in title for black in lower_blacklist)
        
        # Check Location Match
        location_match = True
        if lower_locations:
            location_match = any(loc in location for loc in lower_locations)

        # Check Salary Match (SMART LOGIC)
        salary_match = True
        if MIN_SALARY_THRESHOLD > 0 and salary_raw:
            found_salaries = extract_salaries(salary_raw)
            if found_salaries:
                # If any part of the range is >= threshold, we keep it
                salary_match = any(s >= MIN_SALARY_THRESHOLD for s in found_salaries)
            else:
                # If we couldn't parse numbers but salary exists, we keep it to be safe
                salary_match = True
        
        # Final Decision: Title matches AND Not blacklisted AND Location matches AND Salary matches
        if title_match and not is_blacklisted and location_match and salary_match:
            filtered_jobs.append(job)

    # Save filtered results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_jobs, f, indent=2)

    print(f"\n✅ Filtering Complete!")
    print(f"   - Total Jobs Analyzed: {len(jobs)}")
    print(f"   - Jobs Matching Filters: {len(filtered_jobs)}")
    print(f"   - Results saved to: {output_file}")

if __name__ == "__main__":
    filter_jobs()
