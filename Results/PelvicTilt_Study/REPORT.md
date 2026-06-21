# 骨盤前後傾とハムストリング肉離れリスク: 予測シミュレーション予備研究

作成日: 2026-06-05  
対象リポジトリ: `Pred_Sim_Sprinting`  
解析メッシュ: N=50 direct collocation

## 1. 研究目的

本研究の目的は、このリポジトリのスプリント最適化フレームワークを用いて、骨盤前後傾角 `pelvis_tilt` を変化させたときに、ハムストリング肉離れリスク指標がどのように変化するかを調べることである。

本モデルでは、`pelvis_tilt` の負方向がスプリント時の前傾に対応する。既存の N=50 Nominal 解では、骨盤傾斜角の平均は -7.26 deg、範囲は [-9.92, -2.59] deg であった。

## 2. 仮説

骨盤前傾が大きくなるほど、坐骨結節側で二関節性ハムストリングが伸張され、特に semimembranosus、semitendinosus、biceps femoris long head の正規化筋線維長 `lMtilde` と受動張力 `Fpetilde` が増加すると予測した。biceps femoris short head は単関節性であり、影響は小さいと予測した。

## 3. 実装方法

`MainFunctions/main_pred_sim_sprinting.m` に、`simulation_type` が `_PelvisTilt_*` を含むときだけ有効になる条件分岐を追加した。通常の `_Nominal`、`_HTD_*`、`_IKTD_*` ではベースライン挙動は変更されない。

実装した主な変更は以下である。

- `simulation_type` を引数として注入可能にした。
- `_PelvisTilt_m10` のような条件名から目標中心角を読み取るようにした。
- `createScaledBounds` 内で `pelvis_tilt` の位置境界だけを `[center - 6 deg, center + 6 deg]` に置き換えた。
- `createGuess` で `pelvis_tilt` 初期推定を条件中心に寄せた。
- `_PelvisTilt_*` 条件では N が一致する既存の厳密収束解から双対変数 `lam_x_opt`、`lam_g_opt` を含めて warm-start するようにした。
- `run_pelvic_tilt_sweep.m` を作成・修正し、必要パスを追加して複数条件を実行できるようにした。
- `analysis/analyze_pelvic_tilt.m` を作成・修正し、各条件の `.mat` からハムストリング指標を集計して CSV と図を保存するようにした。

## 4. 条件と収束状況

当初の計画条件は `_PelvisTilt_p00`, `_PelvisTilt_m04`, `_PelvisTilt_m07`, `_PelvisTilt_m10`, `_PelvisTilt_m13` であった。N=50 で試行錯誤した結果、解析可能な結果として保存できたのは Nominal、`m07`、`m10` の3条件である。

| 条件 | 目標中心 | 実現平均 `pelvis_tilt` | Solver status | 速度 (m/s) | 備考 |
|---|---:|---:|---|---:|---|
| Nominal | NA | -7.26 deg | `Solve_Succeeded` | 11.7774 | 既存 N=50 厳密収束解 |
| `_PelvisTilt_m07` | -7 deg | -7.39 deg | `Solved_To_Acceptable_Level` | 11.7755 | 許容解。制約違反は小さいが厳密解ではない |
| `_PelvisTilt_m10` | -10 deg | -8.50 deg | `Solve_Succeeded` | 11.7752 | 本研究で新規に厳密収束 |
| `_PelvisTilt_p00` | 0 deg | NA | 未収束 | NA | IPOPT restoration mode、`inf_pr` 約 1.8e3 で停滞 |
| `_PelvisTilt_m04` | -4 deg | NA | 未収束 | NA | restoration mode または起動・初期化段階で停滞。保存解なし |
| `_PelvisTilt_m13` | -13 deg | NA | 未収束 | NA | `_m10` から warm-start したが `inf_pr` 約 2.1e3 付近で停滞。保存解なし |

重要な注意点として、今回の操作は「骨盤傾斜角を厳密に目標角へ固定する」ものではなく、「許容窓をずらす」操作である。そのため `_PelvisTilt_m10` の実現平均は -10 deg ではなく -8.50 deg になった。速度最大化目的のもとでは、モデルは窓の中でより走りやすい傾斜角を選んだと考えられる。

## 5. 肉離れリスク指標

ハムストリング左右4筋について、以下を計算した。

- `peak lMtilde`: 正規化筋線維長の最大値。主要な伸張リスク proxy。
- `peak eccentric loading`: `max(0, vMtilde) * FMvtilde` の最大値。
- `peak Fpetilde`: 正規化受動線維力の最大値。
- composite risk: `lMtilde * max(0, vMtilde) * (Fce / Fiso)` の最大値。
- peak timing: `lMtilde` 最大時刻の半ストライド内 %。
- L/R asymmetry: 左右差 / 平均。

