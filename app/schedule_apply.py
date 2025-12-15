import json, yaml, pandas as pd
from datetime import datetime, timedelta

CFG = yaml.safe_load(open("config.yaml"))

def build_day_schedule(plan):
    slots, left = [], CFG["daily_hours_max_min"]
    now = datetime.now().replace(second=0, microsecond=0)
    t = now.replace(hour=17, minute=0)  # start at 5pm (simple)
    for p in sorted(plan, key=lambda x: -x["minutes"]):
        if p["decision"]!="shortlist": continue
        dur = min(p["minutes"], left)
        if dur<=0: break
        slots.append({"subject":p["subject"],"start":t.strftime("%H:%M"),
                      "end":(t+timedelta(minutes=dur)).strftime("%H:%M"),
                      "minutes":dur})
        t += timedelta(minutes=dur+5)
        left -= dur
    return slots

if __name__=="__main__":
    plan = json.load(open("app/plan.json"))
    schedule = build_day_schedule(plan)
    df = pd.DataFrame(schedule)
    print("\n=== TODAY'S PLAN ===")
    print(df if not df.empty else "No sessions.")
    # (You can add email/popup later; for now we print the plan.)
    df.to_csv("data/todays_plan.csv", index=False)
