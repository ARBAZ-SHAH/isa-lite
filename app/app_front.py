# app/app_front.py — Streamlit front page (persistent reports panel)
import streamlit as st
import pandas as pd, json, subprocess, sys, os
from pathlib import Path
import time

# ----- Paths (resolve from repo root) -----
ROOT = Path(__file__).resolve().parents[1]
APP   = ROOT / "app"
DATA  = ROOT / "data"
ENG   = ROOT / "engines"
REP   = ROOT / "report"

DATA.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)

# ----- Session store (persistent outputs) -----
if "reports" not in st.session_state:
    st.session_state.reports = {
        "Perceive": "",
        "Reason": "",
        "Act": "",
        "Learn": "",
        "ML": "",
        "DL": "",
        "PRAL": ""
    }

def save_report(name: str, text: str):
    st.session_state.reports[name] = text.strip()

# ----- Helpers -----
def run_file(pyfile: Path) -> str:
    """Run a Python file with the same interpreter; capture stdout+stderr."""
    env = os.environ.copy()
    p = subprocess.run(
        [sys.executable, str(pyfile)],
        cwd=ROOT, env=env, capture_output=True, text=True
    )
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    if err:
        out += ("\n[stderr]\n" + err)
    return out

def seed_if_missing():
    ev = DATA / "events.csv"
    dl = DATA / "deadlines.csv"
    if not ev.exists():
        ev.write_text(
            "date,subject,est_min,done_min,reminders,completed\n"
            "2025-10-13,Math,60,45,1,0\n"
            "2025-10-13,Physics,45,45,1,1\n"
            "2025-10-14,Math,60,60,2,1\n",
            encoding="utf-8"
        )
    if not dl.exists():
        dl.write_text(
            "subject,type,date,weight,difficulty\n"
            "Math,exam,2025-10-28,1.0,3\n"
            "Physics,quiz,2025-10-18,0.6,2\n",
            encoding="utf-8"
        )

# ----- UI -----
st.set_page_config(page_title="ISA-Lite", layout="wide")
st.title("ISA-Lite • Intelligent Study Assistant")

# Sidebar controls
st.sidebar.header("Controls")
if st.sidebar.button("Seed sample data"):
    seed_if_missing()
    st.sidebar.success("Seeded sample CSVs to /data")

if st.sidebar.button("Clear reports panel"):
    for k in st.session_state.reports:
        st.session_state.reports[k] = ""
    st.sidebar.success("Cleared saved outputs.")

# Load data tables
seed_if_missing()
ev = pd.read_csv(DATA / "events.csv")
dl = pd.read_csv(DATA / "deadlines.csv")

colA, colB = st.columns([1,1])
with colA:
    st.subheader("Data")
    st.markdown("**events.csv**")
    st.dataframe(ev, use_container_width=True)
    st.markdown("**deadlines.csv**")
    st.dataframe(dl, use_container_width=True)

with colB:
    st.subheader("Quick Actions")

    if st.button("Run Perceive"):
        out = run_file(APP / "perceive.py")
        save_report("Perceive", out)
        st.success("Perceive completed. Report saved below.")
        st.code(out)

    if st.button("Run Reason (Prolog)"):
        out = run_file(APP / "run_planner.py")
        save_report("Reason", out)
        st.success("Reason completed. Report saved below.")
        st.code(out)

    if st.button("Run Act (Schedule)"):
        out = run_file(APP / "schedule_apply.py")
        save_report("Act", out)
        st.success("Act completed. Report saved below.")
        st.code(out)

    if st.button("Run Learn (Weekly Metrics)"):
        out = run_file(APP / "learn_weekly.py")
        save_report("Learn", out)
        st.success("Learn completed. Report saved below.")
        st.code(out)

    st.divider()

    if st.button("Run ML (Adherence Predictor)"):
        out = run_file(ROOT / "ml" / "ml_adherence.py")
        save_report("ML", out)
        st.success("ML completed. Report saved below.")
        st.code(out)

    if st.button("Run DL (Minutes Predictor)"):
        out = run_file(ROOT / "dl" / "dl_minutes_predictor.py")
        save_report("DL", out)
        st.success("DL completed. Report saved below.")
        st.code(out)

st.divider()
st.subheader("One-Click Pipeline")

if st.button("Run PRAL (Perceive→Reason→Act→Learn)"):
    t0 = time.time()
    pral_log = []
    for py in [APP/"perceive.py", APP/"run_planner.py", APP/"schedule_apply.py", APP/"learn_weekly.py"]:
        pral_log.append(f"→ {py.relative_to(ROOT)}")
        pral_log.append(run_file(py))
    pral_out = "\n\n".join([x for x in pral_log if x.strip()])

    save_report("PRAL", pral_out)
    st.success(f"PRAL finished in {time.time()-t0:.2f}s. Full report saved below.")
    st.code(pral_out)

st.divider()
st.subheader("Outputs (Generated Files)")

plan_path    = APP  / "plan.json"
today_path   = DATA / "todays_plan.csv"
metrics_path = REP  / "weekly_metrics.json"

if plan_path.exists():
    plan = json.load(open(plan_path, "r", encoding="utf-8"))
    st.markdown("**Planner decisions (Reason output)**")
    st.dataframe(pd.DataFrame(plan), use_container_width=True)

if today_path.exists():
    st.markdown("**Today's schedule (Act output)**")
    st.dataframe(pd.read_csv(today_path), use_container_width=True)

if metrics_path.exists():
    st.markdown("**Weekly metrics (Learn output)**")
    st.json(json.load(open(metrics_path, "r", encoding="utf-8")))

# ----- Persistent Reports Panel -----
st.divider()
st.header("Reports Panel (Saved After Each Run)")

# Show each report in an expander with a clear heading
for name in ["Perceive", "Reason", "Act", "Learn", "ML", "DL", "PRAL"]:
    label = f"Report: {name} (saved output)"
    with st.expander(label, expanded=False):
        txt = st.session_state.reports.get(name, "")
        if txt:
            st.code(txt)
        else:
            st.info(f"No saved output for {name} yet. Run the step to generate it.")
