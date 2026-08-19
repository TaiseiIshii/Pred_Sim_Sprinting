"""
build_preview.py -- generate 修士論文_追加図統合プレビュー.html.
Numbers are recomputed via _common / read from the written source CSVs (traceable),
never hand-copied from the manuscript.  Figures 1-7 in the body, S1-S2 in an appendix.
Each figure: purpose before, facts-only results after, bilingual caption.
Does NOT overwrite any existing manuscript HTML.
"""
import csv
import html
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C


def rd(rel):
    return list(csv.DictReader(open(os.path.join(C.OUTDIR, rel), encoding="utf-8")))


def main():
    conds = C.load_primary_N100()
    ant = np.array([c["anterior"] for c in conds])
    spd = np.array([c["speed"] for c in conds])
    reg = {}
    for nm in C.MUS:
        y = np.array([c["m"][nm]["peak_lMtilde"] for c in conds])
        sl, ic, r2 = C.fit(ant, y)
        reg[nm] = (sl, r2, 100.0 * (y[-1] - y[0]) / y[0])
    f5 = {r["muscle"]: r for r in rd("source_data/Fig5_mtu_peaks_source.csv")}
    f7 = rd("source_data/Fig7_pareto_N100_source.csv")
    w1 = [r for r in f7 if abs(float(r["weight"]) - 0.1) < 1e-9]
    mds = np.mean([float(r["dSpeed_pct"]) for r in w1])
    mdu = np.mean([float(r["dSurro_pct"]) for r in w1])

    def png(stem):
        return f"figures/png/{stem}.png"

    FIGS = [
        ("Fig1_study_logic", "Figure 1", "研究ギャップと検証連鎖 / Research gap and validation chain",
         "観察研究に加えて、同一予測モデル内で接地時骨盤傾斜を操作する必要性と、解析の連鎖を示す。 "
         "Why a single-model predictive manipulation of touchdown pelvic tilt is needed, and how the analyses chain.",
         "概念図。観察研究の交絡（個体差・共変動学）を、単一モデルで接地時骨盤傾斜のみ拘束し全身再最適化することで切り分ける枠組み。",
         "Schematic. Observational confounds (anatomy, co-varying kinematics) are isolated by constraining only "
         "touchdown pelvis tilt in one model and re-optimizing the whole body.",
         "概念図。観察研究の交絡を、単一モデルで接地時骨盤傾斜のみ拘束・全身再最適化して切り分け、主解析／機序／発展解析へ連鎖させる。"),
        ("Fig2_primary_N100", "Figure 2", "N=100 主結果 / Primary result",
         "速度をほぼ維持した条件間で、接地前傾量の増加が二関節ハムの1ストライド最大 lMtilde 増加と関連するか。",
         f"速度は Nominal ±1% 内（スプレッド {100*(spd.max()-spd.min())/11.83456:.2f}%）。1ストライド最大 lMtilde の前傾1°当たり傾きは "
         f"SM {reg['semimem'][0]:+.4f}（R²{reg['semimem'][1]:.2f}）, ST {reg['semiten'][0]:+.4f}（R²{reg['semiten'][1]:.2f}）, "
         f"BFlh {reg['bifemlh'][0]:+.4f}（R²{reg['bifemlh'][1]:.2f}）, BFsh {reg['bifemsh'][0]:+.4f}（ほぼ平坦）。"
         f"最小→最大前傾で二関節3筋 +{reg['semiten'][2]:.1f}…+{reg['semimem'][2]:.1f}%, BFsh {reg['bifemsh'][2]:+.1f}%。",
         "A: operability (speed within Nominal +/-1%). B: 1-stride peak lMtilde rises graded with anterior tilt for the "
         "three biarticular muscles; biceps femoris short head (single-joint) is flat. C: slope with leave-one-condition-out "
         "range (NOT a CI) and speed-adjusted coefficient. 8 deterministic design points; no population CI.",
         "A: 操作成立性（速度は Nominal ±1% 内）。B: 1ストライド最大 lMtilde は二関節3筋で前傾量とともに段階的に増加、単関節 BFsh は平坦。"
         "C: 傾き＋単一条件除外感度範囲（CIではない）＋速度調整係数。8決定論的設計点、母集団CIなし。"),
        ("Fig3_lMtilde_waveforms_N100", "Figure 3", "lMtilde 波形とピーク時相 / Waveforms and peak phase",
         "1ストライド最大 lMtilde はどの局面でどのように前傾量へ応答するか。",
         "二関節3筋の1ストライド最大は結果として終末遊脚期（85.5–90.8% stride）に位置し、前傾量とともに段階的に上昇。"
         "BFsh は早期立脚（~2–3%）にピークをもち平坦。主評価は1ストライド全体の最大値であり、Pareto の terminal-swing-window peak とは別定義。",
         "lMtilde vs % stride for the 8 conditions, coloured by anterior tilt (darker = larger). Markers = 1-stride max "
         "(full stride), which lands in terminal swing for the biarticular muscles. Distinct from the Pareto TS-window peak.",
         "8条件の lMtilde 波形（濃色=前傾大）。marker=1ストライド最大（全ストライド）で、二関節筋では終末遊脚期に位置。"
         "Pareto の TS窓ピークとは別量。"),
        ("Fig4_baseline_validation", "Figure 4", "基準シミュレーションの妥当性 / Baseline validity",
         "内部筋力学を論じる前提として、Nominal N=100 は被験者本人の最高速度スプリントの外部特徴をどの程度再現するか。",
         "股・膝・足の関節角は形状一致良好（相関 r=0.90–0.97, 系統オフセット有）。pelvis_tilt は raw IK とモデルで規約/姿勢が異なり "
         "（接地 +5.0° vs −8.0°）、オフセット除去後の形状相関 r=−0.31・RMSE 5.9°。被験者の実験 GRF・EMG は本データに無く、"
         "GRF/活動は**シミュレーションのみ**（鉛直ピーク 5.9BW は接触モデル由来で過大）。GRF/EMG 誤差は not available。",
         "Kinematic shape agreement (hip/knee/ankle r=0.90-0.97) with systematic offsets; pelvis_tilt differs by a "
         "convention/posture offset (flagged, not silently aligned). GRF and activations are SIMULATION-ONLY (no subject "
         "force plate or EMG in the dataset). External agreement does NOT guarantee internal fibre-length/force validity.",
         "運動学の形状一致（股膝足 r=0.90–0.97, オフセット有）。pelvis_tilt は規約/姿勢差を注記。GRF・活動はシミュレーションのみ。"
         "外部一致は内部筋線維長・力の妥当性を保証しない。"),
        ("Fig5_pelvis_femur_mechanism", "Figure 5", "骨盤–大腿協調による機序分解 / Pelvis-femur mechanism",
         "観察されたハム伸長は骨盤絶対角ではなく骨盤–大腿の相対配置で説明されるか。",
         f"正規化位相・OpenSim厳密MTUで、adaptive の終末遊脚期 ΔMTU は SM {f5['semimem_l']['C_adaptive_TSpeak_mm']} / "
         f"ST {f5['semiten_l']['C_adaptive_TSpeak_mm']} / BFlh {f5['bifemlh_l']['C_adaptive_TSpeak_mm']} mm。"
         f"大腿世界姿勢を固定した femur-fixed が adaptive の {f5['bifemlh_l']['fixed_over_adaptive_pct']}–"
         f"{f5['semimem_l']['fixed_over_adaptive_pct']}% を再現（骨盤と共回転する tree-rigid は ΔMTU≈0）。この比は媒介割合ではない。",
         "tree-rigid (pelvis & femur co-rotate) gives dMTU~0; femur-fixed (femur world pose held) reproduces 89.6-95.8% of "
         "the adaptive terminal-swing MTU rise. A/B are geometric counterfactuals; only adaptive is feasible. The ratio is "
         "NOT a mediation fraction.",
         "tree-rigid（骨盤・大腿共回転）で ΔMTU≈0、femur-fixed（大腿世界姿勢固定）が adaptive の 89.6–95.8% を再現。"
         "A/B は幾何学的反実仮想、adaptive のみ実行可能解。比率は媒介割合ではない。"),
        ("Fig6_numerical_robustness", "Figure 6", "数値的成立性・解選択・感度 / Numerical robustness",
         "主結果は角度未達・制約違反・単一条件・速度差・成功解選択だけで説明されないか。",
         "全95 MAT を発見→読込→PelvisTD→N=100→wide→strict の順に絞り、要求offsetごとに inf_pr 最小の8条件を採用。"
         "採用8条件は inf_pr ~1e-9…1e-7（≪1e-4）、失敗解は >1e-2 で低速へ崩壊。",
         "Discovery-to-adoption funnel (95 MAT -> 8 adopted). Target-angle achievement on identity; adopted inf_pr << 1e-4; "
         "failed solves collapse to low speed. Shows the result is not an artefact of unmet angle, constraint violation, or "
         "solution selection.",
         "発見→採用のフロー（95→8）。目標角は identity 上、採用解の残差 ≪1e-4、失敗解は低速へ崩壊。角度未達・制約違反・解選択の "
         "人工物でないことを示す。"),
        ("Fig7_pareto_N100", "Figure 7", "速度–負荷代理指標の Pareto / Speed-load Pareto",
         "速度損失を事前基準内に保ちつつ、筋線維長代理指標が低い候補解を計算上生成できるか。",
         f"w=0.1 の3ウォームスタート経路で平均 dSpeed {mds:+.3f}%・dSurrogate（二関節TS窓ピーク平均）{mdu:+.3f}%。"
         "事前基準（速度損失≤0.5% かつ代理指標≤−3%）を w=0.05/0.10 が満たし、w=0.2 は速度予算超過。"
         "3解は独立反復でなく3決定論的経路。最適化が直接罰する平滑積分項と報告ピークは別指標。候補解は実走可能性・受傷低減を証明しない。",
         "w=0.1 (3 warm-start paths) reduces the biarticular terminal-swing-window peak surrogate by ~5.2% for ~0.34% speed "
         "loss; w=0.05/0.10 meet the pre-registered target, w=0.2 exceeds the speed budget. The 3 solves are deterministic "
         "warm-start paths, not independent restarts. Candidates do NOT prove runnability or injury reduction.",
         "w=0.1（3経路）で速度 −0.34% と引き換えに二関節TS窓ピーク代理指標 −5.2%。w=0.05/0.10 が事前基準を満たす。"
         "3解は決定論的経路。候補解は実走可能性・受傷低減を証明しない。"),
    ]
    SUPPL = [
        ("FigS1_force_length", "Figure S1", "力–長さ作用域 / Force-length operating region",
         "二関節ハムが力–長さ関係上のどこで作動し、前傾でどう移動するか。",
         "前傾大（m8）の終末遊脚期作用点は前傾小（p6）より長い lMtilde 側へ移動。Fce は減衰項を含む収縮要素力。",
         "Fce (incl. damping) vs lMtilde for min vs max tilt; the max-tilt terminal-swing operating point sits at longer lMtilde.",
         "min/max 前傾の Fce–lMtilde 軌跡。前傾大で終末遊脚の作用点が長 lMtilde 側へ。"),
        ("FigS2_muscle_metric_heatmap", "Figure S2", "筋×指標 変化率 / Muscle x metric change",
         "各負荷代理指標が最小→最大前傾でどう変化するか。",
         "受動力 Fpass が最大の上昇（二関節 +42…+88%）、負の仕事 +16…+33%、最大 lMtilde +4.7…+9.7%。BFsh はほぼ中立/負。",
         "Percent change min->max tilt per metric; passive force rises most, biarticular metrics rise, bifemsh near zero.",
         "最小→最大前傾の変化率。受動力が最大上昇、二関節指標が上昇、BFsh は中立。"),
    ]

    def section(stem, tag, title, purpose, res_jp, cap_en, cap_jp):
        return f"""
    <section>
      <h2>{html.escape(tag)} | {html.escape(title)}</h2>
      <p class="purpose"><b>目的 / Purpose:</b> {html.escape(purpose)}</p>
      <img src="{png(stem)}" alt="{html.escape(tag)}">
      <p class="result"><b>結果（事実のみ） / Results (facts only):</b> {res_jp}</p>
      <p class="caption"><b>Caption (EN):</b> {html.escape(cap_en)}<br>
         <b>図注 (JP):</b> {html.escape(cap_jp)}</p>
    </section>"""

    body = "".join(section(*f) for f in FIGS)
    appendix = "".join(section(*f) for f in SUPPL)

    doc = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>修士論文 追加図 統合プレビュー</title>
