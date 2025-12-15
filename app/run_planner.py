# app/run_planner.py  — Reason Layer (Prolog) runner for ISA-Lite
# Runs SWI-Prolog with planner_rules.pl + facts.pl and writes app/plan.json

from __future__ import annotations
import subprocess
import json
import time
import os
from pathlib import Path

# Optional dependency: PyYAML (you already installed it)
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
ENGINES = ROOT / "engines"
APP = ROOT / "app"
CONFIG = ROOT / "config.yaml"

RULES_PL = ENGINES / "planner_rules.pl"
FACTS_PL = ENGINES / "facts.pl"
OUT_JSON = APP / "plan.json"


# ---------- Config helpers ----------
def load_config() -> dict:
    if not CONFIG.exists():
        return {}
    if yaml is None:
        # If yaml isn't installed, fallback to empty config
        return {}
    try:
        cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def swipl_path(cfg: dict) -> str:
    """
    Return SWI-Prolog executable path.
    Priority: config.yaml -> environment variable SWIPL -> default 'swipl'
    """
    if "swipl_path" in cfg and str(cfg["swipl_path"]).strip():
        return str(cfg["swipl_path"]).strip()
    if os.environ.get("SWIPL"):
        return os.environ["SWIPL"]
    return "swipl"


# ---------- Prolog runner ----------
def build_cmd(swipl: str) -> list[str]:
    """
    Use:
      -q           quiet
      -f none      ignore init files (stability)
      -s file      consult files
      -g goal      run goal
      -t halt      terminate always
    """
    return [
        swipl,
        "-q",
        "-f", "none",
        "-s", str(RULES_PL),
        "-s", str(FACTS_PL),
        "-g", "main",
        "-t", "halt",
    ]


def pretty_file_head(path: Path, max_lines: int = 60) -> str:
    if not path.exists():
        return f"[debug] Missing file: {path}"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    head = "\n".join(lines[:max_lines])
    tail_note = "" if len(lines) <= max_lines else f"\n... ({len(lines)-max_lines} more lines)"
    return f"[debug] {path} (first {min(max_lines,len(lines))} lines)\n{head}{tail_note}"


def run_prolog(timeout_s: int = 30) -> tuple[str, float]:
    cfg = load_config()
    swipl = swipl_path(cfg)
    cmd = build_cmd(swipl)

    # Sanity checks
    if not RULES_PL.exists():
        raise SystemExit(f"[reason] Missing rules file: {RULES_PL}")
    if not FACTS_PL.exists():
        raise SystemExit(
            f"[reason] Missing facts file: {FACTS_PL}\n"
            "Run Perceive first (python app/perceive.py) to generate facts.pl."
        )

    t0 = time.time()
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except FileNotFoundError:
        raise SystemExit(
            f"[reason] SWI-Prolog not found: '{swipl}'.\n"
            "Fix options:\n"
            "  (1) Add SWI-Prolog bin to PATH so 'swipl' works\n"
            "  (2) Set config.yaml:\n"
            '      swipl_path: "C:/Program Files/swipl/bin/swipl.exe"\n'
            "  (3) Or set env var SWIPL to the full path."
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(
            f"[reason] Prolog timed out (hung >{timeout_s}s).\n"
            "Likely reasons:\n"
            "  - planner_rules.pl threw an error and Prolog is stuck\n"
            "  - main/0 does not terminate or calls a predicate that loops\n"
            "Fix:\n"
            "  - Ensure main/0 prints the plan and ends\n"
            "  - Ensure comparisons use numbers (no uninstantiated vars)\n"
        )

    latency = time.time() - t0
    stdout = (p.stdout or "").strip()
    stderr = (p.stderr or "").strip()

    if p.returncode != 0:
        debug = "\n\n".join([
            "[reason] Prolog failed.",
            "CMD: " + " ".join(cmd),
            "STDOUT:\n" + stdout,
            "STDERR:\n" + stderr,
            pretty_file_head(FACTS_PL, 80),     # show facts for diagnosis
            pretty_file_head(RULES_PL, 80),     # show rules for diagnosis
        ])
        raise SystemExit(debug)

    # Even if returncode==0, empty output is suspicious
    if not stdout:
        raise SystemExit(
            "[reason] Prolog succeeded but printed no output.\n"
            "Your main/0 must print a list like:\n"
            "  [[math,shortlist,120],[physics,needs_info,60]]\n"
            "Fix planner_rules.pl: ensure main :- plan(P), writeln(P).\n"
        )

    return stdout, latency


# ---------- Output parsing ----------
def parse_plan(text: str) -> list[dict]:
    """
    Expected Prolog output format:
      [[math,shortlist,120],[physics,needs_info,60]]
    We'll parse a *simple* bracket list safely.
    """
    # Normalize whitespace
    raw = text.strip()

    # Option 1: Prolog prints JSON already (future-proof)
    if raw.startswith("{") or raw.startswith("[{"):
        try:
            obj = json.loads(raw)
            # Accept either {"plan":[...]} or direct list
            if isinstance(obj, dict) and "plan" in obj:
                return obj["plan"]
            if isinstance(obj, list):
                return obj
        except Exception:
            pass

    # Option 2: Prolog list like [[a,b,1],[c,d,2]]
    # We'll do a lightweight parse instead of ast.literal_eval hacks.
    # Strategy: split on "],[" boundaries and parse tokens.
    if not (raw.startswith("[[") and raw.endswith("]]")):
        raise SystemExit(
            f"[reason] Unexpected Prolog output format:\n{raw}\n"
            "Expected something like: [[math,shortlist,120],[physics,needs_info,60]]"
        )

    inner = raw[2:-2]  # remove outer [[ and ]]
    items = inner.split("],[") if inner else []
    plan = []
    for it in items:
        parts = [p.strip() for p in it.split(",")]
        if len(parts) != 3:
            raise SystemExit(f"[reason] Bad item in Prolog output: [{it}]")
        subject, decision, minutes = parts
        # remove quotes if any
        subject = subject.strip("'\"")
        decision = decision.strip("'\"")
        try:
            minutes_i = int(float(minutes))
        except Exception:
            minutes_i = 0
        plan.append({"subject": subject, "decision": decision, "minutes": minutes_i})
    return plan


def main():
    out, latency = run_prolog(timeout_s=30)
    plan = parse_plan(out)

    OUT_JSON.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print("[reason] wrote app/plan.json")
    print(json.dumps({"latency_s": round(latency, 3), "plan": plan}, indent=2))


if __name__ == "__main__":
    main()
