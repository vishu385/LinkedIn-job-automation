# 🚀 LinkedIn Job Automation Pipeline (Zero-Touch System)

Welcome to the ultimate **LinkedIn Job Automation Pipeline**! This project is designed to completely automate the tedious process of finding jobs, tailoring your resume, and writing cover letters. 

It is a fully automated, end-to-end Python system that:
1. **Scrapes** real-time job postings from LinkedIn.
2. **Filters** out irrelevant roles or bad locations.
3. **Reads** your personal Resume and uses **Advanced AI** (Gemini, OpenAI, or Anthropic) to compare it against the job description, scoring how good of a match you are.
4. **Auto-Generates** a highly customized, ATS-friendly PDF Resume and Cover Letter specifically tailored for the jobs that score high ("Dream Jobs").
5. **Syncs** everything (including links to the generated PDFs) directly to a **Google Sheet** so you can track your applications in real-time.

---

## 🌟 Why is this system unique? (Key Features)

- **🧠 Universal AI Hub:** Don't want to pay for OpenAI? No problem! This system supports **Google Gemini (Free tier)**, OpenAI (ChatGPT), and Anthropic (Claude). It can even rotate between multiple API keys automatically if you hit rate limits.
- **🔄 Background Monitor (Magic Mode):** The system has a background worker (`monitor_sheet.py`). If you are looking at your Google Sheet and see a job you like, just type `true` in the "Resume" column. The Python script running in the background will instantly detect it, generate your PDF Resume and Cover Letter, and put the Google Drive links back into the sheet within seconds!
- **📱 Telegram Alerts:** Get a ping on your phone the second the AI finds a job that is a perfect match for you.
- **☁️ Cloud Native:** Saves all your generated documents directly directly to your Google Drive via Google Docs API.

---

## 🛠️ Complete Step-by-Step Setup Guide

This guide assumes you are a beginner. Follow every step carefully to get this running on your PC.

