#!/bin/bash
# ── noon OOS Agent — one-shot setup script ────────────────────────────────────
set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║      noon OOS Analytics Agent — Setup            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 1. Python venv
echo "▶ Step 1/4 — Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "  ✅ venv created"

# 2. Dependencies
echo ""
echo "▶ Step 2/4 — Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✅ packages installed"

# 3. GCP auth
echo ""
echo "▶ Step 3/4 — BigQuery authentication"
echo "  Choose your auth method:"
echo ""
echo "  [1] gcloud CLI  (recommended if gcloud is installed)"
echo "  [2] Service account key file  (for production / CI)"
echo "  [3] Skip  (app will use mock data until you auth)"
echo ""
read -p "  Enter choice [1/2/3]: " AUTH_CHOICE

if [ "$AUTH_CHOICE" = "1" ]; then
    echo "  Running: gcloud auth application-default login"
    gcloud auth application-default login
    echo "  ✅ gcloud ADC configured"

elif [ "$AUTH_CHOICE" = "2" ]; then
    read -p "  Path to service account JSON key file: " KEY_PATH
    if [ -f "$KEY_PATH" ]; then
        echo "GOOGLE_APPLICATION_CREDENTIALS=$KEY_PATH" >> .env
        echo "  ✅ Key path added to .env"
    else
        echo "  ⚠️  File not found. Add GOOGLE_APPLICATION_CREDENTIALS manually to .env"
    fi
else
    echo "  ⏭  Skipped — app will use mock data until BigQuery auth is set up"
fi

# 4. Schema check
echo ""
echo "▶ Step 4/4 — Verifying BigQuery table schema..."
python data/schema_check.py

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ Setup complete!                              ║"
echo "║                                                  ║"
echo "║  Run the app:                                    ║"
echo "║    source venv/bin/activate                      ║"
echo "║    streamlit run app.py                          ║"
echo "║                                                  ║"
echo "║  Opens at: http://localhost:8501                 ║"
echo "║                                                  ║"
echo "║  Login with:                                     ║"
echo "║    username: category_manager                    ║"
echo "║    password: noon2024                            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
