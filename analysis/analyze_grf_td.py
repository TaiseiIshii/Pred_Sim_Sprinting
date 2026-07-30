"""
analyze_grf_td.py
v3 (TDPT) 各接地骨盤前傾条件の「地面反力 (GRF)」の用量反応を解析する。

最適化結果 .mat の optimumOutput.GRFs.R（右足＝接地脚の合計GRF, 3成分 [前後, 鉛直,
左右]）を timeNodes とともに読み、接地骨盤前傾角に対して次の指標を算出する:

  peakVert   : 鉛直GRFピーク            (BW)   ← 荷重の大きさ
  peakBrake  : 制動(後向き)水平GRFピーク (BW)   ← ブレーキ
  peakProp   : 推進(前向き)水平GRFピーク (BW)
  contact_ms : 接地時間                 (ms)
  vertImp    : 鉛直力積                 (BW·s)
  brakeImp   : 制動力積 / propImp: 推進力積 (BW·s)
  loadRate   : 平均鉛直荷重速度 = peakVert/接地〜ピーク時間 (BW/s)

出力 (Results/PelvicTD_Study/):
  grf_td_summary.csv
  td_fig5_grf_doseresponse.png   (2x2: 波形 / 鉛直ピーク / 制動・推進 / 接地時間・力積)

Run: python analysis/analyze_grf_td.py       (N=50)
     python analysis/analyze_grf_td.py 100   (N=100)
"""
from __future__ import annotations

import csv
import glob
import os
import sys

import numpy as np
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Results")
STUDY = os.path.join(RESULTS, "PelvicTD_Study")

BODY_MASS = 72.17            # kg (subject)
BW = BODY_MASS * 9.80665     # N (body weight)

TARGET_N = 50
SUFFIX = ""

# (offset_deg, tag, prefix); most-anterior half uses the bound-relaxed runs
CONDITIONS = [(-8, "m8", "PelvisTDwide"), (-6, "m6", "PelvisTDwide"),
              (-4, "m4", "PelvisTDwide"), (-2, "m2", "PelvisTDwide"),
              (0, "p0", "PelvisTDwide"),
              (2, "p2", "PelvisTD"), (4, "p4", "PelvisTD"), (6, "p6", "PelvisTD")]

# representative conditions for the waveform overlay (anterior / nominal / neutral)
REP = {"m8": ("#2166ac", "強い前傾 −15.5°"),
       "p0": ("#4d4d4d", "基準 −7.5°"),
       "p6": ("#b2182b", "中立寄り −1.5°")}


def setup_jp_font():
    for c in ("Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"):
        if c in {f.name for f in font_manager.fontManager.ttflist}:
            matplotlib.rcParams["font.family"] = c
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def _get(o, *names):
    for n in names:
        o = getattr(o, n) if hasattr(o, n) else o[n]
    return o


def _mat_N(path):
    try:
        m = loadmat(path, struct_as_record=False, squeeze_me=True,
                    variable_names=["optimumOutput"])
        return int(np.asarray(_get(m["optimumOutput"], "options", "N")).ravel()[0])
    except Exception:
        return None


def latest(tag, prefix):
    fs = sorted(glob.glob(os.path.join(RESULTS,
                f"pred_sprinting_data_*{prefix}_{tag}.mat")),
                key=os.path.getmtime, reverse=True)
    for p in fs:
        if _mat_N(p) == TARGET_N:
            return p
    return None


