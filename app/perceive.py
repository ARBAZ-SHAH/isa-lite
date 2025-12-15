import pandas as pd, yaml, json
from datetime import datetime

def load_data():
    dl = pd.read_csv("data/deadlines.csv", parse_dates=["date"])
    ev = pd.read_csv("data/events.csv", parse_dates=["date"])
    cfg = yaml.safe_load(open("config.yaml"))
    return dl, ev, cfg

def derive_progress(ev):
    # simple completion % per subject (last 7 days)
    lately = ev[ev["date"] >= (ev["date"].max() - pd.Timedelta(days=7))]
    if lately.empty: return {}
    g = lately.groupby("subject")["completed"].mean().to_dict()
    return {s: float(v) for s,v in g.items()}

def to_prolog_facts(dl, progress, cfg):
    facts = []
    facts.append(f"hours_per_day({cfg['daily_hours_max_min']}).")
    facts.append(f"exam_near_days({cfg['exam_near_days']}).")
    for _,r in dl.iterrows():
        s = r["subject"].strip().lower()
        facts += [f"subject({s}).",
                  f"difficulty({s},{int(r['difficulty'])})."]
        y,m,d = r["date"].year, r["date"].month, r["date"].day
        facts.append(f"deadline({s},{r['type']},date({y},{m},{d})).")
    for s,p in progress.items():
        facts.append(f"progress({s.lower()},completion_pct,{p:.2f}).")
    return "\n".join(sorted(set(facts)))

if __name__ == "__main__":
    dl, ev, cfg = load_data()
    prg = derive_progress(ev)
    facts = to_prolog_facts(dl, prg, cfg)
    open("engines/facts.pl","w").write(facts+"\n")
    print("[perceive] wrote engines/facts.pl")
