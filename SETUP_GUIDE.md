# Automation Setup Guide: GitHub Actions + Vertex AI + Google Drive API

This guide walks you through connecting your Google Cloud project and Google Drive with GitHub Actions to automatically generate, publish, and sync 1500+ word articles.

---

## 🛠️ Step 1: Google Cloud Setup

### 1. Enable Required Google Cloud APIs
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Select your Project (or create a new one).
3. Navigate to **APIs & Services > Library** and enable:
   - **Vertex AI API** (`aiplatform.googleapis.com`)
   - **Google Drive API** (`drive.googleapis.com`)

### 2. Create a Service Account
1. In Cloud Console, go to **IAM & Admin > Service Accounts**.
2. Click **Create Service Account**:
   - **Name**: `nexussphere-automation`
   - **Role**: Grant **Vertex AI User** (`roles/aiplatform.user`).
3. Click **Done**.
4. Click on your newly created service account, navigate to the **Keys** tab, and click **Add Key > Create new key > JSON**.
5. Save the downloaded JSON file safely (this is your `GCP_SA_KEY`).

---

## 📁 Step 2: Google Drive Folder Setup

1. Open [Google Drive](https://drive.google.com/).
2. Create an **Input Folder** (e.g. `NexusSphere_Drafts`) where you will place topic briefs (`.txt` or `.md` files).
3. (Optional) Create a **Backup Folder** (e.g. `NexusSphere_Published`).
4. Click **Share** on both folders and add your Service Account email (e.g. `nexussphere-automation@<your-project-id>.iam.gserviceaccount.com`) as **Editor**.
5. Copy the Folder ID from the URL:
   - URL: `https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ`
   - Folder ID is: `1aBcDeFgHiJkLmNoPqRsTuVwXyZ`

---

## 🔐 Step 3: Add GitHub Secrets

1. Go to your GitHub Repository: [https://github.com/muhammadhabib00001/ai-website](https://github.com/muhammadhabib00001/ai-website)
2. Go to **Settings > Secrets and variables > Actions**.
3. Click **New repository secret** and add:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `GCP_SA_KEY` | Entire content of your downloaded Service Account JSON key | `{"type": "service_account", ...}` |
| `GCP_PROJECT_ID` | Your Google Cloud Project ID | `my-gcp-project-12345` |
| `DRIVE_FOLDER_ID` | Google Drive Input Folder ID (optional) | `1aBcDeFgHiJkLmNoPqRsTuVwXyZ` |
| `DRIVE_BACKUP_FOLDER_ID` | Google Drive Output Folder ID (optional) | `2bCdEfGhIjKlMnOpQrStUvWxYzA` |

---

## 🚀 Step 4: Running the Automation

### 1. Manual On-Demand Trigger:
1. In your GitHub repository, click on the **Actions** tab.
2. Select **"NexusSphere AI Content & Google Drive Automation"** on the left.
3. Click **Run workflow**:
   - You can type a custom topic (e.g. *"Quantum Computing Breakthroughs in Material Science"*).
   - Or leave it blank to pull topic briefs automatically from your Google Drive folder!
4. Click **Run workflow**.

### 2. Automatic Scheduled Trigger:
- The pipeline runs automatically every **Monday at 06:00 UTC** via cron.
- It generates the comprehensive 1500+ word publication, formats it into responsive HTML, commits it to GitHub, and backs it up to Google Drive.
