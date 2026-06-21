# 骨盤の傾きと「走りの速さ・ケガのリスク」— やさしい要約

作成日: 2026-06-21
対象: チーム共有用のやさしいまとめ（詳細版は [REPORT.md](REPORT.md)）

---

## ひとことで言うと

スプリント中に **骨盤を前に倒す（前傾を強める）ほど**、

- **走る速さ**は **わずかに落ちる**
- **ハムストリング（もも裏）の肉離れリスク**は **はっきり上がる**（特に半膜様筋）

逆に **骨盤を後ろに起こす（後傾ぎみ）** と、速さはほぼ変わらないまま、もも裏の
伸ばされ具合（＝肉離れリスクの一因）は下がりました。

> これは実走の計測ではなく、**最適化シミュレーション**で骨盤の傾きだけを
> ±6°ずらして比較した結果です。「骨盤の傾き」以外の条件はそろえています。

---

## 何をしたか（実験のしくみ）

1. まず「全力スプリント」を最適化シミュレーションで1回解く（基準フォーム）。
2. 同じ走りに対して、**骨盤の前後傾だけ**を 2°きざみで強制的にずらす
   （−6°〜+6°、計7条件）。「マイナス＝前傾を強める」「プラス＝後傾ぎみ」。
3. それぞれで **達成速度** と **もも裏4筋の伸ばされ具合** を測って比べる。

骨盤の傾きを「狙いどおり正確に」ずらせたことは確認済みです（下の図1）。

---

## 結果（数字でわかる変化）

### 1. 走る速さ

| 骨盤の傾き | 実際の平均傾き | 達成速度 |
|---|---:|---:|
| 前傾を強める（−6°） | −13.1° | 10.62 m/s |
| 前傾を強める（−4°） | −11.2° | 10.52 m/s |
| 少し前傾（−2°） | −9.2° | 11.50 m/s |
| 基準（0°） | −7.3° | 11.78 m/s |
| 少し後傾（+2°） | −5.7° | 11.78 m/s |
| 後傾ぎみ（+4°） | −3.6° | 11.76 m/s |
| 後傾ぎみ（+6°） | −1.5° | 11.75 m/s |

→ **前傾を強めるほど遅くなる**（特に −4°/−6° で大きく低下）。後傾側はほぼ横ばい。

### 2. もも裏（ハムストリング）の伸ばされ具合 ＝ 肉離れリスク

「正規化筋線維長（lMtilde）」が大きいほど筋肉が**引き伸ばされている**＝肉離れの
**伸張リスクが高い**ことを意味します。骨盤を1°前傾するごとの変化（傾き）：

| 筋肉 | 前傾1°あたりの伸び | あてはまり(R²) | コメント |
|---|---:|---:|---|
| 半膜様筋 (semimembranosus) | 強く増加 | 0.99 | **最もリスクが上がる** |
| 大腿二頭筋・長頭 (bifemlh) | 増加 | 0.98 | 二関節筋 |
| 半腱様筋 (semitendinosus) | 増加 | 0.99 | 二関節筋 |
| 大腿二頭筋・短頭 (bifemsh) | **ほぼ変化なし** | — | 単関節筋（対照） |

→ 股関節をまたぐ**二関節のハムストリングだけ**が前傾で伸ばされ、股関節をまたがない
短頭は**変化なし**。これは「前傾→骨盤(坐骨)が後上方へ回る→もも裏が引き伸ばされる」
というメカニズムの**動かぬ証拠**です。受動的な張力（こわばり）も半膜様筋で約2割増。

---

## なぜそうなるのか（メカニズム）

```
骨盤を前に倒す（前傾↑）
   → 坐骨結節（もも裏の付け根）が後ろ上方へ回る
   → 二関節ハムストリングが股関節側で引き伸ばされる
   → 筋線維長・受動張力が増える（肉離れの伸張リスク↑）
   ※ 短頭は股関節をまたがないので影響なし（対照）
```

---

## 実践的な示唆

