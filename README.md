# 🚀 LinkedIn Job Automation Pipeline (Zero-Touch System)

Welcome to the ultimate **LinkedIn Job Automation Pipeline**! This project is designed to completely automate the tedious process of finding jobs, tailoring your resume, and writing cover letters.

It is a fully automated, end-to-end Python system that:
1. **Scrapes** real-time job postings from LinkedIn.
2. **Filters** out irrelevant roles or bad locations.
3. **Reads** your personal Resume and uses **Advanced AI** (Gemini, OpenAI, or Anthropic) to compare it against the job description, scoring how good of a match you are.
4. **Auto-Generates** a customized Resume and Cover Letter specifically for jobs that score high ("Dream Jobs").
5. **Syncs** everything (including links to the generated PDFs) directly to a **Google Sheet** so you can track your applications in real-time.

---

## 🌟 Why is this system unique? (Key Features)

- **🧠 Universal AI Hub:** Don't want to pay for OpenAI? No problem! This system supports Google Gemini (Free tier), OpenAI (ChatGPT), and Anthropic (Claude). It can even rotate between multiple API keys automatically if you hit rate limits.
- **🔄 Background Monitor (Magic Mode):** The system has a background worker (`monitor_sheet.py`). If you are looking at your Google Sheet and see a job you like, just type `true` in the "Resume" column. The Python script running in the background will instantly detect it, generate your PDF Resume and Cover Letter, and put the Google Drive links back into the sheet within seconds!
- **📱 Telegram Alerts:** Get a ping on your phone the second the AI finds a job that is a perfect match for you.
- **☁️ Cloud Native:** Saves all your generated documents directly directly to your Google Drive via Google Docs API.

---

## 🛠️ Complete Step-by-Step Setup Guide

This guide assumes you are a beginner. Follow every step carefully to get this running on your PC.

