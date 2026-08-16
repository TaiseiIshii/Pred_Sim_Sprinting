# 学会抄録ドラフト（ABSTRACTS）

数値は [PAPER_RESULTS_FREEZE.md](PAPER_RESULTS_FREEZE.md) の確定値のみ。評価対象は
**力学的負荷代理指標**であり受傷確率ではない（[CLAIM_CALIBRATION.md](CLAIM_CALIBRATION.md) 準拠）。
Pareto 候補 w=0.1 は **N=100・multi-start（3/3 初期値）で確認済**（Phase-2.4 全ゲート合格 → Supported）。

- **英語タイトル**: Boundary-Condition-Aware Predictive Sprint Optimization for Hamstring Load
  Reduction at Near-Matched Performance
- **日本語タイトル**: 境界条件を考慮した予測スプリント最適化による性能維持下のハムストリング
  負荷低減動作探索

---

## 1. 日本語抄録（約600字）

**目的**　ハムストリング肉離れは疾走型で遊脚後期に多いが、骨盤姿勢の操作が筋線維レベルの力学的
負荷をどう変えるかは切り分けが難しい。本研究は、同程度のスプリント性能下で接地時の骨盤前傾角を
操作し、境界条件と全身協調の変化がハムストリングの力学的負荷代理指標（正規化筋線維長、能動・
受動・腱張力、負の筋線維仕事）をどう変えるかを筋駆動予測シミュレーションで検証し、性能低下を
抑えつつ負荷代理指標を下げる候補動作を探索することを目的とした。

**方法**　OpenSim 筋骨格モデルと直接コロケーション最適化（CasADi/IPOPT）で、strict 収束した接地
骨盤前傾8条件（速度11.72–11.80 m/s、N=50・N=100）を解析した。指標は非一様時間格子上で物理単位に
より再計算し、terminal swing と early stance を分離した。

**結果**　より前傾した接地骨盤では、二関節ハム（半膜様筋・半腱様筋・大腿二頭筋長頭）の遊脚後期
ピーク筋線維長が頑健に増加し（半膜様筋 +9.3%、mesh 差<1.6%）、単関節の大腿二頭筋短頭は不変で
あった。この効果は主に股関節屈曲の増加（≈−1.07 deg/deg）で実現され、大腿固定の幾何反実仮想が
約85–90%を説明した。受動張力と負の仕事は方向は頑健だが絶対値は mesh 依存であった。過伸張ペナルティ
掃引では、速度−0.34%で代理指標−5.2%の near-matched-speed 候補が得られ、N=100・multi-start（3/3 初期値）で確認された。

**結論**　本モデルにおいて骨盤前傾は二関節ハムの筋線維負荷代理指標を筋別・局面別に変化させ、
性能維持下の負荷低減候補動作を生成しうる。これは受傷予防の実証ではなく、実験的介入仮説である。

---

## 2. 日本語抄録（約1000字）

**背景と目的**　ハムストリング肉離れ（HSI）は疾走型スポーツで最多の外傷の一つで、疾走型受傷は
遊脚後期に集中する。しかし、骨盤前傾のような姿勢操作が筋線維レベルの力学的負荷に与える影響は、
形態・協調・境界条件が交絡するため切り分けが難しい。本研究は、(1) grid・単位整合の筋線維負荷
評価、(2) 境界条件を分けた骨盤↔負荷の分解、(3) near-matched-speed の速度–負荷 Pareto 候補、の三点を
目的とし、評価対象を受傷確率ではなく **injury-related mechanical-load surrogates**（正規化筋線維長
lMtilde、能動・受動・腱張力、筋線維伸張速度、負の筋線維仕事、および terminal swing / early stance の
各ピーク）とした。

**方法**　国際級スプリンターの OpenSim 筋骨格モデルと直接コロケーション（CasADi/IPOPT、対称1
ステップ）を用い、接地骨盤前傾を8条件（要求 −8…+6°）操作した。strict 収束（Solve_Succeeded）した
条件のみを主解析とし（達成速度11.72–11.80 m/s、差≤0.51%）、N=50 と N=100 の両 mesh で評価した。
負荷指標は保存された非一様 Radau 時間格子上で物理単位により再計算し（負の仕事は J）、reference-limb
の全ストライドを再構成して terminal swing と early stance を分離した。骨盤操作の力学的由来は、
tree-rigid・femur-fixed の幾何反実仮想と adaptive 再最適化解に分解した。

