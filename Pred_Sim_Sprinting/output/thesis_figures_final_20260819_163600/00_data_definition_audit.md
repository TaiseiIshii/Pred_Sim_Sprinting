# 00 データ定義監査 / Data-definition audit

出力: `output/thesis_figures_final_20260819_163600/`
Git commit: `e7b8de98016594ebc9d30ec4495c5958b3fe7020` (`e7b8de9`, main==origin/main)
再計算エンジン: `scripts/_common.py`（`Results/Independent_Audit_20260819/audit_recalc_N100.py` と定義一致・数値一致を確認）
生成日: 2026-08-19

本図集は**すべて元MAT / .mot / .sto / .osim から再計算**しており、論文本文の数値をハードコードしていない。
`01_numeric_reconciliation.csv` に、再計算値と課題文の期待値の三者照合（絶対差・相対差・判定）を記録した（27行・不一致0）。

---

## 1.1 条件（N=100 主解析）

- 採用系列: **PelvisTDwide**（接地時骨盤 `pelvis_tilt` を等式拘束、基準 −7.987°）、全8条件 **strict `Solve_Succeeded`**。
- 選択規則: 実験=PelvisTD・`options.N=100`・`return_status=='Solve_Succeeded'`（strict）・要求offsetごとに最終 `inf_pr` 最小。mtime 単独では選ばない。
- 正値の前傾量 `A = -pelvis_tilt_deg`（モデル規約: `pelvis_tilt` 負が前傾, main L136）。

| offset | 採用MAT (mtime) | achieved TD `pelvis_tilt`(°) | A = 前傾量(°) | achieved speed (m/s) | final inf_pr | solver |
|--|--|--|--|--|--|--|
| p6 | 25-Jun 07-24-05 | −1.987 | 1.987 | 11.788504 | 6.5e-09 | strict |
| p4 | 25-Jun 05-43-11 | −3.987 | 3.987 | 11.761059 | 2.3e-08 | strict |
| p2 | 25-Jun 04-33-19 | −5.987 | 5.987 | 11.787288 | 5.7e-08 | strict |
| p0 | 25-Jun 03-15-59 | −7.987 | 7.987 | 11.792386 | 1.3e-07 | strict |
| m2 | 25-Jun 02-31-10 | −9.987 | 9.987 | 11.797841 | 9.2e-08 | strict |
| m4 | 25-Jun 01-05-16 | −11.987 | 11.987 | 11.796764 | 5.5e-08 | strict |
| m6 | 25-Jun 00-01-41 | −13.987 | 13.987 | 11.765964 | 1.4e-08 | strict |
| m8 | 24-Jun 23-17-49 | −15.987 | 15.987 | 11.746657 | 7.9e-09 | strict |

- 達成前傾量レンジ **1.987–15.987°**、速度レンジ **11.7467–11.7978 m/s**（min=m8, max=m2）。全条件 Nominal N=100 速度 11.83456 比 ≤ −0.743%、条件間スプレッド 0.43%（全て ±1% 以内）。
- requested offset = achieved（基準 −7.987 + offset に厳密一致）。
- Nominal 定義: `pred_sprinting_data_10-April-2026__16-29-40___Nominal.mat`（N=100, strict, TD −7.987°, 11.83456 m/s）。
- **standard／wide の区別**: 主解析8条件は全て **wide**（基準 −7.987）。standard 系列（基準 −7.4626）は N=50 のみで、主結果には混在させていない。Fig 6D に全試行の系列別内訳を可視化。

## 1.2 筋（0-based MAT 行, 左右対称再構成の基準=右脚）

| 略号 | 英名 | 和名 | L 行 | R 行 | 種別 |
|--|--|--|--|--|--|
| SM | semimembranosus | 半膜様筋 | 6 | 52 | 二関節 |
| ST | semitendinosus | 半腱様筋 | 7 | 53 | 二関節 |
| BFlh | biceps femoris long head | 大腿二頭筋長頭 | 8 | 54 | 二関節 |
| BFsh | biceps femoris short head | 大腿二頭筋短頭 | 9 | 55 | 単関節（解剖学的対照） |

筋名↔index は MAT（行）・OpenSim モデル（`semimem_l` 等の筋名）・解析コード（`_common.L/R`）の3箇所で照合済み。左右対称性（行 r と r+46 の一致）で index を検証。

## 1.3 評価量の定義（`_common.py` 実装）