集計表: `pelvic_tilt_summary.csv`

## 6. 主要結果

### 6.1 骨盤傾斜の実現値

`_PelvisTilt_m07` は Nominal とほぼ同じ平均骨盤前傾で、Nominal の再現・近傍条件として機能した。`_PelvisTilt_m10` は Nominal より前傾が増えたが、実現平均は -8.50 deg であり、Nominal からの差は約 -1.23 deg だった。

図: `fig1_tilt_validation.png`

### 6.2 peak `lMtilde`

代表的な peak `lMtilde` は以下である。

| 筋 | 側 | Nominal | `_m07` | `_m10` | Nominal -> `_m10` |
|---|---|---:|---:|---:|---:|
| semimem | L | 0.9856 | 0.9868 | 0.9964 | +1.10% |
| semiten | L | 1.1343 | 1.1350 | 1.1410 | +0.59% |
| bifemlh | L | 1.0455 | 1.0465 | 1.0543 | +0.84% |
| bifemsh | L | 0.9393 | 0.9393 | 0.9390 | -0.03% |
| semimem | R | 0.9347 | 0.9360 | 0.9476 | +1.38% |
| semiten | R | 1.0823 | 1.0830 | 1.0898 | +0.70% |
| bifemlh | R | 0.9747 | 0.9758 | 0.9861 | +1.18% |
| bifemsh | R | 0.9443 | 0.9443 | 0.9438 | -0.05% |

最大値は一貫して左 semitendinosus で、Nominal 1.1343 から `_m10` 1.1410 に増加した。semimembranosus と biceps femoris long head も左右とも増加した。一方、biceps femoris short head はほぼ不変であり、仮説と整合する。

図: `fig2_peakLM.png`

### 6.3 `Fpetilde`

代表的な受動張力 `Fpetilde` は以下のように変化した。

| 筋 | 側 | Nominal | `_m10` | 変化 |
|---|---|---:|---:|---:|
| semimem | L | 0.01686 | 0.01813 | +7.52% |
| semiten | L | 0.04560 | 0.04767 | +4.54% |
| bifemlh | L | 0.02518 | 0.02671 | +6.09% |
| bifemsh | L | 0.01236 | 0.01234 | -0.17% |
| semimem | R | 0.01198 | 0.01307 | +9.03% |
| semiten | R | 0.03220 | 0.03386 | +5.17% |
| bifemlh | R | 0.01567 | 0.01692 | +7.99% |
| bifemsh | R | 0.01278 | 0.01273 | -0.34% |

受動張力は二関節性ハムストリングで増加し、bifemsh ではほぼ変化しなかった。これは「前傾増加により伸張性・受動張力リスクが増える」という仮説を支持する。

図: `fig3_peakFpe.png`

### 6.4 eccentric loading と composite risk

`max(0, vMtilde) * FMvtilde` は、`_m10` で semimembranosus 左が 2.0260 から 2.0399 に微増した一方、semitendinosus や biceps femoris long head ではやや低下した。composite risk も semimembranosus 左では 681.2 から 777.9 に増加したが、全筋で単調増加したわけではない。

従って、今回のデータから強く言えるのは「前傾増加は筋線維長と受動張力を増やす傾向がある」という点であり、「すべての動的リスク指標が単調に増える」とまでは言えない。

図: `fig4_composite_speed.png`

## 7. 解釈

今回の予備解析では、Nominal からやや強い前傾条件 `_PelvisTilt_m10` へ移ることで、二関節性ハムストリングの peak `lMtilde` と `Fpetilde` が小さいながら一貫して増加した。特に semimembranosus、semitendinosus、biceps femoris long head で増加し、biceps femoris short head はほぼ不変だった。

この筋ごとの差は、骨盤前傾が股関節をまたぐハムストリングの近位伸張に作用するという解剖学的な期待と整合する。したがって、骨盤前傾が肉離れリスクのうち「伸張ストレス成分」を高める可能性はある。

ただし、今回の変化量は比較的小さい。これは `_PelvisTilt_m10` でも実現平均が -8.50 deg に留まり、Nominal との差が約 1.23 deg だったためである。より強い結論を出すには、単なる境界窓ではなく、`pelvis_tilt` の平均値または時系列をより直接的に制御する必要がある。

## 8. 失敗と試行錯誤の記録

本研究では、単純な cold start では収束しなかった。Nominal 解の主変数だけでなく、IPOPT の双対変数 `lam_x_opt`, `lam_g_opt` も warm-start に渡すことで `_PelvisTilt_m10` が `Solve_Succeeded` まで到達した。

主な失敗と対策は以下である。