**結果**　より前傾した接地骨盤では、二関節ハム（半膜様筋・半腱様筋・大腿二頭筋長頭）の遊脚後期
ピーク正規化筋線維長が頑健に増加し（半膜様筋 0.97→1.07、+9.3%；半腱様筋 +4.6%；長頭 +7.0%、
R²=0.95–0.96、N50–N100 差<1.6%）、単関節の短頭は不変（span 0.4%）で、効果は股関節をまたぐ筋に
特異的であった。ピークは遊脚後期（ストライドの88–91%）に生じた。受動張力と terminal-swing の負の
仕事は方向は頑健に増加したが、絶対値は mesh 依存であった（最大 ~10–33%）。能動・腱張力は筋別で、
半膜様筋は増加、半腱様筋の能動張力はわずかに減少した。骨盤前傾は主に股関節屈曲の増加で実現され
（≈−1.07 deg/deg）、femur-fixed 幾何が adaptive の遊脚後期 MTU 伸張の約85–90%を説明した。二関節ハム
過伸張ペナルティの掃引では、速度損失−0.24%で代理指標−4.1%の near-matched-speed 候補（w=0.1）が
得られ、非劣解であった（速度−０．３４％、代理指標−５．２％；Ｎ＝１００・multi-startで 3/3 初期値が同一解に収束）。

**結論**　本モデル・速度・最適化条件下で、骨盤前傾は二関節ハムの筋線維負荷代理指標を筋別・局面別
に変化させ、境界条件で分解できること、また性能維持下で負荷代理指標を下げる候補動作を生成しうる
ことを示した。これは受傷確率や予防の実証ではなく、前向きに検証すべき実験的介入仮説を与える。

---

## 3. English abstract (~250 words)

**Boundary-Condition-Aware Predictive Sprint Optimization for Hamstring Load Reduction at
Near-Matched Performance**

**Purpose.** Hamstring strain injuries in sprinting cluster in terminal swing, but how pelvic
posture changes fiber-level mechanical load is confounded by morphology, coordination, and boundary
conditions. Using muscle-driven predictive simulation, we tested how manipulating touchdown pelvic
tilt at near-matched sprint performance alters hamstring **mechanical-load surrogates** (normalized
fiber length, active/passive/tendon force, fiber lengthening velocity, negative fiber work), and
sought candidate motions that lower these surrogates with minimal speed loss. The evaluated quantity
is a load surrogate, **not** injury probability.

**Methods.** An OpenSim model of an international-caliber sprinter was solved by direct collocation
(CasADi/IPOPT, symmetric step). A strict, speed-matched 8-condition touchdown-pelvic-tilt set
(11.72–11.80 m/s) was analyzed at N=50 and N=100; surrogates were recomputed in physical units on the
saved non-uniform grid, separating terminal swing and early stance.

**Results.** More anterior touchdown tilt robustly increased terminal-swing peak normalized fiber
length in all three biarticular hamstrings (semimembranosus +9.3%; mesh |Δ|<1.6%), with the
mono-articular biceps femoris short head unchanged — a hip-crossing-specific effect realized mainly by
added hip flexion (≈−1.07 deg/deg; a femur-fixed counterfactual explained ~85–90%). Passive force and
negative work rose in the same direction but with mesh-conditional magnitude. An overstretch-penalty
sweep yielded a near-matched-speed candidate confirmed at N=100 by multi-start (3/3 initializations;
−0.34% speed, −5.2% surrogate; all pre-declared gates).

**Conclusion.** Within this model, pelvic tilt reshapes hamstring fiber-load surrogates in a
muscle- and phase-specific way and can generate load-reduction candidate motions at maintained
performance — an experimental intervention hypothesis, not demonstrated injury prevention.