### Step 1: Install Prerequisites
1. **Python 3.11.9+**: Download and install Python from [python.org](https://www.python.org/). *Critical: During installation, make sure to check the box that says "Add Python to PATH".*
2. **Git**: Download and install Git from [git-scm.com](https://git-scm.com/).

### Step 2: Download the Project
Open your Terminal (Command Prompt / PowerShell on Windows, Terminal on Mac) and run:
```bash
git clone <your-github-repo-url>
cd "Linkdin job Automation"
```

### Step 3: Install Required Python Libraries
We need to install the tools that make this script work (like Google APIs, Apify, and AI libraries).
Run this command in your terminal:
```bash
pip install -r requirements.txt
```

### Step 4: Configuration (Essential)

This project uses template files (`.example`) to help you set up yours without exposing your private data.

1. **Personal Information (`resume.json`):**
   - Copy `resume.json.example` and rename it to `resume.json`.
   - Fill it with your actual details (Experience, Skills, etc.).
   - *Note: The AI uses this to score jobs against your profile.*

2. **Google Sheet Config (`sheet_config.json`):**
   - Copy `sheet_config.json.example` and rename it to `sheet_config.json`.
   - Update the `spreadsheet_id` with your own Google Sheet ID.

3. **API Keys (`.env`):**
   - Copy `.env.example` and rename it to `.env`.
   - Add your API keys for Apify, Gemini/OpenAI, and Telegram.

4. **Google Cloud Credentials:**
   - Place your Google Service Account JSON file in the root folder as `credentials.json`.
   - (Optional) If using OAuth, place your `oauth_credentials.json` in the root folder.

*Note: These files are automatically ignored by Git to keep your data safe!*

---

### Step 5: Getting Your API Keys (Crucial Step)

If you don't have your keys yet, follow these steps to get them:

#### A. Apify API Key (For Scraping LinkedIn)
Apify acts as the engine to scrape LinkedIn without getting blocked.
- Go to [Apify.com](https://apify.com/) and create a free account.
- In the left sidebar, go to **Settings** -> **Integrations**.
- Copy your `Personal API Token`.
- Paste it in `.env` like this: `APIFY_API_TOKEN=your_copied_token_here`

#### B. AI Provider Key (For Scoring & Writing Resumes)
You only need ONE of these. Google Gemini has a generous free tier, so we recommend that.
- **Gemini:** Go to [Google AI Studio](https://aistudio.google.com/app/apikey), sign in, and click "Create API Key". 
- Paste it in `.env` like this: `GEMINI_API_KEY=your_gemini_key_here`
- *(Advanced: You can comma-separate multiple keys `key1,key2` to avoid rate limits).*

---

### Step 6: Setting up Google Sheets & Google Drive

This is the most technical step. The Python script needs to talk to your Google Account to create spreadsheets and save documents. We do this using a "Google Service Account".

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click **Select a Project** (top left) and click **New Project**. Name it "Job Automation" and click Create.
3. Left menu -> **APIs & Services** -> **Library**.
   - Search for **Google Sheets API** -> Click Enable.
   - Search for **Google Drive API** -> Click Enable.
   - Search for **Google Docs API** -> Click Enable.
4. Left menu -> **APIs & Services** -> **Credentials**.
5. Click **+ CREATE CREDENTIALS** (top screen) -> **Service Account**.
   - Name it "job-bot" and click Done.
6. Look at the "Service Accounts" list at the bottom. Click on the email address of the account you just created (it ends with `@...iam.gserviceaccount.com`).
   - -> Click the **KEYS** tab at the top.
   - -> Click **ADD KEY** -> **Create new key**.
   - -> Choose **JSON** and click Create.
7. A JSON file will download to your PC. 
8. **MOVE this file** into your `Linkdin job Automation` project folder and **RENAME it** to `credentials.json`.

**🛑 CRITICAL FINAL GOOGLE STEP:** 
Open `credentials.json` in Notepad. Find the line that says `"client_email"`. Copy that long email address. 
Go to your personal Google Drive, create a Folder called "Generated Resumes", right-click it -> **Share** -> Paste that Service Account email address and give it **Editor** access. Do the same for your Google Sheet once it's created!

---

## 🚀 How to Run the System

You are done with the setup! Now let's run the magic.
Open your terminal inside the project folder and type:

```bash
python main.py
```

The system will wake up and show you this Interactive Dashboard:
```text
==============================
   LINKEDIN JOB AUTOMATION 
==============================
1. 🚀 Run Scraper (Get Raw Jobs)
2. 🔍 Run Filter (Title & Location)
3. 🧠 Run Universal AI Scoring (Any Provider)
4. 🌟 Process Dream Jobs (Docs & Alert)
5. 📊 Sync Results to Google Sheets
6. 📈 Run All (Scrape -> Filter -> Score -> Docs -> Sync)
7. ☀️ Start Background Monitor (Auto Resume/CL)
8. 📝 Auto-Generate All Pending Docs
9. ❌ Exit
==============================
```

### 📋 What each option does:

- **1 to 5:** Runs individual parts of the system if you only want to do one specific task.
- **6. 📈 Run All (The Daily Run):** Press this every morning. It will launch the Apify scraper, pull new LinkedIn jobs, use Gemini/OpenAI to score every single one against your `resume.json`, generate PDFs for the top-scoring jobs, and push everything into a beautiful Google Sheet.
- **7. ☀️ Start Background Monitor (Interactive AI):** 
  If you choose option 7, the script will stay open and "watch" your Google Sheet. If you open your Google Sheet on your phone or laptop and manually change a cell in the "Resume" column to `true`, the background monitor will instantly notice, wake up the AI, generate a custom Resume specifically for that row, save it to your Google Drive, and replace the word `true` with the actual Google Docs link!
- **8. 📝 Auto-Generate All:** If you marked 10 jobs as `true` while the script was off, press 8, and it will generate all 10 in one go.

---

## 📂 Project Structure Explanation (For Techies)
- `main.py`: The heart of the system containing the interactive menu.
- `llm_hub.py`: A brilliant universal adapter that easily switches between Gemini, OpenAI, and Anthropic APIs.
- `save_to_sheets.py`: The robust Google Sheets sync engine that handles column mapping and data deduplication.
- `sheet_config.json`: Allows you to customize exactly which columns appear in your Google Sheet without changing Python code.
- `resume_prompt.txt` / `cover_letter_prompt.txt`: The secret sauce. These are the highly optimized system prompts that tell the AI exactly how to write top-tier ATS resumes.

---

## 🧠 Customizing the AI (Prompts & Resume)

This system is built around three core files that you should edit to match your specific profile:

1. **`resume.json`**: This is your digital brain. The AI reads this file to understand your experience, skills, and education to score jobs. **You MUST edit this file** with your real profile before running the system.
2. **`resume_prompt.txt`**: This tells the AI *how* to write your tailored resume. Open this file and update the `=== CANDIDATE PROFILE ===` section with a high-level summary of your career.
3. **`cover_letter_prompt.txt`**: This tells the AI *how* to write your cover letter. Update the `=== CANDIDATE PROFILE ===` section here as well, so the AI knows your background and preferred tone of writing.
4. **`ai_prompt.txt`**: The internal criteria the AI uses to score jobs out of 100. (You don't need to edit this unless you want to change the scoring weights).

---

## 🗄️ Understanding the System Files (JSONs & State)

As the system runs, it creates and uses several files. Here is exactly what they do:

### 🔐 Credentials & Keys
- **`credentials.json`**: Your Google Service Account key. This gives the script permission to write to your Google Sheets and Google Drive directly.
- **`oauth_credentials.json` / `token.json`**: Used for alternative Google authentication methods (OAuth 2.0). If you strictly use `credentials.json`, you generally don't need to worry about these.
- **`.env`**: Stores your secret API keys (Apify, Gemini, OpenAI, Anthropic, Telegram). **Never share this file on GitHub!**

### 📊 Data Files (The Pipeline)
- **`scraped_data.json` / `linkedin_jobs.json`**: The raw output directly from the Apify LinkedIn scraper. It contains all the messy, unfiltered job data.
- **`filtered_jobs.json`**: The clean list of jobs after `filter_jobs.py` removes bad locations, wrong titles, or promoted spam.
- **`scored_jobs.json`**: The most important data file! After the AI evaluates the jobs, the overall scores (out of 100), AI reasoning, and "Dream Job" status are saved here. **This is the exact file that gets synced to Google Sheets.**
- **`sheet_config.json`**: Controls exactly how the JSON data maps to columns in your Google Sheet. If you want to change a column name in your Google Sheet, you update the mapping in this file.

### ⚙️ System State Tracking (Smart Resume Capability)
- **`.llm_scoring_state.json`**: The script remembers which jobs it has already scored. If you stop the script halfway or run it the next day, it reads this file so it can resume scoring exactly where it left off. This prevents duplicate API calls and saves your API credits!
- **`.llm_docs_state.json`**: Similar to the scoring state, this remembers which "Dream Jobs" have already had PDF Resumes and Cover Letters generated for them to prevent duplicates.

---

Enjoy your completely automated job hunting experience! 🌟
