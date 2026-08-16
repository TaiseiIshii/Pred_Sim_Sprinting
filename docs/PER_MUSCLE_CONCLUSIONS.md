# Phase F — per-muscle conclusions (paper wording, with numbers)

Scope note (applies to every statement): *in this musculoskeletal model, at matched top speed
(11.72–11.80 m/s), under the stated optimization, across the strict 8-condition touchdown-pelvic-tilt
(TDPT) set at N=100 (N=50 sign-consistent).* Values are **mechanical-load surrogates**, not injury
outcomes. Source: `phaseA_verdicts.csv`, `phaseA_doseresponse.csv` (analysis_commit `bb0433a`).
Direction "↑ with anterior tilt" = higher at −16° touchdown tilt than at −2°.

## F1. Semimembranosus (biarticular)
More anterior touchdown pelvic tilt was associated with **robustly higher** terminal-swing peak
**normalized fiber length** (0.97→1.07, +9.3%; R²=0.96; mesh-robust, |N100−N50|=1.5%), **active
fiber force** (3099→3312 N, +6.6%; mesh 1.6%) and **tendon force** (3013→3253 N, +7.7%; mesh 1.7%).
**Passive fiber force** increased in the same direction (40→75 N) but its **magnitude is
mesh-conditional** (10.5%). **Negative active fiber work** increased in terminal swing (13.7→28.5 J)
but is **mesh-sensitive** (full-stride inconclusive, 21.7%). **Fiber lengthening velocity** was
approximately invariant/inconclusive full-stride. → *Semimembranosus is the muscle whose length,
active and tendon-force channels track anterior tilt most robustly.*

## F2. Semitendinosus (biarticular)
Anterior tilt was associated with **robustly higher** peak **normalized fiber length** (1.13→1.18,
+4.6%; mesh 0.8%) and **passive force** (36→51 N; mesh 6.3%), and higher terminal-swing negative
work (direction robust; **magnitude mesh-conditional**, 28.4%). In contrast, peak **active fiber
force slightly *decreased*** (816→790 N, −3.3%) and **tendon force was approximately invariant**
(1.9%). Fiber lengthening velocity was non-monotonic full-stride. → *Semitendinosus separates the
length/passive channel (up) from the active/tendon channel (flat-to-down) — a clear reason not to
lump "tension".*

## F3. Biceps femoris long head — BFlh (biarticular)
Anterior tilt was associated with **robustly higher** peak **normalized fiber length** (1.04→1.11,
+7.0%; mesh 1.3%) and **passive force** (43→71 N; mesh 9.3%), and higher terminal-swing negative
work (direction robust; **magnitude strongly mesh-conditional**, 33.4%). Peak **active force**
(0.9%) and **tendon force** (1.4%) were **approximately invariant**, and **fiber lengthening
velocity was non-monotonic** (ρ=−0.14). → *For BFlh the anterior-tilt effect is expressed as
fiber-length and passive-force increase, not active/tendon-force increase.*

## F4. Biceps femoris short head — BFsh (mono-articular control)
BFsh peak **normalized fiber length was approximately invariant** (0.945→0.942, span 0.4%) and its
active/passive/tendon force were invariant — **confirming the anterior-tilt effect is
hip-crossing-specific**. BFsh peaks in **early stance** (~2% of stride), a different mechanism; its
early-stance active/tendon force and (stance-phase) lengthening velocity did change with tilt, which
is a stance-mechanics effect, **not** the terminal-swing stretch that drives the biarticular result.

## F5. Cross-muscle synthesis (what may be claimed)
1. **Robust, mesh-insensitive (primary):** terminal-swing peak normalized fiber length rises with
   anterior touchdown tilt for **all three biarticular** hamstrings; the mono-articular control is
   flat → the effect is hip-crossing-specific and phase-specific (terminal swing).
2. **Direction robust, magnitude mesh-conditional (report direction):** passive fiber force and
   terminal-swing negative active work.
3. **Muscle-specific (must be stated per muscle):** active and tendon force (semimem ↑; semiten
   active ↓; BFlh flat) and fiber lengthening velocity (non-monotonic/invariant for biarticular).
4. **Not claimable:** any statement that "hamstring tension increases" as a lump; any injury-rate,
   injury-probability, or prevention claim; any equivalence of `lMtilde` with engineering strain or
   of `lMo` with ultrasound fascicle length.

These statements are the source text for the thesis Chapter 5/6 and the abstracts.
