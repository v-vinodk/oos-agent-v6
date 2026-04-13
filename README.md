# noon OOS Analytics Agent

AI-powered out-of-stock analytics for category managers at noon.com.
Powered by Claude + BigQuery (`noonbigmktgsandbox.vinod.oos_sku_daily`).

---

## QUICKSTART (3 steps)

### Step 1 — Unzip and open a terminal in the project folder

```bash
cd oos_agent_v3
```

### Step 2 — Run the setup script

```bash
bash setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Walk you through BigQuery authentication
- Verify your table schema
- Print your login credentials

### Step 3 — Launch

```bash
source venv/bin/activate
streamlit run app.py
```

Opens at **http://localhost:8501**

---

## Login credentials

| Username           | Password     | Role    |
|--------------------|--------------|---------|
| admin              | admin123     | admin   |
| category_manager   | noon2024     | manager |
| analyst            | analyst123   | analyst |

---

## BigQuery authentication options

### Option A — gcloud CLI (easiest for local dev)

```bash
# Install gcloud if needed: https://cloud.google.com/sdk/docs/install
gcloud auth application-default login
```

### Option B — Service account key

1. Go to GCP Console → IAM & Admin → Service Accounts
2. Create or select a service account with:
   - `roles/bigquery.dataViewer`
   - `roles/bigquery.jobUser`
3. Download the JSON key file
4. Add to `.env`:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json
   ```

---

## Configuration

All config lives in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-api03-...       # Claude API key
BQ_PROJECT=noonbigmktgsandbox            # GCP project
BQ_DATASET=vinod                         # BigQuery dataset
BQ_TABLE=oos_sku_daily                   # Table name
GOOGLE_APPLICATION_CREDENTIALS=...      # Path to service account key (if using Option B)
```

---

## How the schema mapping works

The app auto-detects your table columns on startup and maps them to standard names.
Run this to see exactly how your columns are mapped:

```bash
python data/schema_check.py
```

If a column isn't found, the app either derives it (e.g. `days_of_supply = stock / sales_rate`)
or falls back to mock data for that field.

---

## Inline charts — what gets auto-rendered

| Question type             | Chart shown                              |
|---------------------------|------------------------------------------|
| GMV loss                  | Bar by category + bar by region          |
| Root cause                | Donut chart with % breakdown             |
| Trend / better or worse   | Dual-axis area + line over time          |
| At-risk SKUs              | Horizontal bar, color = urgency          |
| Retail vs marketplace     | Side-by-side bar comparison              |

---

## Project structure

```
oos_agent_v3/
├── app.py                        # Streamlit UI (auth + chat + sidebar)
├── setup.sh                      # One-shot setup script
├── auth/
│   └── auth.py                   # Login screen + hashed passwords
├── agent/
│   ├── core.py                   # Agentic loop with tool use
│   ├── tools.py                  # 6 OOS analysis tools
│   └── prompts.py                # Claude system prompt
├── components/
│   └── charts.py                 # Auto chart renderer
├── data/
│   ├── bigquery.py               # BQ client, schema detection, caching
│   ├── schema_check.py           # Run this to inspect your table
│   └── mock_data.py              # Fallback sample data
├── .env                          # Your credentials (do not commit)
├── .streamlit/secrets.toml       # Streamlit Cloud secrets (do not commit)
└── requirements.txt
```

---

## Deploy to Streamlit Cloud

1. Push to a private GitHub repo (`.env` must be in `.gitignore`)
2. Go to https://share.streamlit.io → New app
3. Select repo, main file = `app.py`
4. In **Advanced → Secrets**, paste:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
BQ_PROJECT = "noonbigmktgsandbox"
BQ_DATASET = "vinod"
BQ_TABLE   = "oos_sku_daily"

[gcp_service_account]
type = "service_account"
project_id = "noonbigmktgsandbox"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-sa@noonbigmktgsandbox.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

5. Click Deploy ✓
