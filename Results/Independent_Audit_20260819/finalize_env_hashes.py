"""
finalize_env_hashes.py -- writes environment_lock.txt and sha256_manifest.csv for the audit.
Read-only w.r.t. all source data. Run with base miniconda python.
"""
from __future__ import annotations
import csv, datetime as dt, glob, hashlib, os, platform, subprocess, sys
import numpy as np, scipy

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(RESULTS, ".."))


def sha256(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(buf), b""):
            h.update(c)
    return h.hexdigest()


def git(*a):
    try:
        return subprocess.check_output(["git", *a], cwd=REPO, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


# ---- adopted source artifacts (used in this audit) ----
PRIMARY = [
    "pred_sprinting_data_24-June-2026__23-17-49___PelvisTDwide_m8.mat",
    "pred_sprinting_data_25-June-2026__00-01-41___PelvisTDwide_m6.mat",
    "pred_sprinting_data_25-June-2026__01-05-16___PelvisTDwide_m4.mat",
    "pred_sprinting_data_25-June-2026__02-31-10___PelvisTDwide_m2.mat",
    "pred_sprinting_data_25-June-2026__03-15-59___PelvisTDwide_p0.mat",
    "pred_sprinting_data_25-June-2026__04-33-19___PelvisTDwide_p2.mat",
    "pred_sprinting_data_25-June-2026__05-43-11___PelvisTDwide_p4.mat",
    "pred_sprinting_data_25-June-2026__07-24-05___PelvisTDwide_p6.mat",
    "pred_sprinting_data_10-April-2026__16-29-40___Nominal.mat",
]
PARETO = [
    "pred_sprinting_data_15-August-2026__19-53-23___HamPareto_Nom_w0000.mat",
    "pred_sprinting_data_15-August-2026__21-57-37___HamPareto_Nom_w0050.mat",
    "pred_sprinting_data_15-August-2026__23-30-42___HamPareto_Nom_w0100.mat",
    "pred_sprinting_data_16-August-2026__02-26-49___HamPareto_Nom_w0200.mat",
    "pred_sprinting_data_16-August-2026__03-57-45___HamPareto_Nom_w0100.mat",
    "pred_sprinting_data_16-August-2026__05-49-46___HamPareto_Nom_w0200.mat",
    "pred_sprinting_data_16-August-2026__07-39-58___HamPareto_Nom_w0100.mat",
]
BOUNDARY = [
    "pred_sprinting_coords_10-April-2026__16-29-40___Nominal.mot",
    "pred_sprinting_coords_24-June-2026__23-17-49___PelvisTDwide_m8.mot",
]


def main():
    # environment_lock.txt
    env = os.path.join(HERE, "environment_lock.txt")
    with open(env, "w", encoding="utf-8") as f:
        f.write("INDEPENDENT REPRODUCIBILITY AUDIT -- ENVIRONMENT LOCK\n")
        f.write(f"generated_at: {dt.datetime.now().isoformat(timespec='seconds')}\n\n")
        f.write("[repository]\n")
        f.write(f"path: {REPO}\n")
        f.write(f"git_HEAD: {git('rev-parse', 'HEAD')}\n")
        f.write(f"git_branch: {git('rev-parse', '--abbrev-ref', 'HEAD')}\n")
        f.write(f"git_describe: {git('describe', '--always', '--dirty')}\n")
        dirty = git("status", "--porcelain=v1")
        f.write(f"git_dirty_files:\n{dirty if dirty else '  (clean)'}\n\n")
        f.write("[analysis environment -- this audit]\n")
        f.write(f"OS: {platform.platform()}\n")
        f.write(f"python: {platform.python_version()} ({sys.executable})\n")
        f.write(f"numpy: {np.__version__}\n")
        f.write(f"scipy: {scipy.__version__}\n")
        f.write("opensim (opencap env): 4.4-2022-08-12-dcf8e2cb1  "
                "(C:\\Users\\T11648sTb\\AppData\\Local\\miniconda3\\envs\\opencap\\python.exe)\n\n")
        f.write("[simulation environment -- as documented / inferred from artifacts]\n")
        f.write("MATLAB: R2017b (Japanese locale CP932; .m sources must be ASCII)  [documented]\n")
        f.write("NLP solver: IPOPT via CasADi nlpsol (stats.return_status/iterations.inf_pr saved).\n")
        f.write("  exact CasADi/IPOPT versions NOT recorded inside the .mat artifacts (unresolved).\n")
        f.write("muscle model: De Groote 2016 Hill-type; Fmax x2 (muscleFScale=2.0);\n")
        f.write("  vMax=12*lMo (vMaxMult=12; contPrms Sph_Plane_simultOptContPrms_Fmax_2_Vmax_12.mat);\n")
        f.write("  aTendon=35, passive FL e0=0.6/kpe=4, Fce damping d=0.01.\n")
        f.write("  quad_fem (muscle 25) optimal fibre length +10% (row 2; comment mislabels as TSL).\n\n")
        f.write("[subject / model]\n")
        f.write("OpenSim model: Scaled_FullBody_HamnerModel_Muscle_withContact.osim\n")
        f.write("total model mass: 72.1700 kg (verified by summing 20 body masses) == BODY_MASS 72.17\n")
        f.write("BW: 72.17*9.80665 = 707.75 N\n")
        f.write("mesh: N=50 -> q(37,200) muscle(92,151) 3N+1; N=100 -> q(37,400) muscle(92,301).\n")
    print("wrote", env)

    # sha256_manifest.csv
    def add(rows, relpath, role):
        p = os.path.join(RESULTS, relpath)
        if os.path.isfile(p):
            st = os.stat(p)
            rows.append(dict(role=role, file=relpath, sha256=sha256(p), size_bytes=st.st_size,
                             mtime=dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")))
        else:
            rows.append(dict(role=role, file=relpath, sha256="MISSING", size_bytes="", mtime=""))

    rows = []
    for fn in PRIMARY:
        add(rows, fn, "adopted_source_primary_N100" if "Nominal" not in fn else "adopted_source_nominal_N100")
    for fn in PARETO:
        add(rows, fn, "adopted_source_pareto_checkpoint")
    for fn in BOUNDARY:
        add(rows, fn, "adopted_source_boundary_mot")
    for p in sorted(glob.glob(os.path.join(HERE, "*.csv"))):
        st = os.stat(p)
        rows.append(dict(role="derived_audit_table", file=os.path.relpath(p, RESULTS),
                         sha256=sha256(p), size_bytes=st.st_size,
                         mtime=dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")))

    out = os.path.join(HERE, "sha256_manifest.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["role", "file", "sha256", "size_bytes", "mtime"])
        w.writeheader(); w.writerows(rows)
    print("wrote", out, f"({len(rows)} artifacts)")
    for r in rows:
        print(f"  {r['role']:34s} {str(r['sha256'])[:16]}  {r['file']}")


if __name__ == "__main__":
    main()
