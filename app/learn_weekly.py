import pandas as pd, json
from datetime import datetime, timedelta
WEEK_DAYS = 7

def compute_metrics():
    ev = pd.read_csv("data/events.csv", parse_dates=["date"])
    wk = ev[ev["date"] >= (ev["date"].max() - pd.Timedelta(days=WEEK_DAYS))]
    if wk.empty:
        return {"completion_pct":0,"adherence":0}
    completion = 100*wk["completed"].mean()
    adherence = (wk["done_min"].sum() / max(1,wk["est_min"].sum()))
    return {"completion_pct":round(completion,1),
            "adherence":round(adherence,2)}

if __name__=="__main__":
    m = compute_metrics()
    print("[learn] weekly", m)
    open("report/weekly_metrics.json","w").write(json.dumps(m, indent=2))
