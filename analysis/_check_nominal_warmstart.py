"""One-off checker: does a strict N=50 Nominal warm-start source exist?"""
import glob
import os

from scipy.io import loadmat

RES = os.path.join(os.path.dirname(__file__), "..", "Results")


def _get(o, *names):
    for n in names:
        try:
            o = getattr(o, n)
        except AttributeError:
            o = o[n]
    return o


for f in sorted(glob.glob(os.path.join(RES, "pred_sprinting_data_*Nominal.mat"))):
    try:
        m = loadmat(f, struct_as_record=False, squeeze_me=True)
        o = m["optimumOutput"]
        N = int(_get(o, "options", "N"))
        status = str(_get(o, "stats", "return_status"))
        has_lx = hasattr(o, "lam_x_opt") or ("lam_x_opt" in getattr(o, "_fieldnames", []))
        has_lg = hasattr(o, "lam_g_opt") or ("lam_g_opt" in getattr(o, "_fieldnames", []))
        spd = float(_get(o, "ave_speed"))
        print(f"N={N:4d} | status={status:24s} | lam_x={has_lx} lam_g={has_lg} | "
              f"speed={spd:5.2f} | {os.path.basename(f)}")
    except Exception as e:  # noqa: BLE001
        print(f"[skip] {os.path.basename(f)}: {e}")
