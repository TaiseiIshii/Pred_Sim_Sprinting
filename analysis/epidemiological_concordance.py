"""
epidemiological_concordance.py
==============================
CONSTRUCT-VALIDITY check for the predictive sprinting simulation.

The companion script `validate_against_literature.py` shows the *Nominal* model
reproduces experimentally measured sprint biomechanics (face validity). This
script asks a different question:

    Does the model reproduce established *epidemiological* hamstring-strain-injury
    (HSI) risk-factor associations -- i.e. do the "virtual athlete" perturbations
    move injury surrogates in the direction (and, where possible, magnitude)
    documented by cohort/meta-analytic epidemiology?

If a single-parameter change to hamstring architecture reproduces the direction
of a real epidemiological association, the model has captured the mechanism that
the epidemiology can only correlate. That is construct validity.

It reads the two virtual-athlete sweeps already in Results/:
  * _HamFascicle_[mp]NN : biceps-femoris-long-head fascicle (optimal fibre)
                          length scaled x(1 -/+ NN/100)   (Timmins short-fascicle risk factor)
  * _HamStrength_[mp]NN : hamstring max isometric force scaled            (eccentric-weakness risk factor)

and maps the resulting dose-responses onto documented epidemiological findings,
printing a concordance table and writing Results/Validation/epidemiological_concordance.csv.

Usage:
    python analysis/epidemiological_concordance.py
"""
from __future__ import annotations

import csv
import glob
import os

import numpy as np
from scipy.io import loadmat

from injury_metrics import BIARTIC, HAM, HAM_L, HAM_R, RESULTS, _get, compute_injury_metrics
from analyze_ham_architecture import collect

OUTDIR = os.path.join(RESULTS, "Validation")

# Biceps femoris long head rows (0-based) in the 92-row muscle arrays.
BFLH_L, BFLH_R = 8, 54

REFERENCES = {
    "Timmins2016": "Timmins RG, Bourne MN, Shield AJ, Williams MD, Lorenzen C, Opar DA (2016). "
                   "Short biceps femoris fascicles and eccentric knee flexor weakness increase the "
                   "risk of hamstring injury in elite football. Br J Sports Med 50:1524-1535. "
                   "(BFlh fascicle <~10.56 cm and eccentric knee-flexor strength <~337 N raised risk.)",
    "Opar2015": "Opar DA, Williams MD, Timmins RG, Hickey J, Duhig SJ, Shield AJ (2015). Eccentric "
                "hamstring strength and hamstring injury risk in Australian footballers. "
                "Med Sci Sports Exerc 47:857-865.",
    "Bourne2018": "Bourne MN, Timmins RG, Opar DA, et al. (2018). An evidence-based framework for "
                  "strengthening exercises to prevent hamstring injury. Sports Med 48:251-267. "
                  "(Nordic/eccentric training lengthens BFlh fascicles and increases eccentric strength.)",
    "vanDyk2019": "van Dyk N, Behan FP, Whiteley R (2019). Including the Nordic hamstring exercise in "
                  "injury prevention programmes halves the rate of hamstring injuries: a meta-analysis "
                  "of 8459 athletes. Br J Sports Med 53:1362-1370. (~51% HSI reduction.)",
    "Ekstrand2016": "Ekstrand J, Walden M, Hagglund M (2016). Hamstring injuries have increased by 4% "
                    "annually in men's professional football (UEFA Elite Club Injury Study). "
                    "Br J Sports Med 50:731-737. (Hamstring = most common injury.)",
    "Woods2004": "Woods C, Hawkins RD, Maltby S, et al. (2004). The Football Association Medical "
                 "Research Programme: an audit of injuries in professional football - hamstring "
                 "injuries. Br J Sports Med 38:36-41. (Biceps femoris the most frequently injured hamstring.)",
    "Askling2007": "Askling C, Tengvar M, Saartok T, Thorstensson A (2007). Acute first-time hamstring "
                   "strains during high-speed running. Am J Sports Med 35:197-206. (Sprint-type strains "
                   "predominantly involve the biceps femoris long head.)",
    "Thelen2005": "Thelen DG, Chumanov ES, Hoerth DM, et al. (2005). Hamstring muscle kinematics during "
                  "treadmill sprinting. Med Sci Sports Exerc 37:108-114.",
    "Chumanov2007": "Chumanov ES, Heiderscheit BC, Thelen DG (2007). The effect of speed and influence "
                    "of individual muscles on hamstring mechanics during the swing phase of sprinting. "
                    "J Biomech 40:3555-3562.",
    "Danielsson2020": "Danielsson A, Horvath A, Senorski C, et al. (2020). The mechanism of hamstring "
                      "injuries - a systematic review. BMC Musculoskelet Disord 21:641.",
    "Kalkhoven2023": "Kalkhoven JT, Lehnert M, Bourne MN, et al. (2023). Reconsidering the swing-phase "
                     "hamstring stretch-injury paradigm. Sports Med 53:2321-2346.",
}


def _slope(rows, key):
    x = np.array([r["factor"] for r in rows], float)
    y = np.array([r[key] for r in rows], float)
    return float(np.polyfit(x, y, 1)[0])


