# StudentLife Visual Analytics Dashboard

**Dissertation: Visual Analytics for Digital Health**  
Author: Rohith Elanchezhian | Newcastle University

---

## How to run locally

**Step 1 — Install Python dependencies**
```bash
pip install -r requirements.txt
```

**Step 2 — Run the dashboard**
```bash
streamlit run app.py
```

**Step 3 — Upload your data**  
When the browser opens, upload your `daily_master.csv` file.  
Find it in: Google Drive → clean_data → daily_master.csv

---

## How to deploy to Streamlit Cloud (free public URL)

1. Go to [github.com](https://github.com) and create a free account
2. Create a new repository called `studentlife-dashboard`
3. Upload these three files:
   - `app.py`
   - `requirements.txt`
   - `README.md`
4. Go to [share.streamlit.io](https://share.streamlit.io)
5. Sign in with GitHub
6. Click **New app**
7. Select your repository and set main file to `app.py`
8. Click **Deploy** — done!

You will get a URL like:  
`https://rohith-studentlife.streamlit.app`

Share this URL with your evaluation participants.

---

## Dashboard views

| Tab | What it shows |
|-----|--------------|
| Overview | Summary stats + distributions |
| Weekly Trends | All variables across the 10-week term |
| Correlations | Scatter plots + correlation matrix |
| Stress Heatmap | Every student × every week |
| Student Explorer | Individual student profiles |

---

## Filters (sidebar)
- **Study week** — zoom into one specific week
- **Day type** — compare weekdays vs weekends
