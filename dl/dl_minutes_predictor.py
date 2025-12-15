import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORT = ROOT / "report"
REPORT.mkdir(parents=True, exist_ok=True)

ev = pd.read_csv(DATA / "events.csv", parse_dates=["date"])
dl = pd.read_csv(DATA / "deadlines.csv", parse_dates=["date"])

# ----- Feature join -----
df = ev.merge(
    dl[["subject", "date", "difficulty"]].rename(columns={"date": "ddl_date"}),
    on="subject",
    how="left",
)

df["days_to_deadline"] = (df["ddl_date"] - df["date"]).dt.days
df["days_to_deadline"] = df["days_to_deadline"].fillna(14).clip(lower=0, upper=60)

# rolling completion signal (per subject)
df["past_completion"] = (
    df.groupby("subject")["completed"]
      .shift(1)
      .fillna(0)
      .rolling(3, min_periods=1)
      .mean()
      .reset_index(level=0, drop=True)
).fillna(0)

df["difficulty"] = df["difficulty"].fillna(3).clip(lower=1, upper=5)

# subject index
subs = {s: i for i, s in enumerate(sorted(df["subject"].unique()))}
df["sub_ix"] = df["subject"].map(subs).astype(int)

# X, y
X_np = df[["sub_ix", "difficulty", "days_to_deadline", "past_completion"]].values.astype("float32")
y_np = df["est_min"].values.astype("float32").reshape(-1, 1)

# ----- Train/test split (simple + deterministic) -----
n = len(df)
if n < 6:
    raise SystemExit("[dl] Not enough rows in events.csv. Add more events (>= 6) for train/test split.")

idx = np.arange(n)
rng = np.random.default_rng(42)
rng.shuffle(idx)

test_size = max(2, int(0.3 * n))
test_idx = idx[:test_size]
train_idx = idx[test_size:]

X_train = torch.tensor(X_np[train_idx])
y_train = torch.tensor(y_np[train_idx])
X_test  = torch.tensor(X_np[test_idx])
y_test  = torch.tensor(y_np[test_idx])

n_sub = len(subs)
emb = 4

class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.emb = nn.Embedding(n_sub, emb)
        self.net = nn.Sequential(
            nn.Linear(emb + 3, 32), nn.ReLU(),
            nn.Linear(32, 16), nn.ReLU(),
            nn.Linear(16, 1)
        )
    def forward(self, x):
        s = x[:, 0].long()
        rest = x[:, 1:]
        z = torch.cat([self.emb(s), rest], dim=1)
        return self.net(z)

model = MLP()
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
lossf = nn.L1Loss()  # MAE

# ----- Baseline: predict mean(est_min) from train -----
baseline_pred = float(y_train.mean().item())
baseline_mae = float(torch.mean(torch.abs(y_test - baseline_pred)).item())

# ----- Train -----
model.train()
for epoch in range(300):
    opt.zero_grad()
    pred = model(X_train)
    loss = lossf(pred, y_train)
    loss.backward()
    opt.step()

# ----- Evaluate -----
model.eval()
with torch.no_grad():
    pred_test = model(X_test)
    test_mae = float(lossf(pred_test, y_test).item())

report = {
    "mode": "pytorch_mlp_minutes_predictor",
    "n_rows": int(n),
    "n_train": int(len(train_idx)),
    "n_test": int(len(test_idx)),
    "features": ["sub_ix(embedding)", "difficulty", "days_to_deadline", "past_completion"],
    "baseline": {"type": "mean_est_min", "mae_minutes": round(baseline_mae, 3)},
    "dl_model": {"mae_minutes": round(test_mae, 3)},
    "subjects": subs,
}

(REPORT / "dl_minutes_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("[dl] wrote report/dl_minutes_report.json")
print(json.dumps(report, indent=2))