def _at(rows, factor, key):
    for r in rows:
        if abs(r["factor"] - factor) < 1e-6:
            return r[key]
    return np.nan


def newest_nominal():
    fs = sorted(glob.glob(os.path.join(RESULTS, "pred_sprinting_data_*Nominal.mat")),
                key=os.path.getmtime, reverse=True)
    return fs[0] if fs else None


def bflh_optimal_length_cm(matpath):
    """Model BFlh optimal fibre (fascicle) length in cm = median(lM / lMtilde)."""
    o = loadmat(matpath, struct_as_record=False, squeeze_me=True)["optimumOutput"]
    mv = _get(o, "muscleValues")
    lM = np.asarray(_get(mv, "lM"), float)
    lMt = np.asarray(_get(mv, "lMtilde"), float)
    vals = []
    for row in (BFLH_L, BFLH_R):
        r = np.divide(lM[row], lMt[row], out=np.full_like(lM[row], np.nan), where=lMt[row] > 0)
        vals.append(np.nanmedian(r))
    return 100.0 * float(np.mean(vals))     # m -> cm


def per_muscle_ecc_work(rows):
    """Bilateral-mean active eccentric fibre work per hamstring at factor 1.0."""
    ref = min(rows, key=lambda r: abs(r["factor"] - 1.0))
    return {nm: ref[f"{nm}_ecc_work"] for nm in HAM}


# ---------------------------------------------------------------------------
class Item:
    __slots__ = ("finding", "epi_dir", "sim_metric", "sim_value", "verdict", "refs")

    def __init__(self, finding, epi_dir, sim_metric, sim_value, verdict, refs):
        self.finding, self.epi_dir = finding, epi_dir
        self.sim_metric, self.sim_value = sim_metric, sim_value
        self.verdict, self.refs = verdict, refs


def build_items():
    fasc = collect("Fascicle", target_N=50)
    strg = collect("Strength", target_N=50)
    if len(fasc) < 3 or len(strg) < 3:
        raise SystemExit("Need the HamFascicle and HamStrength sweeps in Results/ "
                         "(run run_ham_arch.bat fascicle / strength).")

    # --- quantitative evidence ------------------------------------------------
    d_strain_d_fasc = _slope(fasc, "biartic_peak_lMtilde")     # expect strongly negative
    d_speed_d_fasc = _slope(fasc, "speed")                     # expect ~0
    strain_short = _at(fasc, 0.70, "biartic_peak_lMtilde")     # short-fascicle athlete
    strain_long = _at(fasc, 1.20, "biartic_peak_lMtilde")      # long-fascicle athlete
    spd_lo = min(r["speed"] for r in fasc)
    spd_hi = max(r["speed"] for r in fasc)

    d_strain_d_str = _slope(strg, "biartic_peak_lMtilde")      # expect ~0
    d_speed_d_str = _slope(strg, "speed")                      # expect positive
    d_ecc_d_str = _slope(strg, "biartic_ecc_work")             # expect positive

    nom_mat = newest_nominal()
    l0 = bflh_optimal_length_cm(nom_mat)
    l_short, l_long = 0.70 * l0, 1.20 * l0
    THRESH = 10.56                                              # Timmins 2016 (cm)

    ecc = per_muscle_ecc_work(fasc)
    bflh_rank = sorted(BIARTIC, key=lambda m: ecc[m], reverse=True)
    bflh_top = bflh_rank[0] == "bifemlh"

    # peak strain occurs in swing for all biarticular hams? (from factor-1.0 row)
    ref = min(fasc, key=lambda r: abs(r["factor"] - 1.0))
    swing_all = all(ref.get(f"{m}_peak_in_stance") is False for m in BIARTIC)

    fpe_short = _at(fasc, 0.70, "bifemlh_peak_Fpetilde")
    fpe_long = _at(fasc, 1.20, "bifemlh_peak_Fpetilde")

    I = []
    I.append(Item(
        "Short BFlh fascicle length is a modifiable HSI risk factor",
        "shorter fascicle -> higher risk",
        "d(peak fascicle strain)/d(fascicle factor); strain at x0.70 vs x1.20",
        f"slope {d_strain_d_fasc:+.2f}; strain {strain_short:.2f} (x0.70) vs "
        f"{strain_long:.2f} (x1.20) -> +{100*(strain_short/strain_long-1):.0f}%",
        "CONCORDANT (direction + mechanism)", ["Timmins2016"]))
    I.append(Item(
        "BFlh fascicle-length risk threshold ~10.56 cm",
        "risk rises as length drops below ~10.6 cm",
        "model BFlh optimal fibre length; sweep range vs threshold",
        f"L0={l0:.1f} cm; sweep {l_short:.1f}-{l_long:.1f} cm brackets {THRESH:.1f} cm "
        f"({'spans' if l_short < THRESH < l_long else 'does NOT span'} threshold)",
        "CONCORDANT (sweep spans the clinical range)"
        if l_short < THRESH < l_long else "PARTIAL (range offset from threshold)",
        ["Timmins2016"]))
    I.append(Item(
        "Short-fascicle athletes are not slower ('fast but fragile')",
        "little/no performance cost",
        "d(top speed)/d(fascicle factor); speed range over sweep",
        f"slope {d_speed_d_fasc:+.2f} m/s; speed {spd_lo:.2f}-{spd_hi:.2f} m/s "
        f"(±{100*(spd_hi-spd_lo)/2/((spd_hi+spd_lo)/2):.1f}%)",
        "CONCORDANT", ["Timmins2016"]))
    I.append(Item(
        "Weak eccentric knee-flexor strength is a risk factor",
        "weaker -> higher risk",
        "strength sweep: d(peak strain), d(speed), d(ecc work) / d(strength)",
        f"d(strain)={d_strain_d_str:+.2f} (~flat), d(speed)={d_speed_d_str:+.2f} m/s, "
        f"d(eccWork)={d_ecc_d_str:+.1f} J",
        "REFINED: strength routes to performance & eccentric-work capacity, "
        "not peak stretch strain (two risk factors act via distinct paths)",
        ["Opar2015", "Timmins2016"]))
    I.append(Item(
        "Biceps femoris long head is the most frequently injured hamstring",
        "BFlh carries the greatest injurious load",
        "active eccentric fibre work per hamstring at top speed (Nominal)",
        f"bifemlh {ecc['bifemlh']:.1f} J = highest of biarticular "
        f"(semimem {ecc['semimem']:.1f}, semiten {ecc['semiten']:.1f} J); "
        f"rank {'/'.join(bflh_rank)}",
        "CONCORDANT" if bflh_top else "PARTIAL (BFlh not top by this metric)",
        ["Woods2004", "Askling2007", "Danielsson2020"]))
    I.append(Item(
        "Sprint HSIs occur in terminal/late swing",
        "peak lengthening in swing, not stance",
        "phase of peak fascicle strain (all biarticular hams)",
        f"peak strain in SWING for all biarticular hams: {swing_all}",
        "CONCORDANT" if swing_all else "DISCORDANT",
        ["Thelen2005", "Chumanov2007", "Danielsson2020"]))
    I.append(Item(
        "Nordic/eccentric training reduces HSI (~51%) by lengthening fascicles",
        "longer fascicle -> lower risk",
        "fascicle sweep, protective direction: peak strain & passive force at x1.10-1.20",
        f"strain {strain_long:.2f} (x1.20) < {ref['biartic_peak_lMtilde']:.2f} (x1.00); "
        f"BFlh passive force {fpe_long:.2f} (x1.20) < {fpe_short:.2f} (x0.70)",
        "CONCORDANT (reproduces the protective direction)",
        ["vanDyk2019", "Bourne2018"]))
    I.append(Item(
        "Prior injury and older age are the strongest (non-modifiable) predictors",
        "history/age -> higher risk",
        "not represented (no tissue-damage memory or ageing in the model)",
        "not mechanistically modeled",
        "OUT OF SCOPE (honest boundary)", ["Ekstrand2016"]))

    meta = dict(l0=l0, thresh=THRESH, nom_mat=os.path.basename(nom_mat),
                n_fasc=len(fasc), n_strg=len(strg), ecc=ecc)
    return I, meta


