# 学会発表・ポスター準備計画

## 発表の主軸

本発表は、骨盤前傾そのものの再確認ではなく、**予測シミュレーションを使って、ハムストリング肉離れリスク proxy と最高速度の速度-安全トレードオフを設計し、選手タイプごとに介入を選ぶ**ことを主軸にする。

推奨タイトル案:

> 予測シミュレーションによるハムストリング肉離れ予防の速度-安全パレート設計

短い副題案:

> 筋束長・筋力の違いに応じた「技術 vs トレーニング」の個別化処方

## 中心メッセージ

1. 標準的なスプリンターでは、二関節ハムストリングの筋束過伸張ペナルティをわずかに加えると、最高速度をほぼ保ったままピーク筋束ひずみを下げられる低コスト領域がある。
2. 短筋束アスリートでは、走り方だけで安全側へ寄せると速度代償が大きく、筋束を長くするトレーニング経路の方が有利である。
3. 弱筋力アスリートでは、筋力は主に速度を変え、ピーク筋束ひずみは大きく変えない。したがって、強化と技術修正は別目的のつまみとして扱う。

## 発表用の仮説

### H1: 標準選手の速度-安全パレート

二関節ハムストリングの筋束過伸張を目的関数で罰すると、最高速度の低下がほぼゼロに近い範囲で、ピーク筋束ひずみと受動張力を低下させる最適フォームが存在する。

検証:

- `_HamPareto_Nom_wXXXX` の重み掃引。
- 主要評価軸は、最高速度、二関節ハム平均ピーク `lMtilde`、`Fpetilde`、能動的伸張性仕事。
- `w=0` が N=50 Nominal を再現する自己整合性を確認。

### H2: 短筋束選手では技術修正が高コスト

最適筋束長が短い選手では、筋束ひずみが構造的に高く、走り方だけで安全域に入るには大きな速度損失を要する。一方、筋束長を標準へ戻すトレーニング経路は、速度を落とさずにひずみを下げる。

検証:

- `_HamPareto_Sh_wXXXX` の技術パスと、RQ2 の `_HamFascicle_*` 筋束長パスを同じ速度-ひずみ平面で比較。
- 短筋束 base は `HamFascicle_m20`、トレーニング比較は factor 0.80 -> 1.00 を中心に示す。

### H3: 弱筋力選手では強化と安全化は直交する

筋力低下は速度と伸張性仕事量に効くが、ピーク筋束ひずみへの影響は小さい。そのため、弱筋力選手に対する強化は主にパフォーマンス改善、技術修正はひずみ低下として分けて解釈する。

検証:

- `_HamPareto_Wk_wXXXX` と `_HamStrength_*` の比較。
- 「弱い = すぐ過伸張する」ではなく、「弱い = 速度・仕事量の経路」という精緻化として提示する。

## 主張してよいこと / 避けること

| 強く主張してよいこと | 避けるべき表現 |
| --- | --- |
| 速度-安全の低コスト領域が、このモデルの最適解として存在した | 実選手でも必ず同じフォーム変更で肉離れが減る |
| 報告値は fascicle-strain injury surrogate の変化である | 肉離れ発生確率を直接予測した |
| 短筋束リスクは、走り方より筋束長そのものに由来する可能性が高い | 短筋束選手に技術指導は無意味 |
| 弱筋力は速度経路、筋束長はひずみ経路という分離が見えた | 筋力低下は肉離れリスクではない |
| GRFピークではなく、筋束・受動張力・相対比較を主証拠にする | 絶対GRFピークを組織負荷の主証拠にする |

推奨表現:

- 「injury risk」単独ではなく、原則として「筋束ひずみベースの injury-risk proxy」または「fascicle-strain injury surrogate」と書く。
- 「free lunch」は口頭説明や一般向け図では使ってよいが、ポスター本文では「low-cost region」または「near-zero speed-cost region」を使う。
- `wJ(13)` は実測されたコーチング量ではなく、速度-安全トレードオフを探索するための最適化上の重みであると明記する。

## ポスター構成案

### Panel 1: Background and Validation

目的:

- なぜ筋束レベルを見る必要があるか。
- 基準モデルと疫学整合性がどの程度あるかを最小限で示す。

載せる内容:

- 基準 Nominal は原著速度 11.85 m/s を 0.1% 差で再現。
- 28指標中25指標が文献レンジ内。
- 短BFlh筋束長、Nordic方向、BFlh負荷、遊脚期ピークなど疫学の主要知見と整合。

図候補:

- `Results/HamArch_Study/viz_speed_injury_landscape.png` の小型版。
- もしくは文献整合を示す小表のみ。

### Panel 2: Method

目的:

- 「速さ最大化」に「筋束を伸ばしすぎるな」という罰則を足しただけであることを伝える。
- 最適化 surrogate と報告 metric の違いを明示する。

載せる内容:

- 既存コスト: 平均速度最大化 + 正則化。
- 追加コスト: 二関節ハム `lMtilde > 1.0` の滑らかな片側二乗ペナルティ。
- 報告指標: post-hoc の真のピーク `lMtilde`、`Fpetilde`、eccentric work。
- 対照: 単関節 bifemsh はペナルティ対象外。

数式:

$$J_{inj} = w_{13}s\sum_j B_j h\sum_{m \in biartic\ ham} smoothpos(\tilde l_{M,m}-1.0)^2$$

### Panel 3: Results - Nominal Pareto Frontier

目的:

- 低コスト領域を一目で示す。

載せる数字:

