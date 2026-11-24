# 03 欠損データと未達事項 / Missing data and blockers

出力: `output/thesis_figures_final_20260819_163600/`  ・ commit `e7b8de9` ・ 2026-08-19

本図タスクは当初**読み取り専用**（既存MATの再計算）で本文 Fig 1–7・補足 S1–S2 を作成した。その後、利用者の指示により**不足していた検証（MATLAB R2017b + CasADi の再solve）を実施**し、補足 S3・S4 を追加した。以下は現状と残る不足。

## A. 作成した図（本文 Fig 1–7・補足 S1–S4）
すべて元MAT/.mot/.sto/.osim から再計算し、PDF+SVG+600dpi PNG+source CSV+作図スクリプトを保存。自動QA23項目 PASS（`qa/qa_results.csv`）。

## B. 追加で実施した検証（再solve）と結果

### Figure S4（解像度頑健性: N=50 wide 対 N=100 wide）— **完成**
- 不足していたのは **N=50 wide の p2/p4/p6**（既存は p0/m2/m4/m6/m8 のみ）。これを再solve（strict `Solve_Succeeded`、22–33分/条件）し、N=50 wide 全8条件を得た。
- 新規MAT: `...19-August-2026__18-20-12___PelvisTDwide_p2/…18-47-03…p4/…19-20-05…p6`。
- 比較は**達成接地角**で行い、基準差 0.524°（N=50 −7.4626 / N=100 −7.987）はメッシュ依存の最適解シフトとして開示。**純粋な mesh convergence ではなく解像度頑健性**。
- **所見**: 用量反応の方向は両メッシュで一致（二関節3筋 正、BFsh 平坦）。ただし **N=50 の傾きは N=100 より約20%急**（例 SM: 0.00811 vs 0.00679/°）、達成角一致での差 |Δ|≈0.006–0.009。→ N=100 を主解析とする根拠を補強。

### Figure S3（筋腱パラメータ感度）— **3系統完成＋1系統は失敗を明示**
- **至適筋線維長 oMFL**（既存 `HamFascicle` ±10–30%）と**最大等尺性筋力 Fmax**（既存 `HamStrength` ±10–30%）は既存MATから再計算（新規solve不要）。
- **腱自然長 TSL** は `_HamTendon_*` 型を追加して再solve。**所見**: TSL は脆弱なパラメータで、−10% は strict だが全身動作が大きく変化（速度 11.57 = −2.4%、骨盤傾斜ドリフト、二関節平均 peak lMtilde 1.32）、**+10% は未収束**（`Maximum_CpuTime_Exceeded`、速度 7.12 に崩壊）。図では赤リング（速度ドリフト）と × （失敗）で明示。
- **重要（原ファイル不上書き）**: TSL 計算のための `main_pred_sim_sprinting.m` / `checkSimulationType.m` への追加（加算的・ASCII）は、MAT生成後に**元へ復元**（`git diff` クリーンを確認）。再現手順は `scripts/patch_HamTendon_for_S3.md` に保存。生成済みMATから S3 は再生成可能。
- **oMFL が支配的**（−10%短縮で二関節平均 +0.09、+10%で −0.08）、Fmax は微小（±0.008）。Timmins 2016 の短筋束リスクと整合。

## C. まだ不足しているデータ／未実施

1. **S3 受動力–長さ特性（passive force-length）**: 受動FL は大域パラメータ `Fpparam`（e0, kpe）で全筋共通のため、ハムストリング単独の一因子摂動には **per-muscle 化のモデル改変**が必要。加算的hookでは実現できず、未実施。
2. **S3 の完全な「用量反応傾き」感度**: 現行 S3 は**基準作用点**の感度（全身再最適化）。各摂動での用量反応**傾き**そのものの感度は、摂動ごとに接地角スイープ（4param×2方向×8条件≈64 solve）が必要で未実施。
3. **被験者本人の実験 GRF・EMG が無い**（`MainFunctions/ExperimentalData/` は IK スプラインのみ）。→ Fig 4 Panel B(GRF)/C(活動) は**シミュレーションのみ**と明示、GRF/EMG 誤差は `not available`。
4. **pelvis_tilt の規約/姿勢オフセット**（raw IK 接地 +5.0° vs モデル出力 −8.0°）。Fig 4 は無言整合せず注記。股膝足は形状一致（r=0.90–0.97）。
5. **接触モデル由来の GRF ピーク過大**（Nominal 鉛直 5.9 BW）。Fig 4 は「ピークでなく形状」を明記。
6. **筋25（quad_fem_r）設計意図が未確認**（実装=至適筋線維長+10%）。全条件共通で用量反応の**差**に無影響。**編集していない。**
7. **CasADi/IPOPT の厳密バージョンが MAT に未記録**（環境: MATLAB R2017b、De Groote2016: Fmax×2, vMax=12×lMo, aTendon=35, 受動 e0=0.6/kpe=4, Fce減衰 d=0.01）。

## D. 査読前に必ず直す/確認する事項
1. 筋25 のコメント訂正（実装＝至適筋線維長+10%）と設計意図の上流著者確認。
2. 本文で N=50/N=100 を「mesh convergence」と呼ばない（S4=解像度頑健性、N=50傾きは約20%急）。
3. Pareto の3解は「3決定論的ウォームスタート経路」であり独立多開始ではない、と明記（Fig 7 に記載済み）。
4. 「injury risk / safe motion / 予防」等の未検証表現を使わない（相関・機序に限定）。
5. S3 の腱スラック +10% は未収束（失敗）・−10% は作用点ドリフト有りである点を本文でも明示。受動FLは未実施。
6. S3/S4 の追加solve MAT（N=50 wide p2/p4/p6、HamTendon m10/p10）の SHA256 は `qa/input_hashes.csv` に記録済み。
