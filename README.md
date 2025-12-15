Below is a **clean, professional `README.md`** you can copy-paste directly into your repository.
It is written **exactly at the level your ISD (CS-5104) instructor expects**: explicit, structured, PRAL-aligned, and easy to understand without oral explanation.

---

# ISA-Lite — Intelligent Study Assistant

**Course:** CS-5104 Intelligent Systems Design
**Program:** MS Artificial Intelligence
**Student:** Arbaz Shah
**Semester:** Fall (First Semester)

---

## 1. Project Overview

**ISA-Lite (Intelligent Study Assistant)** is a small but complete **intelligent system** designed using the **PRAL architecture** (Perceive → Reason → Act → Learn).
The goal of the system is to assist a student in **deciding what to study, how long to study, and when to study**, using a combination of:

* **Rule-based reasoning (Prolog)**
* **Machine Learning (scikit-learn)**
* **Deep Learning (PyTorch)**
* **Explainable logging and metrics**

The project is intentionally kept **simple, modular, and fully software-based**, focusing on **correct application of ISD concepts** rather than scale or complexity.

---

## 2. Problem Statement

Students often struggle to prioritize subjects and allocate study time based on multiple factors such as deadlines, difficulty, and past performance.
ISA-Lite models this as an **intelligent decision-making problem**, where the system:

* Perceives study data
* Reasons about priorities
* Acts by generating a daily schedule
* Learns from feedback and performance metrics

---

## 3. System Architecture (PRAL)

### PRAL Loop

```
Perceive → Reason → Act → Learn
     ↑_______________________↓
            (Logging)
```

Each stage produces a **concrete artifact** (facts, decisions, schedules, metrics), ensuring traceability and explainability.

---

## 4. Directory Structure (Explained)

```
isa-lite/
│
├── app/                      # Core PRAL pipeline
│   ├── app_front.py          # Streamlit UI (main entry point)
│   ├── perceive.py           # Perceive layer (CSV → facts)
│   ├── run_planner.py        # Reason layer (calls Prolog)
│   ├── schedule_apply.py     # Act layer (creates daily plan)
│   ├── learn_weekly.py       # Learn layer (metrics & feedback)
│   └── plan.json             # Reason output (generated)
│
├── engines/                  # Knowledge & reasoning engine
│   ├── planner_rules.pl      # Prolog rules (expert system)
│   └── facts.pl              # Generated facts (from Perceive)
│
├── data/                     # Environment data (inputs/outputs)
│   ├── events.csv            # Study activity history
│   ├── deadlines.csv         # Exams/quizzes with difficulty
│   └── todays_plan.csv       # Generated daily schedule
│
├── ml/                       # Machine Learning module
│   └── ml_adherence.py       # Predicts task completion (ML)
│
├── dl/                       # Deep Learning module
│   └── dl_minutes_predictor.py  # Predicts study minutes (DL)
│
├── report/                   # Evaluation & learning outputs
│   └── weekly_metrics.json   # Performance & adherence metrics
│
├── config.yaml               # Configuration (e.g., Prolog path)
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 5. PRAL Components (Explicit)

### 5.1 Perceive — Input Processing

**File:** `app/perceive.py`

* Reads `events.csv` and `deadlines.csv`
* Validates and cleans data
* Converts data into symbolic **Prolog facts**
* Writes facts to `engines/facts.pl`

**Output:** Structured world representation
**Metric Logged:** Input completeness (%)

---

### 5.2 Reason — Decision Logic

**Files:**

* `app/run_planner.py`

* `engines/planner_rules.pl`

* Uses **rule-based reasoning (Prolog)**

* Applies explicit IF–THEN rules:

  * Deadline proximity
  * Subject difficulty
  * Past completion

* Outputs decisions:

  * `shortlist`
  * `reject`
  * `needs_info`

* Allocates study minutes

**Output:** `app/plan.json`
**Metric Logged:** Reasoning latency (seconds)

---

### 5.3 Act — Execution Layer

**File:** `app/schedule_apply.py`

* Converts decisions into a **non-overlapping daily schedule**
* Assigns start/end times
* Writes `data/todays_plan.csv`

**Output:** Executable study plan
**Metric Logged:** Schedule generation success

---

### 5.4 Learn — Feedback & Metrics

**File:** `app/learn_weekly.py`

* Computes weekly metrics:

  * Task completion rate
  * Adherence
* Writes results to `report/weekly_metrics.json`

**Output:** Learning signals
**Metric Logged:** Completion %, adherence %

---

## 6. ML and DL Extensions (Hybrid Intelligence)

### 6.1 Machine Learning (ML)

**File:** `ml/ml_adherence.py`

* Supervised learning (Logistic Regression)
* Predicts whether a task will be completed
* Baseline comparison included
* Evaluation metrics:

  * Accuracy
  * Precision
  * Recall
  * F1-score

---

### 6.2 Deep Learning (DL)

**File:** `dl/dl_minutes_predictor.py`

* Small neural network (PyTorch MLP)
* Predicts required study minutes
* Uses embeddings for subjects
* Metric:

  * MAE (Mean Absolute Error)
* Baseline:

  * Mean minutes predictor

---

## 7. Logging Plan (ISD-Compliant)

**Events Logged:**

* Inputs (CSV rows)
* Intermediate decisions (Prolog output)
* Final actions (schedule)
* Errors and timeouts

**Log Schema:**

* Timestamp
* Module name
* Subject
* Decision
* Minutes
* Latency

**Storage:**

* Local JSON files (`report/`)
* Console logs (Streamlit panel)

**Privacy:**

* No personal identifiers
* Only academic task data

---

## 8. How to Run the Project

```bash
cd isa-lite
python -m venv .venv
# activate venv
pip install -r requirements.txt
python -m streamlit run app/app_front.py
```

---

## 9. Why This Project Is Sufficient for Assignment-2

* ✔ Part-1: **Rule-based system (Prolog)**
* ✔ Part-2: **Machine Learning model**
* ✔ Part-3: **Deep Learning model**
* ✔ Unified problem across all parts
* ✔ Clear metrics, baselines, and robustness
* ✔ Fully aligned with ISD lectures and PRAL methodology

---

## 10. Key Learning Outcomes

* Designed a complete intelligent system
* Applied PRAL rigorously
* Compared symbolic vs data-driven intelligence
* Built explainable, testable, and modular AI software

---

If you want, I can also:

* Add **architecture diagrams** (L0/L1) to the README
* Simplify wording further for submission
* Create a **one-page executive summary** for your instructor