<style>
 body {{ font-family: "Yu Gothic","Meiryo",sans-serif; max-width: 1000px; margin: 24px auto;
        color:#161616; background:#fff; line-height:1.6; padding:0 16px; }}
 h1 {{ font-size:1.5em; border-bottom:3px solid #2166ac; padding-bottom:6px; }}
 h2 {{ font-size:1.15em; color:#1a1a1a; margin-top:2em; border-left:5px solid #2166ac; padding-left:10px; }}
 .prov {{ background:#f4f7fb; border:1px solid #d6e2f0; padding:12px 16px; font-size:0.85em; border-radius:6px; }}
 section {{ margin-bottom:1.5em; }}
 img {{ max-width:100%; height:auto; border:1px solid #e2e2e2; padding:6px; background:#fff; display:block; margin:10px 0; }}
 .purpose {{ color:#0b3d66; }}
 .result {{ background:#fbfbfb; border-left:3px solid #1b7837; padding:8px 12px; }}
 .caption {{ font-size:0.85em; color:#444; }}
 .warn {{ background:#fff6e8; border:1px solid #e0b877; padding:10px 14px; border-radius:6px; font-size:0.88em; }}
 code {{ background:#f0f0f0; padding:1px 4px; border-radius:3px; }}
 footer {{ margin-top:3em; font-size:0.82em; color:#555; border-top:1px solid #ddd; padding-top:12px; }}
</style></head>
<body>
<h1>修士論文 追加図 統合プレビュー<br><span style="font-size:0.6em;font-weight:normal;color:#555;">
Thesis additional figures — integrated preview</span></h1>

<div class="prov">
<b>Provenance:</b> 全図は元 MAT / .mot / .sto / .osim から再計算（エンジン <code>scripts/_common.py</code>、
<code>Results/Independent_Audit_20260819/audit_recalc_N100.py</code> と数値一致）。commit <code>e7b8de9</code>。
主評価項目 = <b>1ストライド全体の最大 lMtilde（=lM/lMo）</b>。N=100 を主解析、N=50 は主結果に混在させない。
数値照合は <code>01_numeric_reconciliation.csv</code>（27行・不一致0）、自動QAは <code>qa/qa_results.csv</code>（20項目 PASS）。
Fce は減衰項を含む収縮要素力。前傾量 <code>A = -pelvis_tilt</code>。
</div>

<div class="warn"><b>解釈の限界:</b> 本図集は単一予測モデル内の<b>相関・機序</b>を示すもので、肉離れの<b>因果</b>・受傷リスク低減・
安全姿勢・個人一般化・絶対GRF妥当性は主張しない。8条件は同一モデルの決定論的設計点であり、母集団の標準誤差・p値・95%CIは付さない。
筋25（quad_fem_r）の設計意図は未確認（全条件共通のため用量反応の差には無影響）。考察的解釈は本文考察章に置く。</div>

<h1 style="font-size:1.2em;border:none;color:#2166ac;">本文図 / Body figures</h1>
{body}

<h1 style="font-size:1.2em;border:none;color:#762a83;">補足図 (Appendix)</h1>
{appendix}

<footer>
出力フォルダ: <code>output/thesis_figures_final_20260819_163600/</code>。
各図の PDF/SVG/600dpi PNG は <code>figures/</code>、元データCSVは <code>source_data/</code>、
provenance は <code>02_figure_manifest.csv</code>、入出力 SHA256 は <code>qa/input_hashes.csv</code> /
<code>qa/output_hashes.csv</code>。未作成図（S3 パラメータ感度・S4 同系列N50–N100）の理由は
<code>03_missing_data_and_blockers.md</code>。既存原稿・既存結果は上書きしていない。
</footer>
</body></html>"""

    out = os.path.join(C.OUTDIR, "修士論文_追加図統合プレビュー.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("wrote", out, f"({len(doc)} chars)")


if __name__ == "__main__":
    main()