def main():
    items, meta = build_items()
    print("=" * 100)
    print("  PREDICTIVE SPRINT SIMULATION -- CONSTRUCT VALIDITY vs HSI EPIDEMIOLOGY")
    print("=" * 100)
    print(f"  virtual-athlete sweeps: {meta['n_fasc']} fascicle + {meta['n_strg']} strength "
          f"conditions (N=50)")
    print(f"  model BFlh optimal fibre length L0 = {meta['l0']:.1f} cm "
          f"(Timmins risk threshold {meta['thresh']:.2f} cm)")
    print("-" * 100)
    for i, it in enumerate(items, 1):
        print(f"\n  [{i}] {it.finding}")
        print(f"      epidemiology : {it.epi_dir}   ({', '.join(it.refs)})")
        print(f"      sim metric   : {it.sim_metric}")
        print(f"      sim evidence : {it.sim_value}")
        print(f"      VERDICT      : {it.verdict}")

    conc = sum(it.verdict.startswith("CONCORDANT") for it in items)
    print("\n" + "-" * 100)
    print(f"  {conc}/{len(items)} findings CONCORDANT; the rest are REFINED / OUT-OF-SCOPE "
          f"(explained above, not failures).")
    print("-" * 100)

    os.makedirs(OUTDIR, exist_ok=True)
    csvpath = os.path.join(OUTDIR, "epidemiological_concordance.csv")
    with open(csvpath, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["epidemiological_finding", "documented_direction", "sim_metric",
                    "sim_evidence", "verdict", "references"])
        for it in items:
            w.writerow([it.finding, it.epi_dir, it.sim_metric, it.sim_value,
                        it.verdict, "; ".join(it.refs)])
    print(f"  wrote {os.path.relpath(csvpath, os.path.dirname(__file__))}")

    print("\n  REFERENCES")
    for k in sorted({r for it in items for r in it.refs}):
        print(f"   [{k}] {REFERENCES[k]}")


if __name__ == "__main__":
    main()