### Step 1: Install Prerequisites
1. **Python 3.11.9+**: [python.org](https://www.python.org/). *Check "Add Python to PATH" during install.*
2. **Git**: [git-scm.com](https://git-scm.com/).

### Step 2: Download the Project
```bash
git clone <your-github-repo-url>
cd "LinkedIn-job-automation"
```

### Step 3: Install Required Python Libraries
We need to install the tools that make this script work (like Google APIs, Apify, and AI libraries). Run this command in your terminal:

```bash
pip install -r requirements.txt
```

#### 🔍 Customizing Job Filters
You can easily change which jobs are saved and which are ignored by editing `filter_jobs.py` in Notepad:

1. **Open Filter Script:** Run `notepad filter_jobs.py` in your terminal.
2. **Edit TARGET_TITLES (Line 17):** Add or remove job titles you are interested in.
3. **Edit BLACKLIST_KEYWORDS (Line 47):** Add keywords you want to EXCLUDE (e.g., "internship", "volunteer", "freelance").
4. **Edit MIN_SALARY_THRESHOLD (Line 52):** Set your minimum required salary (e.g., 50000). If a job mentions a salary, the script will check if it meets this value. If no salary is mentioned, it will still pass through.
5. **Save & Close:** Press `Ctrl + S` and close Notepad.
6. **Run Filter:** Select option 2 in `main.py` to apply your new filters.

---

### Step 4: Configuration

#### ⚙️ System Configuration
The project uses several configuration files to manage data flow and security. **DO NOT edit the .example files directly!** Follow these steps instead:

**1. Copy the Templates (Rename)**
Open your terminal in the project folder and run these commands to create your real configuration files:
```powershell
cp resume.json.example resume.json
cp sheet_config.json.example sheet_config.json
cp .env.example .env
cp .docs.env.example .docs.env  # Optional: For separate Doc Gen keys
```

**2. Open & Edit Files**
To open these files in **Notepad**, run these commands:
- **Resume:** `notepad resume.json`
- **Main Config:** `notepad .env`
- **Doc Gen Keys:** `notepad .docs.env`
- **Sheet Info:** `notepad sheet_config.json`

**3. How to Save Your Changes**
1. Press **`Ctrl + S`** to Save.
2. Close Notepad.

**4. Summary of Files & Actions:**

| File Name | Mandatory Action | What to Fill? |
| :--- | :--- | :--- |
| **`resume.json`** | **Edit** | Your personal experience, skills, and summary. |
| **`.env`** | **Edit** | Your Apify Token and AI API Keys. |
| **`Client ID & Secret`** | **Copy & Paste** | Get from Google Cloud Console and paste in **`.env`**. |
| **`sheet_config.json`** | **Edit** | Your Google Sheet ID. |
| **`token.json`** | **Do Nothing** | Created **automatically** when you first log in. |

*Note: These files are automatically ignored by Git to keep your data safe!*

---

### Step 5: Getting Your API Keys (Crucial Step)
If you don't have your keys yet, follow these steps to get them:

**A. Apify API Key (For Scraping LinkedIn)**
Apify acts as the engine to scrape LinkedIn without getting blocked.
1. Go to [Apify.com](https://apify.com/) and create a free account.
2. In the left sidebar, go to **Settings** -> **Integrations**.
3. Copy your **Personal API Token**.
4. Paste it in `.env` like this: `APIFY_API_TOKEN=your_copied_token_here`

**B. AI Provider Key (For Scoring & Writing Resumes)**
You only need ONE of these. Google Gemini has a generous free tier, so we recommend that.
1. **Gemini:** Go to [Google AI Studio](https://aistudio.google.com/), sign in, and click "Create API Key".
2. Paste it in `.env` like this: `GEMINI_API_KEY=your_gemini_key_here`
*(Advanced: You can comma-separate multiple keys `key1,key2` to avoid rate limits).*

---

### Step 6: Setting up Google Sheets & Google Drive (Modern Auth) 🛠️

1.  **Google Cloud Console:** Go to [console.cloud.google.com](https://console.cloud.google.com/) and create a **New Project**.
2.  **Enable APIs:** In the sidebar, go to **Library** and enable these 3 APIs:
    - **Google Sheets API**
    - **Google Drive API**
    - **Google Docs API**
3.  **OAuth Consent Screen:**
    - Select **External** and click **Create**.
    - **Scopes (Permissions):** Click **"Add or Remove Scopes"** and manually add these 3 URLs:
        - `https://www.googleapis.com/auth/documents`
        - `https://www.googleapis.com/auth/drive`
        - `https://www.googleapis.com/auth/spreadsheets`
    - **Test User:** Scroll down to the **Test users** section and add your own **Gmail address**. (Note: Login will fail if your email is not added here!)
4.  **Credentials:**
    - Go to **Credentials** tab -> click **+ CREATE CREDENTIALS** -> **OAuth client ID**.
    - **Application type:** Select **Desktop App** (Mandatory).
    - Give it a name (e.g., "JobBot") and click **Create**.
5.  **Update `.env`**: Copy the **Client ID** and **Client Secret** shown on the screen and paste them into your **`.env`** file.

---

### 📊 Customizing Your Google Sheets Headers (Dynamic Mapping)

Want to change the header names in your Google Sheet? You don't need to touch a single line of Python code! Everything is managed via `sheet_config.json`.

![Sheet Configuration Guide](./docs/images/sheet_config_guide.png)

#### 📝 How it works:
Inside `sheet_config.json`, the `column_mapping` section links **Sheet Headers** (on the left) to **Job Data** (on the right).

**Example:**
```json
"column_mapping": {
    "My Custom Header": "title",
    "Company Name": "companyName",
    "Application Link": "link"
}
```
- **"My Custom Header":** This is exactly what you will see in Row 1 of your Google Sheet.
- **"title":** This is the internal data name (Do not change these!).

#### 🛠️ How to Add or Change Headers:
1. Open `sheet_config.json`.
2. To **Rename** a header: Change the text on the **left side** (e.g., change `"job_title"` to `"Job Name"`).
3. To **Add** a new header: Add a new line like `"New Column": "data_field"`.
4. **Save** the file and run Option 5 or 6 in `main.py`. The script will automatically detect the new headers and update your sheet!

---

## 🚀 How to Run the System
1. Run: `python main.py`
2. **Login:** A browser window will open. Login with your Gmail and click **Allow**. This creates your `token.json`.

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

📋 **What each option does:**
- **1 to 5:** Runs individual parts of the system if you only want to do one specific task.
- **6. 📈 Run All (The Daily Run):** Press this every morning. It will launch the Apify scraper, pull new LinkedIn jobs, use Gemini/OpenAI to score every single one against your `resume.json`, generate PDFs for the top-scoring jobs, and push everything into a beautiful Google Sheet.
- **7. ☀️ Start Background Monitor (Interactive AI):** If you choose option 7, the script will stay open and "watch" your Google Sheet. If you open your Google Sheet on your phone or laptop and manually change a cell in the "Resume" column to `true`, the background monitor will instantly notice, wake up the AI, generate a custom Resume specifically for that row, save it to your Google Drive, and replace the word `true` with the actual Google Docs link!
- **8. 📝 Auto-Generate All:** If you marked 10 jobs as `true` while the script was off, press 8, and it will generate all 10 in one go.

---

## 📂 Project Structure Explanation (For Techies)
- **`main.py`**: The heart of the system containing the interactive menu.
- **`llm_hub.py`**: A brilliant universal adapter that easily switches between Gemini, OpenAI, and Anthropic APIs.
- **`save_to_sheets.py`**: The robust Google Sheets sync engine that handles column mapping and data deduplication.
- **`sheet_config.json`**: Allows you to customize exactly which columns appear in your Google Sheet without changing Python code.
- **`resume_prompt.txt` / `cover_letter_prompt.txt`**: The secret sauce. These are the highly optimized system prompts that tell the AI exactly how to write top-tier ATS resumes.

---

## 🧠 Customizing the AI (Prompts & Resume)
This system is built around three core files that you should edit to match your specific profile:

1. **`resume.json`**: This is your digital brain. The AI reads this file to understand your experience, skills, and education to score jobs. You **MUST** edit this file with your real profile before running the system.
2. **`resume_prompt.txt`**: This tells the AI how to write your tailored resume. Open this file and update the `=== CANDIDATE PROFILE ===` section with a high-level summary of your career.
3. **`cover_letter_prompt.txt`**: This tells the AI how to write your cover letter. Update the `=== CANDIDATE PROFILE ===` section here as well, so the AI knows your background and preferred tone of writing.
4. **`ai_prompt.txt`**: The internal criteria the AI uses to score jobs out of 100. (You don't need to edit this unless you want to change the scoring weights).

---

## 🔐 Understanding the System Files (JSONs & State)
- **`.env`**: **(The Secret Vault)** Stores all private API keys (Apify, Gemini, **Google Client ID & Secret**). 
- **`token.json`**: **(The Permission Slip)** Stores your session token so you don't have to login again.
- **`auth_util.py`**: **(The Central Brain)** Handles all Google logins. Replaces the old `credentials.json` system.
- **`sheet_config.json`**: **(The Translator)** Matches job data to your Google Sheet columns.
- **`.llm_scoring_state.json`**: Tracks scored jobs to save API costs.
- **`.llm_docs_state.json`**: Tracks generated resumes to avoid duplicates.

---

## 🤝 Need Custom Automation?
If you're looking for someone to build a custom automation system, web scraper, or AI-powered pipeline like this one, I'd love to help!

📧 **Contact Me:** vishupal4102@gmail.com

Let's build something amazing together! 🚀🔥

Enjoy your completely automated job hunting experience! 🌟
