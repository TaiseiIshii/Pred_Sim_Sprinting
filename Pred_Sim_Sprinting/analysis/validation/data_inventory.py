"""
data_inventory.py -- summarize the source-.mat inventory for docs/DATA_AVAILABILITY.md.

Reads Results/Validation_Master/manifest_provenance.csv (per source MAT) and prints a per-experiment
markdown table (rows, strict, meshes, total size on disk if the MATs are present locally). Also
writes Results/Validation_Master/data_inventory.csv.

Run: & "C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\python.exe" analysis/validation/data_inventory.py
"""
from __future__ import annotations

import collections
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RESULTS = os.path.join(REPO, "Results")
MP = os.path.join(RESULTS, "Validation_Master", "manifest_provenance.csv")


def main():
    rows = list(csv.DictReader(open(MP, encoding="utf-8")))
    agg = collections.OrderedDict()
    for r in rows:
        e = r["experiment"]
        a = agg.setdefault(e, {"n": 0, "strict": 0, "mesh": set(), "bytes": 0, "sim": set()})
        a["n"] += 1
        a["strict"] += (r["strict"] == "True")
        a["mesh"].add(r["mesh_N"])
        a["sim"].add(r.get("simulation_commit", "?"))
        p = os.path.join(RESULTS, r["source_file"])
        if os.path.isfile(p):
            a["bytes"] += os.path.getsize(p)

    out = os.path.join(RESULTS, "Validation_Master", "data_inventory.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["experiment", "n_mats", "n_strict", "meshes", "sim_commits", "total_MB_if_local"])
        print(f"| experiment | n | strict | meshes | sim_commit | size (MB) |")
        print(f"|---|---|---|---|---|---|")
        tot = 0
        for e, a in agg.items():
            mb = a["bytes"] / 1e6
            tot += a["bytes"]
            meshes = "|".join(sorted(a["mesh"]))
            sims = "|".join(sorted(a["sim"]))
            w.writerow([e, a["n"], a["strict"], meshes, sims, f"{mb:.1f}"])
            print(f"| {e} | {a['n']} | {a['strict']} | {meshes} | {sims} | {mb:.1f} |")
        print(f"\nTOTAL local MAT size: {tot/1e6:.1f} MB across {sum(a['n'] for a in agg.values())} files")
        print(f"wrote {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    main()
