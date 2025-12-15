import re, json, datetime as dt
# Deterministic fallback (no external API needed)
def parse_text(t):
    # "Add Physics quiz on Fri 3pm; need 2 hrs"
    subj = re.findall(r"(Math|Physics|Chemistry|English)", t, re.I)
    est = re.findall(r"(\d+)\s*hr", t, re.I)
    date = re.findall(r"(\d{4}-\d{2}-\d{2})", t)
    return {
        "subject": (subj[0] if subj else "General").title(),
        "type": "task",
        "date": (date[0] if date else dt.date.today().isoformat()),
        "est_min": int(est[0])*60 if est else 60
    }

if __name__=="__main__":
    print(parse_text("Add Physics quiz on 2025-10-17; need 2 hr"))