- スプリント中の**過度な骨盤前傾**は、**もも裏（特に半膜様筋）の肉離れリスク**を
  高める方向に働きます。速度面でも前傾しすぎは不利でした。
- **中間〜やや後傾**の骨盤は、速度の損失がほとんどなく、もも裏の伸張リスクを
  下げる方向です。
- ただし本結果は**シミュレーション上の傾向**であり、個人差・実走条件は別途検証が必要です。

---

## 可視化（動画・画像）

「骨盤の傾きごとに走りがどう違うか」を3通りの見せ方で用意しました。
すべて **代表3条件（−6° / 0° / +6°）** の比較です。

### A. 筋骨格モデル（実際のOpenSim骨格＋もも裏を“ひずみ色”で表示）★おすすめ
本物のOpenSim骨メッシュを動かし、もも裏4筋を**伸び具合で色分け**（緑=低リスク→
赤=高リスク）。「どの傾きでもも裏が赤く＝危険になるか」が一目でわかります。

- 横並び: [pelvic_shift_musculoskeletal_sidebyside.mp4](pelvic_shift_musculoskeletal_sidebyside.mp4)
- 重ね合わせ: [pelvic_shift_musculoskeletal_overlay.mp4](pelvic_shift_musculoskeletal_overlay.mp4)
- 静止画（ピーク伸張）: [pelvic_shift_musculoskeletal_hero.png](pelvic_shift_musculoskeletal_hero.png)

### B. 3D人体（SMPL風の人体シルエット）
人体の見た目に近い滑らかなボディで、フォーム全体の違いを直感的に表示。

- 横並び: [pelvic_shift_smpl_sidebyside.mp4](pelvic_shift_smpl_sidebyside.mp4)
- 重ね合わせ: [pelvic_shift_smpl_overlay.mp4](pelvic_shift_smpl_overlay.mp4)
- 静止画: [pelvic_shift_smpl_hero.png](pelvic_shift_smpl_hero.png)

### C. スティックフィギュア（軽量・全7条件）
最も軽い棒人間表示（読み込みが速い）。

- 横並び: [pelvic_shift_motion_sidebyside.mp4](pelvic_shift_motion_sidebyside.mp4)
- 重ね合わせ: [pelvic_shift_motion_overlay.mp4](pelvic_shift_motion_overlay.mp4)

### グラフ
- 操作の成立確認: [fig1_manipulation_check.png](fig1_manipulation_check.png)
- もも裏の伸び（用量反応）: [fig2_dose_peakLM.png](fig2_dose_peakLM.png)
- 受動張力・伸張仕事: [fig3_dose_passive_eccwork.png](fig3_dose_passive_eccwork.png)
- メカニズム・速度コスト: [fig4_mechanism_cost.png](fig4_mechanism_cost.png)

---

## 動画の作り直し方（チーム向け）

`analysis/` の以下のスクリプトで再生成できます。**pyvista・vtk・imageio-ffmpeg** と
**OpenSim 4.x の Geometry**（骨メッシュ `.vtp`）が必要です。

```bash
# 環境（pyvista 等）を入れる
pip install pyvista imageio imageio-ffmpeg scipy numpy matplotlib

# 筋骨格モデル（骨＋もも裏ひずみ着色）
python analysis/visualize_pelvic_shift_musculoskeletal.py --fps 25 --frames 60 --cycles 2

# 3D人体（SMPL風）
python analysis/visualize_pelvic_shift_smpl.py --fps 25 --frames 60 --cycles 2

# 軽量スティックフィギュア（全7条件）
python analysis/visualize_pelvic_shift_motion.py --fps 25 --frames 80 --cycles 2
```

- OpenSim Geometry は `OPENSIM_HOME` 環境変数か `C:\OpenSim 4.x\Geometry` から自動検出します。
- 本物の SMPL ボディを使いたい場合は `--smpl_model <path>` を指定します
  （`smplx` と研究ライセンス取得済みモデルが必要。未指定時は soft-body 近似で動作）。

詳しい数値・手法・限界・試行錯誤の記録は [REPORT.md](REPORT.md) を参照してください。
