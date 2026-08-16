"""
add_provenance.py -- Phase 1.1 provenance completion (NON-DESTRUCTIVE).

Reads the historical Results/Validation_Master/manifest.csv (generated 2026-08-15T15:55 while
repo HEAD was 3da75fc, using analysis scripts that were only *committed* at bb0433a) and writes:

  * manifest_provenance.csv  -- superset with explicit simulation / analysis / documentation
                               commits per source MAT (does NOT overwrite manifest.csv).
  * output_hashes.csv        -- SHA256 of every Validation_Master output file (CSV + PNG) so a
                               third party can verify each output's byte-identity.

Commit model (verified by `git diff`, see docs/PROVENANCE.md):
  * numerical simulation path (main_pred_sim_sprinting.m standard-condition code + ExternalFunctions
    + MuscleModel + Polynomials + CollocationScheme) is byte-identical 59877aa..bb0433a.
  * ham-load penalty (wJ(13)/paretoStudy) and run_ham_pareto_sweep.m first appear at 59877aa.
  * the combined pelvic-shift x virtual-athlete path (_athSh/_athWk) is new between 59877aa..bb0433a.
  * all analysis/validation/* scripts + Validation_Master outputs are first committed at bb0433a.

Run (base conda python):
  & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" analysis/validation/add_provenance.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUTDIR = os.path.join(REPO, "Results", "Validation_Master")
MANIFEST = os.path.join(OUTDIR, "manifest.csv")

# Verified commit attribution (short SHAs; see docs/PROVENANCE.md for the git-diff evidence).
SIM_PENALTY = "59877aa"   # first commit containing wJ(13)/paretoStudy + run_ham_pareto_sweep.m
SIM_COMBINED = "bb0433a"  # combined _athSh/_athWk path added between 59877aa..bb0433a
ANALYSIS_COMMIT = "bb0433a"  # analysis/validation/* first committed here (byte-identical to 15:55 run)


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    try:
        return subprocess.check_output(["git", "-C", REPO, *args], text=True).strip()
    except Exception:
        return "unknown"


def sim_commit(row):
    """Attribute the simulation commit for one source MAT (see PROVENANCE.md rules)."""
    cond = row.get("condition", "")
    obj = row.get("objective", "")
    if "_athSh" in cond or "_athWk" in cond:
        return SIM_COMBINED
    if obj.startswith("load_penalty") or row.get("experiment") == "HamPareto":
        return SIM_PENALTY  # penalty path; numerically identical 59877aa..bb0433a
    # baseline max-performance framework: numerically identical 59877aa..bb0433a
    return SIM_PENALTY


def main():
    head = git("rev-parse", "--short", "HEAD")
    dirty = git("status", "--porcelain")
    doc_commit = head + ("+uncommitted-2026-08-15" if dirty else "")

    with open(MANIFEST, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())

    # rename the ambiguous historical 'commit' -> 'repo_head_at_runtime'; add explicit commits.
    new_fields = []
    for c in fields:
        new_fields.append("repo_head_at_runtime" if c == "commit" else c)
    insert_at = new_fields.index("source_sha256")
    for i, col in enumerate(("simulation_commit", "analysis_commit", "documentation_commit")):
        new_fields.insert(insert_at + i, col)

    out_rows = []
    for r in rows:
        nr = {("repo_head_at_runtime" if k == "commit" else k): v for k, v in r.items()}
        nr["simulation_commit"] = sim_commit(r)
        nr["analysis_commit"] = ANALYSIS_COMMIT
        nr["documentation_commit"] = doc_commit
        out_rows.append(nr)

    prov = os.path.join(OUTDIR, "manifest_provenance.csv")
    with open(prov, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=new_fields)
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {os.path.relpath(prov, REPO)}  ({len(out_rows)} rows, "
          f"doc_commit={doc_commit})")

    # hash every output artifact in Validation_Master (CSV + PNG), excluding the two we generate.
    skip = {"manifest_provenance.csv", "output_hashes.csv"}
    arts = []
    for name in sorted(os.listdir(OUTDIR)):
        p = os.path.join(OUTDIR, name)
        if not os.path.isfile(p) or name in skip:
            continue
        arts.append({"file": name, "bytes": os.path.getsize(p), "sha256": sha256(p),
                     "analysis_commit": ANALYSIS_COMMIT})
    oh = os.path.join(OUTDIR, "output_hashes.csv")
    with open(oh, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "bytes", "sha256", "analysis_commit"])
        w.writeheader()
        w.writerows(arts)
    print(f"wrote {os.path.relpath(oh, REPO)}  ({len(arts)} artifacts hashed)")


if __name__ == "__main__":
    main()
