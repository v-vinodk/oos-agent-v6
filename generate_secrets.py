#!/usr/bin/env python3
"""
Run this once to generate a ready-to-paste Streamlit secrets block.
It reads your .env and your GCP service account JSON key, then prints
the exact text to paste into Streamlit Cloud → Advanced settings → Secrets.

Usage:
    python generate_secrets.py
    python generate_secrets.py --key /path/to/service-account.json
"""
import os, sys, json, argparse

def load_env():
    env = {}
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", help="Path to GCP service account JSON key file", default=None)
    args = parser.parse_args()

    env = load_env()
    anthropic_key = env.get("ANTHROPIC_API_KEY", "sk-ant-YOUR_KEY_HERE")
    bq_project    = env.get("BQ_PROJECT", "noonbigmktgsandbox")
    bq_dataset    = env.get("BQ_DATASET", "vinod")
    bq_table      = env.get("BQ_TABLE",   "oos_sku_daily")

    # Load service account JSON if provided
    sa = {}
    key_path = args.key or env.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path and os.path.exists(key_path):
        with open(key_path) as f:
            sa = json.load(f)
        print(f"✅ Loaded service account from: {key_path}\n")
    else:
        print("⚠️  No service account JSON found.")
        print("   Run with: python generate_secrets.py --key /path/to/key.json\n")

    print("=" * 62)
    print("  PASTE THIS INTO: Streamlit Cloud → Secrets")
    print("=" * 62)
    print(f"""
ANTHROPIC_API_KEY = "{anthropic_key}"
BQ_PROJECT        = "{bq_project}"
BQ_DATASET        = "{bq_dataset}"
BQ_TABLE          = "{bq_table}"

[gcp_service_account]
type            = "{sa.get('type', 'service_account')}"
project_id      = "{sa.get('project_id', bq_project)}"
private_key_id  = "{sa.get('private_key_id', 'PASTE_KEY_ID_HERE')}"
private_key     = "{sa.get('private_key', '-----BEGIN RSA PRIVATE KEY-----\\nPASTE_KEY_HERE\\n-----END RSA PRIVATE KEY-----\\n')}"
client_email    = "{sa.get('client_email', 'oos-agent@' + bq_project + '.iam.gserviceaccount.com')}"
client_id       = "{sa.get('client_id', 'PASTE_CLIENT_ID_HERE')}"
auth_uri        = "{sa.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth')}"
token_uri       = "{sa.get('token_uri', 'https://oauth2.googleapis.com/token')}"
""")
    print("=" * 62)
    print("  Copy everything between the lines above and paste into")
    print("  Streamlit Cloud → your app → Settings → Secrets")
    print("=" * 62)

if __name__ == "__main__":
    main()
