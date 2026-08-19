# 04 目視QA報告 / Visual QA report

出力: `output/thesis_figures_final_20260819_163600/`  ・ commit `e7b8de9` ・ 2026-08-19
各 600dpi PNG を実際に開いて目視確認した。自動QA（`qa/qa_results.csv`）20項目は全 PASS。

共通確認: 白背景・濃文字・控えめグリッド、3D/影/グラデ無し、PDF/SVG は文字・線が編集可能なベクター（`svg.fonttype=none`, `pdf.fonttype=42`）、PNG 600dpi、筋色固定（SM深緑/ST紫/BFlh青/BFsh灰・open）、色だけに依存せず marker/線種/open-filled 併用。軸ラベルは英語（和訳対応は下表）。

| 図 | 目視結果 | 文字切れ/重なり | 軸・単位・符号 | 白黒判読 | 問い→答えの即読性 | 修正履歴 |
|--|--|--|--|--|--|--|
| Fig1 study logic | 良 | 無 | 概念図（該当なし） | 可（色+テキスト） | 研究ギャップ→本研究→3解析の連鎖が一読で分かる | — |
| Fig2 primary | 良 | 無（Panel C 注記を左余白へ移動して解消） | A: m/s, B: lMtilde, C: /° 前傾。A=−pelvis_tilt 正 | 可（marker形状で4筋判別, BFsh open） | B が中心図、傾き+R²直接ラベルで即読 | 帯/ylim, ylabel短縮, 注記位置を修正 |
| Fig3 waveforms | 良 | 無（共有x軸へ変更して解消） | % stride, lMtilde, 共有y | 可（濃淡+peak marker+線） | ピーク時相と段階的上昇が一目 | x軸共有化 |
| Fig4 validation | 良 | 無（凡例を行間へ, B注記分離で解消） | % step/stride, deg, BW, 0-1 | 可 | 股膝足は形状一致, pelvis規約差を明示, GRF/EMGはsim限定 | レイアウト全面調整 |
| Fig5 mechanism | 良 | 無（Δ注記をタイトルへ移動で解消） | % phase, dMTU mm, 比% | 可（線種+色） | femur-fixedがadaptiveのTSピークをほぼ説明 | タイトル調整 |
| Fig6 robustness | 良 | 無 | expected/achieved deg, inf_pr log, m/s, funnel | 可（色+形+黒縁=採用） | 達成/残差/速度/採択フローが揃う | — |
| Fig7 pareto | 良 | 無（strict注記を左上へ移動で解消） | dSpeed%, dSurro%, %stride, deg | 可（marker形状=経路） | 目標領域内にw=0.05/0.1, w=0.2は速度予算超過 | 軸範囲/凡例/注記修正 |
| FigS1 force-length | 良 | 無 | lMtilde, Fce(N) | 可（濃淡+thick=TS） | 前傾大で終末遊脚の作用点が長lMtilde側へ | — |
| FigS2 heatmap | 良 | 無 | % change（発散色, 0中心）+セル値 | セル値併記で可 | Fpass が最大上昇, BFsh 中立 | — |

## 個別注記
- **Fig2**: 帯（±1%）がデータ幅より広いため、速度スプレッド0.43%を数値注記で補足（「全て±1%以内」）。回帰95%CI帯は描いていない（設計点は決定論的）。
- **Fig3**: 半膜様筋の谷 lMtilde≈0.30 は**実データ**（短筋束・長腱）で人工物ではない（別途 MAT 直読で確認）。共有y軸で谷も峰も表示。
- **Fig4**: pelvis_tilt は r=−0.31（規約/姿勢差）。股 r=0.97/膝 r=0.90/足 r=0.93（形状一致・オフセット有）。peak vGRF 5.9BW は接触モデル由来で過大の既知傾向を注記。GRF/EMG 誤差は `not available`。
- **FigS1**: 3筋で力の絶対値スケールが大きく異なる（SM~3300N, ST~800N）ため y 軸は筋ごと（異筋＝異量）。x（lMtilde）は各筋のROMに合わせた。これは「同一量の small multiples 統一」の合理的例外。
- **色覚/白黒**: 4筋は色＋marker形状＋open/filled で冗長符号化。Fig3 の濃淡は連続colorbar＋peak marker（白点縁）で判別可。

## 判定
本文 Fig 1–7 と補足 S1–S2 は、数値照合・単位・符号・評価窓・筋index・solver status の自動QAを通過し、目視でも文字切れ・過剰解釈が無いことを確認した。**Fig 2/3/4/5/6/7 は「明示的限界付きで提出可」**。Fig S3/S4 は未作成（`03_missing_data_and_blockers.md`）。