- `control_extrapolation` が見つからない: headless 直接実行で `UtilityFunctions` が path に入らなかった。runner 側に path 追加を実装して解決。
- cold/primal-only warm-start: IPOPT の dual infeasibility が悪化し、停滞した。双対 warm-start を追加して改善。
- `_PelvisTilt_m07`: 厳密解までは時間がかかったが、許容解として保存できた。
- `_PelvisTilt_p00`: neutral に近い骨盤窓は restoration mode に入り、制約違反が約 1.8e3 から改善しなかった。
- `_PelvisTilt_m04`: `_m07` の許容解を warm-start に使うと restoration mode に入りやすかったため、許容解は以降の warm-start 候補から除外した。ただし最終的な保存解は得られなかった。
- `_PelvisTilt_m13`: `_m10` から双対 warm-start したが、初期制約違反が約 2.16e3 と大きく、短時間では改善が遅かったため保存解は得られなかった。

## 9. 限界

- 完了した骨盤傾斜条件は Nominal、`_m07`、`_m10` のみであり、広い sweep ではない。
- `_m07` は `Solved_To_Acceptable_Level` であり、`_m10` のような厳密な `Solve_Succeeded` ではない。
- `_PelvisTilt_*` の操作は境界窓の移動であり、平均骨盤角を完全に固定していない。
- N=50 の粗いメッシュであり、N=100 以上での再現性確認は未実施である。
- composite risk は筋ごとに単調ではなく、伸張・速度・力の位相関係を追加解析する必要がある。

## 10. 結論

このリポジトリの最適化フレームワークを用いた予備研究として、骨盤前傾をやや増やすと、二関節性ハムストリングの peak `lMtilde` と `Fpetilde` が増加する傾向が確認された。特に semimembranosus、semitendinosus、biceps femoris long head で増加し、biceps femoris short head ではほぼ変化しなかった。

したがって、今回の結果は「骨盤前傾の増加は、ハムストリング肉離れリスクのうち筋線維伸張・受動張力成分を高める可能性がある」という仮説を予備的に支持する。ただし、広い角度範囲の全条件は収束していないため、結論は限定的である。

次の改善では、`pelvis_tilt` を境界窓で誘導するのではなく、平均角または時系列への追従項を目的関数に追加し、Nominal -> `m07` -> `m10` -> `m13` のような continuation を厳密収束解のみでつなぐことが望ましい。そのうえで N=100 で Nominal と高リスク条件を再計算すれば、より強い結論が得られる。

## 11. モーション可視化

収束した各条件 (Nominal、`_m07`、`_m10`) の coords `.mot` から、OpenSim モデルのフォワードキネマティクスでスティックフィギュアを再構成し、骨盤前後傾ごとの走動作を比較する動画と連続スナップショットを生成した。

各半ストライドは継続時間がわずかに異なるため、ストライド位相 [0,1] に正規化して同一位相で比較している。横並び・重ね合わせ動画はトレッドミル視点 (`pelvis_tx`/`pelvis_tz` をゼロに固定、鉛直の `pelvis_ty` は保持) で、図を中央に保ちながら脚の周期運動と腕振りを表示する。連続スナップショットは前進 (`pelvis_tx`) を残し、半ストライドの進行を左から右へ示す。

生成スクリプト: `../../analysis/visualize_pelvic_tilt_motion.py` (既存 `visualize_motion_comparison.py` の FK エンジンを再利用)

出力:
- 横並び動画 (条件ごと): `pelvic_tilt_motion_sidebyside.mp4`
- 重ね合わせ動画 (骨盤を揃えて姿勢比較): `pelvic_tilt_motion_overlay.mp4`
- 連続スナップショット (静止画): `pelvic_tilt_motion_sequence.png`

実現平均骨盤前傾は Nominal -7.27°、`_m07` -7.39°、`_m10` -8.50° と差が小さいため、3条件の走動作姿勢は視覚的にも近い。これは第6節の指標変化が小さかったことと整合する。

## 12. 出力ファイル

- 研究計画: `PLAN.md`
- 集計CSV: `pelvic_tilt_summary.csv`
- 図1: `fig1_tilt_validation.png`
- 図2: `fig2_peakLM.png`
- 図3: `fig3_peakFpe.png`
- 図4: `fig4_composite_speed.png`
- 解析ログ: `analysis_log.txt`
- モーション横並び動画: `pelvic_tilt_motion_sidebyside.mp4`
- モーション重ね合わせ動画: `pelvic_tilt_motion_overlay.mp4`
- モーション連続スナップショット: `pelvic_tilt_motion_sequence.png`
- 可視化スクリプト: `../../analysis/visualize_pelvic_tilt_motion.py`
- 主要成功結果: `../pred_sprinting_data_05-June-2026__11-00-52___PelvisTilt_m10.mat`, `../pred_sprinting_data_05-June-2026__14-50-15___PelvisTilt_m07.mat`
