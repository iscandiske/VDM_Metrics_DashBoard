# Agency Ads Dashboard — Streamlit App

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy FREE on Streamlit Community Cloud (recommended)

1. Push this folder to a GitHub repo (public or private)
2. Go to https://share.streamlit.io → "New app"
3. Connect your GitHub repo → select `app.py`
4. Click "Advanced settings" → paste your Google secrets (see below)
5. Deploy — you get a public URL to share with your team

## Connect Google Sheets (optional but recommended)

### Step 1 — Create a service account
1. Go to https://console.cloud.google.com
2. Create a new project (or use existing)
3. Enable **Google Sheets API** and **Google Drive API**
4. Go to IAM → Service Accounts → Create
5. Download the JSON key file

### Step 2 — Share your sheet
- Open your Google Sheet
- Click Share → paste the service account email (ends in `.iam.gserviceaccount.com`)
- Give it Editor access

### Step 3 — Add secrets to Streamlit
In Streamlit Cloud → App Settings → Secrets, paste:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

## Google Sheet structure

Sheet name must be: **Accounts**

Columns (row 1 headers, exact lowercase):
| name | industry | spend | roas | cpl | leads | ctr | cpc | frequency | engagements | impressions | status |

Pipeline sheet (auto-created): **Pipeline**

## Features
- Overview tab: top 5 / worst 5 rankings with chart, switchable KPI
- All accounts tab: full table with color-coded ROAS, CPL, CPE, Frequency
- New clients tab: pipeline from Prospect → Onboarding
- Add accounts and deals directly in the app
- Sync to/from Google Sheets