- `w=0.05`: 速度損失 0.09%、ピーク筋束ひずみ 2.36%低下。
- `w=0.10`: 速度損失 0.24%、ピーク筋束ひずみ 3.91%低下。
- 最大安全側 `w=3.20`: 速度損失 2.23%、ピーク筋束ひずみ 12.01%低下、受動張力は約半分。

図候補:

- `Results/HamPareto_Study/explainer_frontier_jp.png`、専門発表なら `pareto_frontier.png`。
- 補助に `permuscle_vs_weight.png`。

### Panel 4: Results - Individualized Intervention

目的:

- 「誰に何をするか」が本研究の新規性であることを示す。

載せる数字:

- 短筋束選手: 技術 `w=0.80` ではひずみ 20.30%低下だが速度 14.57%低下。
- 短筋束のトレーニング path: factor 0.80 -> 1.00 でひずみ 1.229 -> 1.026、速度 11.68 -> 11.78 m/s。
- 弱筋力選手: 技術 `w=0.20` でひずみ 6.33%低下、速度 0.55%低下。強化は主に速度を上げ、ひずみは大きく変えない。

図候補:

- `Results/HamPareto_Study/explainer_decision_jp.png`、専門発表なら `technique_vs_training.png`。

### Panel 5: Mechanism and Take-home

目的:

- 安全側フォームが具体的に何を変えたのかを示す。

載せる内容:

- 標準選手の安全側フォームでは、骨盤が前傾から後傾寄りへ、遊脚脚の股関節屈曲ピークが 33 deg -> 20 deg へ低下。
- これは二関節ハムの近位伸張を下げる。

図候補:

- `Results/HamPareto_Study/ham_pareto_musculoskeletal_hero.png`
- `Results/HamPareto_Study/motion_compare_nominal_jp.png`

## 査読者・質疑への先回り

| 想定質問 | 回答方針 | 追加解析の優先度 |
| --- | --- | ---: |
| 最適化で罰した量を評価しているだけでは？ | 最適化は integrated smooth overstretch、評価は post-hoc peak `lMtilde`、`Fpetilde`、eccentric work、運動学で多面的に確認していると説明する | 高 |
| `lMtilde > 1.0` の閾値は恣意的では？ | 1.0 は力-長さ曲線の至適長基準。発表前に 0.95/1.05 感度を追加できると強い | 高 |
| N=50 だけで十分か？ | TDPT は N=100 確認済み。Pareto は計算コスト上 N=50が主。主要点だけN=100確認を今後/追加解析として示す | 高 |
| 実際の肉離れ確率ではないのでは？ | その通り。injury probability ではなく、筋束ひずみ・受動張力 proxy の最適制御研究と明示する | 高 |
| 単一被験者・左右対称で一般化できるか？ | 個別化処方の概念実証であり、個体差・非対称・疲労は次段階。主張は相対効果に限定 | 中 |
| 筋束長スケーリングは実際のトレーニング適応と同じか？ | 実適応そのものではなく、筋形態が変わった仮想条件。Nordic等の方向と整合する mechanistic path として扱う | 中 |
| GRFピークが高いモデルで大丈夫か？ | 絶対GRFピークは主張に使わず、力積と相対比較、筋束指標を主証拠にする | 中 |

## 追加解析ロードマップ

### 発表前に最優先

1. 既存結果から `Fpetilde`、eccentric work、per-muscle response をポスター表に入れる。
2. `wJ(13)` が integrated surrogate、報告軸が post-hoc peak である説明図を作る。
3. 主要Pareto点だけN=100を検討する: Nom `w0000`, `w0050` or `w0100`, `w3200`。

### 可能なら追加

1. 閾値 `lambda_thr` の感度: 0.95 / 1.00 / 1.05。
2. スケール `s=1e4` の感度: 重み値そのものではなく frontier shape が保たれるか。
3. 疲労や左右非対称は将来課題として明記。

## 口頭説明用の短いストーリー

> まず、基準シミュレーションが実測スプリントと疫学リスク因子に整合することを確認しました。次に、最速疾走の目的関数へ、二関節ハムストリングの筋束を伸ばしすぎないための滑らかなペナルティを加え、その重みを少しずつ変えて速度-安全パレート境界を描きました。標準選手では、速度をほぼ落とさずに筋束ひずみを下げられる低コスト領域がありました。一方、短筋束選手では同じ技術修正が高い速度代償を伴い、筋束長を戻すトレーニング経路の方が有利でした。弱筋力選手では、強化は主に速度を上げ、ひずみは技術で下げるという直交した経路でした。つまり、予測シミュレーションは「なぜ危険か」だけでなく、「誰に何をすべきか」を設計する道具になり得ます。

## 検証コマンド

```powershell
python analysis/validate_against_literature.py
python analysis/epidemiological_concordance.py
python analysis/analyze_ham_pareto.py
python analysis/visualize_ham_pareto.py
python analysis/visualize_ham_pareto_explainer.py
```

## 参照ファイル

- `docs/Hamstring_Pareto_Study_Report.md`
- `docs/Hamstring_Fascicle_Study_Report.md`
- `docs/Simulation_Validation_Report.md`
- `docs/Epidemiological_Concordance_Report.md`
- `Results/HamPareto_Study/pareto_frontier.csv`
- `Results/HamPareto_Study/explainer_frontier_jp.png`
- `Results/HamPareto_Study/explainer_decision_jp.png`
- `Results/HamPareto_Study/ham_pareto_musculoskeletal_hero.png`