- `lMtilde = lM / lMo`（正規化筋線維長）。工学ひずみでも超音波筋束長でもない。
- **1ストライド最大 lMtilde（主評価項目）** = 左右対称再構成した1ストライド全体の最大値（NOT terminal-swing 窓）。
- 1ストライド再構成: 右脚1歩 `x_R(t)`（`[0,T]`）＋左脚1歩 `x_L(t−T)`（`[T,2T]`）を連結。`T=totalTime`（1歩=半ストライド）。継目不連続 ≤ 6e-15。
- 最大値の出現時相 `tPeak% = 100·t_argmax / (2T)`。二関節3筋 **85.5–90.8% stride**、BFsh は早期立脚 ~2.1–2.8%（別機序）。
- terminal swing（筋指標窓）= 遊脚後半25% = `[2T−0.25(2T−contact), 2T]`（≈79% 以降）。**境界条件解析の TS 窓（phase≥85%）とは別定義**（Fig 5 で明記）。
- **Fce** = De Groote 2016 の**収縮要素力（減衰項 d=0.01 を含む）**。純粋な active force ではない（図・凡例・キャプションで「Fce (収縮要素力, 減衰項含む)」と表記）。
- 受動筋線維力 `Fpass`、腱力 `FT`、`Fpetilde`（正規化受動力）。
- 物理筋線維速度 `vM = vMtilde × vMax`（m/s, >0=伸張）。
- 負の筋線維仕事（吸収エネルギーの大きさを正値で報告）= `∫ max(Fce·vM, 0) dt`、非一様 `timeNodes` に台形則。
- Pareto の**直接最小化対象** = `∫ (smoothpos(lMtilde−1))^2 dt`（平滑化 hinge の二乗時間積分）。**報告する terminal-swing-window peak lMtilde とは別物**（事後読み出し）。

## 1.4 数値チェックポイント（再計算値 vs 課題期待値）

`01_numeric_reconciliation.csv` に全27行。要約:

| 量 | 再計算 | 期待 | 判定 |
|--|--|--|--|
| achieved anterior tilt | 1.987–15.987° | 1.987–15.987° | 一致 |
| achieved speed | 11.7467–11.7978 m/s | 同 | 一致 |
| 傾き/° SM/ST/BFlh | 0.006785 / 0.003741 / 0.005379 | 0.00678 / 0.00374 / 0.00538 | 一致 |
| 速度調整係数 SM/ST/BFlh | 0.006402 / 0.003509 / 0.005037 | 0.00640 / 0.00351 / 0.00504 | 一致 |
| R² 二関節3筋 | 0.9498–0.9614 | 0.950–0.961 | 一致（丸め） |
| min→max% 二関節3筋 | +4.65 / +7.19 / +9.72 | +4.65–9.72 | 一致 |
| BFsh 端点変化 | −0.32% | −0.32 | 一致 |
| ピーク時相 二関節3筋 | 85.5–90.8% stride | 同 | 一致 |
| femur-fixed/adaptive TS 比 | 92.1 / 89.6 / 95.8% | 89.6–95.8 | 一致 |
| Pareto w=0.1 平均 dSpeed | −0.3401% | −0.340±0.011 | 一致 |
| Pareto w=0.1 平均 dSurrogate | −5.1889% | −5.189±0.077 | 一致 |

**唯一の注記**: BFsh の**生**傾き = −0.000254/°。課題文の「−0.00027/°」は**速度調整後**係数（−0.000272）に一致する。丸め・列帰属の差であり、データ系列の差ではない（`01_numeric_reconciliation.csv` に明記）。

## 1.5 未解決・限界（該当図の判定に影響する事項）

- **筋25 = `quad_fem_r`**: `main_pred_sim_sprinting.m` L872-3 の `muscProperties(2,25)` は**第2行=至適筋線維長を +10%**（コメントの「tendon slack length」は誤り、row3 が腱自然長）。上流 Haralabidis 由来（`b90bf188`, 2024-04-21）、**全条件共通**のため用量反応の**差**（本図集の主対象）には無影響。設計意図は**未確認**。→ 差分ベースの Fig 2/3/5/7 は提出可、絶対値の因果解釈は不可。**編集していない。**
- **N=50 と N=100 は純粋なメッシュ収束ではない**（N=100 全wide 基準 −7.987、N=50 基準 −7.4626、0.524° シフト）。本図集は **N=100 を主解析**とする。**Fig S4** では N=50 wide の欠損3条件（p2/p4/p6）を再solveして全8条件を揃え、**達成接地角**で N=50/N=100 を比較（解像度頑健性）。方向は両メッシュ一致だが N=50 傾きは約20%急。
- **Fig S3**（筋腱パラメータ感度）は oMFL（既存 HamFascicle）・Fmax（既存 HamStrength）・TSL（`_HamTendon_*` を追加solve）の3系統。TSL +10% は未収束（失敗として明示）、−10% は作用点ドリフト有り。TSL用の追加コードは MAT 生成後に**元へ復元**（原ファイル不上書き、`scripts/patch_HamTendon_for_S3.md`）。受動FLは per-muscle 化が必要で未実施。
- **Fig 4**: 被験者本人の実験 GRF・EMG は本データセットに存在しない → GRF/活動は**シミュレーションのみ**（明示）、GRF/EMG 誤差は `not available`。pelvis_tilt は raw IK とモデル出力で規約/姿勢オフセットが異なるため、**無言で整合させず注記**（オフセット除去後の形状一致のみ提示）。
