# StudentLife Visual Analytics Dashboard

Interactive visual analytics for exploring student wellbeing through passive smartphone
sensing data.

**Live dashboard:** https://studentlife-dashboard-online.streamlit.app

MSc Data Science and AI dissertation project
Rohith Elanchezhian · Supervisor: Alaa Alahmadi · School of Computing, Newcastle University

---

## What this is

University mental health services are largely reactive: they respond to crises rather than
detecting the deterioration that precedes them. This project asks whether the data students'
smartphones already collect — movement, conversation, sleep, physical proximity to others —
can be used to explore and monitor wellbeing across an academic term.

The dashboard sits on top of the [StudentLife dataset](https://www.kaggle.com/datasets/dartweichen/student-life)
(Wang et al., 2014), in which 49 Dartmouth College undergraduates were monitored continuously
for ten weeks in Spring 2013. It provides seven coordinated views over the cleaned data,
alongside machine learning predictions of daily stress.

---

## The seven views

| Tab | What it shows |
|---|---|
| **Overview** | Headline statistics and distributions for the current filter |
| **Weekly Trends** | Stress, sleep, mood and conversation time across the term |
| **Correlations** | User-selectable scatter plots with trend lines, plus a correlation matrix |
| **Stress Heatmap** | Student-by-week grid, green (calm) through red (high stress) |
| **Student Explorer** | Individual profile with stress, sleep and model predictions |
| **Compare Students** | Two students side by side |
| **ML Predictions** | Model performance, feature importance and behavioural clusters |

Sidebar filters for study week and day type propagate across every view.

---

## Running it locally

```bash
git clone https://github.com/rohithkombat/studentlife-dashboard.git
cd studentlife-dashboard
pip install -r requirements.txt
streamlit run app.py
```

The app reads its data from the `data/` folder in this repository — no upload step and no
configuration required. It opens at `http://localhost:8501`.

---

## Data files

The dashboard requires one file and optionally uses four more:

| File | Required | Contents |
|---|---|---|
| `data/daily_master.csv` | yes | One row per student per day, all variables merged |
| `data/ml_predictions.csv` | no | Actual and predicted stress per student-day |
| `data/ml_performance.csv` | no | Cross-validated scores for every model |
| `data/ml_feature_importance.csv` | no | Random Forest feature importance scores |
| `data/ml_clusters.csv` | no | K-Means cluster assignment per student |

If the four ML files are absent the dashboard still runs; the ML tab shows a placeholder
rather than failing.

### Regenerating the data

The intermediate cleaned files (activity, Bluetooth and conversation streams) run to
hundreds of megabytes and are deliberately not committed here. To regenerate everything
from source:

1. Download the raw dataset from
   [Kaggle](https://www.kaggle.com/datasets/dartweichen/student-life) and extract it to a
   Google Drive folder.
2. Run `StudentLife_DataCleaning_FINAL.ipynb` — produces nine cleaned CSVs plus
   `daily_master.csv`.
3. Run `StudentLife_ML_SaveFiles.ipynb` — produces the four `ml_*.csv` files.
4. Copy `daily_master.csv` and the four ML files into `data/`.

---

## Results summary

**Stress.** Mean 2.24 out of 5, with 18.4% of days rated high stress (level 4 or 5).
Finals week stood well clear at 3.38 against a rest-of-term mean of 2.23
(t = 2.73, p = .007, Cohen's d = 0.97).

**Weekends.** Weekend stress ran higher than weekday stress (2.36 versus 2.20), which is the
opposite of what one might expect. The difference did **not** reach significance
(p = .078) and is reported as a trend rather than a finding.

**Sleep.** Mean 7.37 hours with quality rated 1.87 out of 5. No significant daily-level
association with stress (r = −0.05, p = .19), despite both variables peaking together around
finals — a shared external cause rather than a direct relationship.

**Machine learning.** Passive sensing features alone barely improved on a mean-prediction
baseline (1.5%). Adding one per-student baseline feature — that student's own mean stress,
computed inside each cross-validation fold from training rows only — raised this to 8.7%
(MAE 0.931 against 1.020) and lifted classification AUC from 0.628 to 0.707. The
interpretation is that between-person variation, not the sensing signal, was the binding
constraint.

**Feature importance.** Conversation minutes (0.154) and movement fractions outranked sleep
hours (0.066, seventh of eleven) and sleep quality (0.039, ninth). This runs against the
emphasis placed on sleep in much of the digital phenotyping literature.

---

## Known limitations

**Coverage.** The aggregated dataset retains 39 of the 49 students and spans study weeks 5
to 10 rather than the full term. Earlier weeks are present as rows but lack a `study_week`
label, so they are excluded from weekly breakdowns. All results should be read as describing
the second half of the term for a subset of the cohort.

**Upper-bound estimates.** Cross-validation folds are randomly shuffled rather than ordered
in time, so a student's baseline feature draws on days from across the whole term, including
days later than the one being predicted. A deployed system would have only the student's
past. The reported figures are therefore an upper bound.

**No user evaluation.** The dashboard has been functionally verified against the analysis
pipeline but has not been evaluated with users. No claim is made about usability or task
support.

**Conversation measurement.** The microphone detects speech *near* the phone, not
necessarily speech *by* the student. Lectures and ambient conversation are included, so
daily totals of several hours are expected and should be read as conversation exposure
rather than time spent talking.

---

## Built with

Python · Streamlit · Plotly · pandas · NumPy · scikit-learn · SciPy

---

## Reference

Wang, R., Chen, F., Chen, Z., Li, T., Harari, G., Tignor, S., Zhou, X., Ben-Zeev, D., and
Campbell, A.T. (2014). StudentLife: Assessing mental health, academic performance and
behavioral trends of college students using smartphones. *Proceedings of ACM UbiComp 2014*,
3–14. https://doi.org/10.1145/2632048.2632054

Dataset available at https://www.kaggle.com/datasets/dartweichen/student-life
