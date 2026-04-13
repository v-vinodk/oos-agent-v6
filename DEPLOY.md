# Deploy to Streamlit Cloud — 3 steps

## Step 1 — Run the deploy script (pushes to GitHub automatically)

```bash
cd oos_agent_v5
bash deploy.sh
```

The script will:
- Ask your GitHub username and repo name
- Commit and push all your code to a private GitHub repo
- Print the exact secrets block to paste into Streamlit Cloud

If you have the GitHub CLI (`gh`) installed it creates the repo for you.
If not, it walks you through creating it manually (30 seconds).

---

## Step 2 — Generate your Streamlit secrets

Once you have your GCP service account JSON key file, run:

```bash
python generate_secrets.py --key /path/to/your-service-account-key.json
```

This prints a ready-to-paste secrets block with all your values pre-filled.

**Don't have a service account key yet?**
1. Go to https://console.cloud.google.com → IAM & Admin → Service Accounts
2. Create service account → name: `oos-agent`
3. Grant roles: `BigQuery Data Viewer` + `BigQuery Job User`
4. Keys tab → Add Key → JSON → download the file
5. Run the command above pointing at that file

---

## Step 3 — Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io → sign in with GitHub
2. Click **Create app**
3. Fill in:
   - Repository: `your-username/oos-agent`
   - Branch: `main`
   - Main file: `app.py`
4. Click **Advanced settings → Secrets**
5. Paste the output from Step 2
6. Click **Deploy**

Your app is live in ~2 minutes at:
`https://your-username-oos-agent-app-xxxx.streamlit.app`

---

## Share with your team

Send the URL to your teammates. They log in with:

| Username | Password | Role |
|---|---|---|
| category_manager | noon2024 | manager |
| analyst | analyst123 | analyst |
| admin | admin123 | admin |

To add new users, edit `auth/auth.py` → `USERS` dict → push to GitHub → auto-redeploys.

---

## Future updates

Any time you update the code:
```bash
git add .
git commit -m "your change description"
git push
```
Streamlit Cloud redeploys automatically within ~30 seconds.
