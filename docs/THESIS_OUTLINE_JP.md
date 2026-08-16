# 修士論文 章構成（THESIS OUTLINE, JP）

対象命題: **同程度のスプリント性能下で骨盤姿勢を操作したとき、境界条件と全身協調の変化がハム
ストリングの力学的負荷代理指標をどう変えるかを筋駆動予測シミュレーションで検証し、性能低下を
抑えつつ負荷代理指標を下げる候補動作を探索する。** 評価対象は受傷確率ではなく
**injury-related mechanical-load surrogates**。数値の一次ソースは
[PAPER_RESULTS_FREEZE.md](PAPER_RESULTS_FREEZE.md)、主張の言い回しは
[CLAIM_CALIBRATION.md](CLAIM_CALIBRATION.md) に準拠。

各章に「図/表・主張・CSV・コード」を対応づける。

## 第1章 序論 ― ハムストリング肉離れとスプリント負荷
- 内容: HSI の疫学的重要性、疾走型受傷が遊脚後期に多いこと、力学的負荷を「筋線維レベル」で
  見る必要性。**本研究は受傷確率でなく負荷代理指標を扱う**と明示。
- 図/表: 図1（研究定式化・反実仮想の概念図）。
- 主張: 問題設定（scope）。 コード/CSV: なし（レビュー）。

## 第2章 先行研究と研究ギャップ
- 内容: Schache 2012 / Chumanov 2007 / Thelen 2005（遊脚後期の伸張性ピーク）、Kalkhoven 2023
  （fiber vs MTU）、Mendiguchia 2024（局所組織伸張）、Timmins 2016 / Opar 2022（形態・筋力）、
  Haralabidis（接地キネマティクスと最高速度）、Lin & Pandy 2022。**定義レベルの相違**（fiber/MTU/
  regional、force/work の定義、正規化）を [LITERATURE_QUANTITATIVE_COMPARISON.md] に基づき整理。
- 図/表: 表2-1（先行研究の定義・速度・局面・数値レンジ・本研究との整合/不整合）。
- 主張: 研究ギャップ = grid/単位整合の負荷評価 + 境界条件を分けた分解 + near-matched-speed Pareto。
- CSV/コード: `docs/LITERATURE_QUANTITATIVE_COMPARISON.md`。

## 第3章 筋駆動予測シミュレーション（方法・基盤）
- 内容: OpenSim 筋骨格モデル（国際級スプリンター、対称1ステップ）、直接コロケーション
  (CasADi/IPOPT)、接触モデル、目的関数（速度最大化＋正則化）、strict 収束基準
  (`Solve_Succeeded`)。Nominal が原著 11.85 m/s を再現。
- 図/表: 表3-1（モデル/ソルバ設定、mesh N=50/100）。
- 主張: 基盤モデルの妥当性（face validity）。 コード: `MainFunctions/main_pred_sim_sprinting.m`。
  CSV: `manifest_provenance.csv`。

## 第4章 筋線維負荷指標の定義と妥当性（監査と修正）
- 内容: Step-0 監査（非一様 Radau `timeNodes`、力は N、`vMtilde>0`=伸張、負の仕事は J）。
  reference-limb full-stride 再構成、terminal-swing/early-stance 窓。**単位・符号・積分の修正**。
- 図/表: 表4-1（指標定義・単位・正規化）、図4（旧 eccWork との差＝バグ影響）。
- 主張: 指標エンジンの正しさ。 コード: `analysis/validation/ham_load_metrics.py`、
  `test_unit_metrics.py`(22/22)、`test_ham_load_metrics.py`(18/18)。 CSV/doc: `METRIC_DEFINITIONS.md`。

## 第5章 骨盤8条件の用量反応（PRIMARY）
- 内容: strict TDPT 8条件（N=50/100、speed 11.72–11.80）。筋別に active/passive/tendon/work を
  分離。二関節ハムの terminal-swing peak `lMtilde` が前傾で robust ↑（semimem+9.3%/semiten+4.6%/
  bifemlh+7.0%、mesh<1.6%）、単関節 bifemsh は不変。passive force・負の仕事は方向 robust だが
  **magnitude mesh-conditional**。
