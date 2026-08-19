"""
audit_pareto.py -- INDEPENDENT Phase-6 audit of the N=100 speed-load Pareto checkpoint.

Reads Results/HamPareto_N100/checkpoint.csv, verifies (a) job/tag uniqueness, (b) out_file
existence + SHA256, (c) warm-start provenance (init_method/ws_file) and that the three w=0.1
solves are 3 DETERMINISTIC continuation paths (forward / from-Nominal / backward) rather than
"independent random restarts", then RE-COMPUTES speed and the biarticular terminal-swing peak
lMtilde surrogate straight from each raw out_file (clean-room engine from audit_recalc_N100),
and compares the w=0.1 3-path mean dSpeed / dSurrogate to the expected -0.340% / -5.189%.

Writes Results/Independent_Audit_20260819/pareto_checkpoint_audit.csv.
"""
from __future__ import annotations
import csv
import os
import numpy as np
import audit_recalc_N100 as A   # my own clean-room engine

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, ".."))
CKPT = os.path.join(RESULTS, "HamPareto_N100", "checkpoint.csv")
BIARTIC = ["semimem", "semiten", "bifemlh"]


def ts_surrogate(d, contact):
    return float(np.mean([A.metrics(d, nm, contact)["TS_peak_lMtilde"] for nm in BIARTIC]))


def main():
    rows = list(csv.DictReader(open(CKPT, encoding="utf-8")))
    print(f"checkpoint rows: {len(rows)}")
    tags = [r["tag"] for r in rows]
    outs = [r["out_file"] for r in rows]
    print(f"unique tags: {len(set(tags))}/{len(tags)}  unique out_files: {len(set(outs))}/{len(outs)}")
    dup_tag = [t for t in set(tags) if tags.count(t) > 1]
    dup_out = [o for o in set(outs) if outs.count(o) > 1]
    print(f"duplicate tags: {dup_tag or 'NONE'}   duplicate out_files: {dup_out or 'NONE'}")

    recs = []
    for r in rows:
        p = os.path.join(RESULTS, r["out_file"])
        exists = os.path.isfile(p)
        rec = dict(tag=r["tag"], condition=r["condition"], init_method=r["init_method"],
                   ws_file=r["ws_file"], out_file=r["out_file"],
                   ckpt_status=r["solver_status"], ckpt_speed=float(r["speed_mps"]),
                   ckpt_tilt=float(r["td_tilt_deg"]), iters=int(r["iters"]),
                   out_exists=exists)
        if exists:
            d = A.load(p)
            c, _, _ = A.contact_s(d)
            rec["recomputed_status"] = d["status"]
            rec["recomputed_speed"] = round(d["speed"], 6)
            rec["recomputed_tilt"] = round(d["td"], 4)
            rec["recomputed_inf_pr"] = d["inf_pr"]
            rec["sha256_16"] = A.sha256(p)[:16]
            rec["weight"] = float(r["condition"].split("_w")[-1]) / 1000.0
            rec["surrogate_TSpeaklM"] = round(ts_surrogate(d, c), 5)
            rec["status_match"] = (d["status"] == r["solver_status"])
            rec["speed_match_ckpt"] = abs(d["speed"] - float(r["speed_mps"])) < 1e-3
        recs.append(rec)

    base = next(x for x in recs if x.get("weight") == 0.0)
    for x in recs:
        if "recomputed_speed" in x:
            x["dSpeed_pct"] = round(100.0 * (x["recomputed_speed"] - base["recomputed_speed"]) / base["recomputed_speed"], 4)
            x["dSurro_pct"] = round(100.0 * (x["surrogate_TSpeaklM"] - base["surrogate_TSpeaklM"]) / base["surrogate_TSpeaklM"], 4)

    out = os.path.join(HERE, "pareto_checkpoint_audit.csv")
    cols = ["tag", "condition", "weight", "init_method", "ws_file", "out_file", "sha256_16",
            "ckpt_status", "recomputed_status", "status_match", "ckpt_speed", "recomputed_speed",
            "speed_match_ckpt", "recomputed_inf_pr", "ckpt_tilt", "recomputed_tilt",
            "surrogate_TSpeaklM", "dSpeed_pct", "dSurro_pct", "iters", "out_exists"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for x in sorted(recs, key=lambda z: (z.get("weight", 0), z["tag"])):
            w.writerow({c: x.get(c, "") for c in cols})

    # w=0.1 three-path reproducibility
    cand = [x for x in recs if x.get("weight") == 0.10]
    print(f"\n=== w=0.1 multi-path ({len(cand)} paths) ===  base(w0)=Nominal speed={base['recomputed_speed']} surro={base['surrogate_TSpeaklM']}")
    for x in sorted(cand, key=lambda z: z["tag"]):
        print(f"  {x['tag']:8s} init={x['init_method']:26s} speed={x['recomputed_speed']:.5f} "
              f"({x['dSpeed_pct']:+.3f}%) surro={x['surrogate_TSpeaklM']:.4f} ({x['dSurro_pct']:+.3f}%) "
              f"status={x['recomputed_status']}")
    dsp = np.array([x["dSpeed_pct"] for x in cand]); dsu = np.array([x["dSurro_pct"] for x in cand])
    sp = np.array([x["recomputed_speed"] for x in cand]); su = np.array([x["surrogate_TSpeaklM"] for x in cand])
    print(f"  MEAN dSpeed={dsp.mean():+.4f}% (exp -0.340)  MEAN dSurro={dsu.mean():+.4f}% (exp -5.189)")
    print(f"  spread: speed {100*(sp.max()-sp.min())/sp.mean():.3f}%  surrogate {100*(su.max()-su.min())/su.mean():.3f}%")
    print("\n  warm-start provenance (independence check):")
    for x in sorted(cand, key=lambda z: z["tag"]):
        print(f"    {x['tag']}: init={x['init_method']} ws_file={x['ws_file'] or '(continuation-in-memory)'}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