def load_grf(off, tag, prefix):
    p = latest(tag, prefix)
    if not p:
        return None
    o = loadmat(p, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    q = np.asarray(_get(o, "optVars_nsc", "q"), dtype=float)
    td_tilt = float(np.degrees(q[0, 0]))
    GR = np.asarray(_get(o, "GRFs", "R"), dtype=float)      # (nT, 3) [AP, vert, ML]
    t = np.asarray(_get(o, "timeNodes"), dtype=float).ravel()
    if t.size != GR.shape[0]:                               # fallback: uniform
        t = np.linspace(0.0, 1.0, GR.shape[0])
    fx, fy = GR[:, 0], GR[:, 1]                             # AP, vertical (N)
    thr = 0.05 * BW
    stance = fy > thr
    if stance.sum() < 3:
        return None
    ts, fys, fxs = t[stance], fy[stance], fx[stance]
    peakVert = fy.max() / BW
    t_peak = t[int(np.argmax(fy))] - ts[0]                  # touchdown -> vertical peak
    load_rate = peakVert / t_peak if t_peak > 1e-6 else np.nan
    peakBrake = -fx.min() / BW if fx.min() < 0 else 0.0     # braking magnitude
    peakProp = fx.max() / BW if fx.max() > 0 else 0.0
    contact_ms = (ts[-1] - ts[0]) * 1000.0
    vertImp = np.trapz(fys, ts) / BW
    brakeImp = -np.trapz(np.minimum(fxs, 0.0), ts) / BW     # magnitude
    propImp = np.trapz(np.maximum(fxs, 0.0), ts) / BW
    try:
        speed = float(np.asarray(_get(o, "ave_speed")).ravel()[0])
    except Exception:
        speed = np.nan
    # stance-normalised waveforms (0..100%)
    ph = (ts - ts[0]) / (ts[-1] - ts[0]) * 100.0
    grid = np.linspace(0, 100, 101)
    return {
        "offset": off, "tag": tag, "td_tilt": td_tilt, "anterior": -td_tilt,
        "peakVert": peakVert, "peakBrake": peakBrake, "peakProp": peakProp,
        "contact_ms": contact_ms, "vertImp": vertImp, "brakeImp": brakeImp,
        "propImp": propImp, "loadRate": load_rate, "speed": speed,
        "wf_vert": np.interp(grid, ph, fys / BW),
        "wf_ap": np.interp(grid, ph, fxs / BW),
    }


def _slope(rows, key):
    x = np.array([r["anterior"] for r in rows])
    y = np.array([r[key] for r in rows])
    return np.polyfit(x, y, 1)[0]


def main():
    global TARGET_N, SUFFIX
    if len(sys.argv) > 1:
        TARGET_N = int(sys.argv[1])
    SUFFIX = "" if TARGET_N == 50 else f"_N{TARGET_N}"
    setup_jp_font()
    rows = [r for off, tag, pre in CONDITIONS if (r := load_grf(off, tag, pre))]
    if len(rows) < 2:
        raise SystemExit("need >=2 conditions with GRF")
    ant = np.array([r["anterior"] for r in rows])

    # ---- CSV ----
    cols = ["offset", "tag", "td_tilt", "anterior", "speed", "peakVert",
            "peakBrake", "peakProp", "contact_ms", "vertImp", "brakeImp",
            "propImp", "loadRate"]
    with open(os.path.join(STUDY, f"grf_td_summary{SUFFIX}.csv"), "w",
              newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(r[k], 4) if isinstance(r[k], float) else r[k])
                        for k in cols})
    print(f"wrote grf_td_summary{SUFFIX}.csv")

    # ---- slopes (per deg anterior tilt) ----
    print("\n--- GRF slopes (per deg anterior touchdown tilt) ---")
    for k in ("peakVert", "peakBrake", "peakProp", "contact_ms", "brakeImp",
              "propImp", "loadRate"):
        print(f"  {k:11s}: {_slope(rows, k):+.5f}   "
              f"(range {min(r[k] for r in rows):.3f}..{max(r[k] for r in rows):.3f})")

    # ---- figure: 2x2 ----
    fig, ax = plt.subplots(2, 2, figsize=(12.5, 9.0))
    grid = np.linspace(0, 100, 101)

    # (a) waveform overlay (representative conditions)
    a = ax[0, 0]
    for r in rows:
        if r["tag"] in REP:
            c, lab = REP[r["tag"]]
            a.plot(grid, r["wf_vert"], color=c, lw=2.0, label=f"{lab} 鉛直")
            a.plot(grid, r["wf_ap"], color=c, lw=1.3, ls="--")
    a.axhline(0, color="0.6", lw=0.8)
    a.set_title("GRF波形（実線=鉛直, 破線=前後）: 前傾で形は変わるか", fontsize=11)
    a.set_xlabel("接地相 (%)")
    a.set_ylabel("GRF (体重比 BW)")
    a.grid(True, alpha=0.3)
    a.legend(fontsize=8, loc="upper right")

    # (b) peak vertical vs tilt
    b = ax[0, 1]
    b.plot(ant, [r["peakVert"] for r in rows], "-o", color="#2ca02c", lw=1.8)
    b.set_title(f"鉛直GRFピーク（傾き {_slope(rows,'peakVert'):+.3f} BW/°）", fontsize=11)
    b.set_xlabel("接地前傾角（度, 右ほど強い前傾）")
    b.set_ylabel("peak 鉛直GRF (BW)")
    b.grid(True, alpha=0.3)

    # (c) braking & propulsive peaks vs tilt
    c = ax[1, 0]
    c.plot(ant, [r["peakBrake"] for r in rows], "-o", color="#d62728",
           label="制動ピーク")
    c.plot(ant, [r["peakProp"] for r in rows], "-s", color="#1f77b4",
           label="推進ピーク")
    c.set_title("水平GRF: 制動 vs 推進", fontsize=11)
    c.set_xlabel("接地前傾角（度, 右ほど強い前傾）")
    c.set_ylabel("peak 水平GRF (BW)")
    c.grid(True, alpha=0.3)
    c.legend(fontsize=9)

    # (d) contact time & braking impulse vs tilt
    d = ax[1, 1]
    d.plot(ant, [r["contact_ms"] for r in rows], "-o", color="#7e3f9e",
           label="接地時間 (ms)")
    d.set_xlabel("接地前傾角（度, 右ほど強い前傾）")
    d.set_ylabel("接地時間 (ms)", color="#7e3f9e")
    d.tick_params(axis="y", labelcolor="#7e3f9e")
    d.grid(True, alpha=0.3)
    d2 = d.twinx()
    d2.plot(ant, [r["brakeImp"] for r in rows], "-^", color="#e8a200",
            label="制動力積 (BW·s)")
    d2.set_ylabel("制動力積 (BW·s)", color="#e8a200")
    d2.tick_params(axis="y", labelcolor="#e8a200")
    d.set_title("接地時間 と 制動力積", fontsize=11)

    fig.suptitle(f"v3(TDPT) 接地骨盤前傾 → 地面反力(GRF)の用量反応  (N={TARGET_N})",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = os.path.join(STUDY, f"td_fig5_grf_doseresponse{SUFFIX}.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", os.path.basename(out))

    # ---- console table ----
    print("\n TDtilt  ant  speed peakV peakBrake peakProp contact vImp bImp pImp")
    for r in rows:
        print(f"{r['td_tilt']:6.2f} {r['anterior']:5.2f} {r['speed']:5.2f} "
              f"{r['peakVert']:5.2f} {r['peakBrake']:8.2f} {r['peakProp']:7.2f} "
              f"{r['contact_ms']:6.1f} {r['vertImp']:5.3f} {r['brakeImp']:5.3f} "
              f"{r['propImp']:5.3f}")


if __name__ == "__main__":
    main()