- 図/表: 図2 / 図A1–A4、表5-1（筋別判定）。
- 主張: FREEZE 2A/2B（支持＋条件付き）。 CSV: `eight_condition_metrics_N50/N100.csv`,
  `phaseA_{long,doseresponse,mesh_sensitivity,verdicts}.csv`。 コード: `phaseA_muscle_tension.py`,
  `analyze_eight_conditions.py`。 結論文: [PER_MUSCLE_CONCLUSIONS.md]。

## 第6章 境界条件と全身協調の分解（PRIMARY）
- 内容: tree-rigid / femur-fixed の**幾何学的反実仮想**と adaptive 再最適化解の区別。tree-rigid
  ΔMTU=0（大腿が骨盤と共回転）、femur-fixed +21.6/+26.9/+24.7 mm/25°、adaptive は femur-fixed 幾何で
  **~85–90%** 説明、残りは協調項。前傾は主に股関節屈曲（≈−1.07 deg/deg）で実現。
- 図/表: 図3、表6-1（3条件の属性: 同速度/位相/動力学的可否/平衡/GRF）。
- 主張: FREEZE 2C。**凍結条件は runnable motion ではない**。 CSV: `boundary_condition_static.csv`,
  `boundary_condition_motion.csv`, `fair_opt_comparison_N100.csv`。 doc: [OPT_ON_OFF_INTERPRETATION.md]。

## 第7章 速度–負荷Paretoと候補動作（PRIMARY, N=100確認）
- 内容: 二関節ハム過伸張ペナルティ wJ(13) を掃引。near-matched-speed 候補 w=0.1
  （speed −0.24%, surrogate −4.14%、N=50）。**N=100・multi-start（前方/後方/nominal 起点）で再現性を
  検証**（実行中；`run_ham_pareto_N100.m`）。合否は Phase-2.4 ゲート。候補動作 vs baseline の運動学・
  筋力学差（機序＝速度低下だけでは説明されない）。
- 図/表: 図4（N=100 Pareto）、図5（baseline vs 候補の運動学・筋負荷差）、表7-1（各解の
  achieved speed/tilt/surrogate/solver/init/mesh）。
- 主張: FREEZE 2D（N=100完了後に Supported/Conditional/Rejected 確定）。 CSV: `pareto_nominal.csv`
  (+`HamPareto_N100/checkpoint.csv`)。 コード: `pareto_and_robustness.py`, `run_ham_pareto_N100.m`。

## 第8章 形態差の探索的解析（EXPLORATORY）
- 内容: 筋束長（−0.0139/%）・筋力（+0.0009/%）の主効果は概ね直交。**morphology×pelvis は交絡**の
  ため探索的。個別化介入は主要結論にしない。
- 図/表: 図M1、表8-1。 主張: FREEZE 3（探索的）。 CSV: `morphology_*.csv`, `pareto_morphology.csv`。

## 第9章 総合考察
- 内容: 前傾→股屈曲→二関節ハム線維長↑→（筋別に）passive/active/work の変化、という連鎖。疫学的
  関連との**方向整合**（因果再現ではない）。fiber vs MTU / regional、`lMo` vs 超音波の**構成概念差**。
- 図/表: 図9（機序連鎖図）。 主張: 支持/条件付き/未検証の分離。 doc: `CLAIM_EVIDENCE_MATRIX.md`,
  `Epidemiological_Concordance_Report.md`(較正済)。

## 第10章 限界と人を対象とした検証計画
- 内容: 実受傷アウトカム無し、決定論的単一解、接触モデルによる GRF ピーク過大、mesh 感度
  （passive/work）、単一被験者モデル。**人を対象とした介入検証計画**（観察可能キネマティクス仮説の
  前向き検証）。 図/表: 表10-1（限界→対応）。

## 第11章 結論
- near-matched-speed 下で骨盤前傾が二関節ハムの terminal-swing 線維長を robust に増やすこと、境界
  条件で分解できること、性能維持で負荷代理指標を下げる候補動作を生成できること（N=100確認）。
  **受傷予防の実証ではない**。

## 付録
- A: provenance（`PROVENANCE.md`, `manifest_provenance.csv`, `output_hashes.csv`）
- B: data availability（`DATA_AVAILABILITY.md`）
- C: 再現コマンド（`README` + 各 runner）、テスト（unit/integration）
- D: 図・CSV・コード対応表（`PAPER_RESULTS_FREEZE.md` §6）
