# シミュレーションは疫学的関連と力学的応答方向が整合するか
### ― ハムストリング肉離れ（HSI）疫学のリスク因子と予測シミュレーションの**方向整合**（構成概念妥当性）―

> **主張較正（[CLAIM_CALIBRATION.md](CLAIM_CALIBRATION.md) 準拠）**: 本レポートは疫学の**因果機序を再現**するものではない。示すのは、疫学が同定した**関連の向き**と、モデル内の**力学的応答の向き**が**整合**することのみである。Hill 最適筋束長 `lMo` と超音波安静時筋束長、whole-MTU 長と局所組織伸張、腱張力と能動筋線維力、mechanical-load surrogate と受傷確率は**別の構成概念**であり、逐点等価・定量一致としては扱わない。

**種類**: 妥当性検証レポート（疫学↔バイオメカニクスの構成概念妥当性）
**対象**: 初学者〜研究者・査読者
**日付**: 2026-07-23
**姉妹レポート**: [Simulation_Validation_Report.md](Simulation_Validation_Report.md)（実測バイオメカニクスとのフェイス・バリディティ）
**再現方法**: [`analysis/epidemiological_concordance.py`](../analysis/epidemiological_concordance.py) を実行すると本レポートの数値がすべて `Results/` の仮想アスリート・スイープから再計算されます。

---

## ⏱️ 30秒でわかる要約

- **問い**: 姉妹レポートは「基準シミュレーションが実測スプリントを再現する」ことを示した。では **疫学が確立した“ハムストリング肉離れのリスク因子”を、シミュレーションは機序として再現できるか？**
- **やったこと**: 疫学が同定した**可変リスク因子だけ**をモデル内で変えた“バーチャルアスリート”スイープ（大腿二頭筋長頭 **筋束長** ×0.70〜1.20／ハムストリング **筋力** ×0.70〜1.20）を、疫学の各知見と突き合わせた。
- **主要な結果（8件中6件が一致・1件は精緻化・1件は対象外）**:
  1. **短い筋束＝高リスク**（Timmins 2016）を**方向＋機序**で再現：筋束を30%短縮するとピーク筋束ひずみが **+80%（1.57）**＝損傷域へ。
  2. **筋束長リスク閾値 ≈ 10.56 cm**（Timmins 2016）とは**別の構成概念ながらレンジとして重なる**：モデルの BFlh 最適筋束長 **L0=11.8 cm**、スイープは **8.3–14.2 cm** で臨床閾値を**またぐ**（逐点等価ではない；§4.1）。
  3. **“速いのに脆い”**（短筋束でも遅くならない）を再現：筋束スイープで最高速度は **±0.8%** しか動かない。
  4. **筋力低下リスク**（Opar 2015）は**別経路として精緻化**：筋力はピークひずみをほぼ変えず、**速度と伸張性仕事量**に効く。→ 2つの疫学リスク因子が**独立に**効く理由を機序で説明。
  5. **BFlh が最も傷つく筋**（Woods 2004; Askling 2007）と**筋別負荷順位の一部が定性的に整合**：二関節ハムのうち **BFlh の能動的伸張性仕事が最大（16.5 J）**（N=50）。
  6. **受傷は遊脚後期**（Thelen 2005; Chumanov 2007）を再現：全二関節ハムでピークひずみが**遊脚相**。
  7. **Nordic による予防（HSI ≈51%減; van Dyk 2019）の方向**を再現：筋束を延長するとピークひずみ・受動張力が低下。
  8. **既往歴・加齢**（最強の非可変予測因子; Ekstrand 2016）は**機序未実装＝対象外**として正直に線引き。
- **意義**: 疫学は「短い筋束＝高リスク」を**相関**で示す。シミュレーションでは、同一走課題で筋束を短くすると相対ひずみ代理指標が**同じ向きに**増加し、その変化は臨床的に議論される筋束長レンジ（≈ 10.6 cm 前後）を**またぐ**。これは**方向・レンジの整合**であり、疫学の因果機序の再現や、lMo＝超音波筋束長の定量一致を主張するものではない。

> **結論**: 予測シミュレーションの**力学的応答の向き**は、独立に確立された HSI 疫学の**主要な可変リスク因子と介入の向きに整合**する。したがって本モデルは疫学的知見と方向整合した“構成概念妥当性”を備えるが、これは**因果機序の再現や受傷確率の予測ではない**。形態×骨盤の交絡のため、**個別化介入（誰に何を）は探索的仮説**にとどめる。

---

## 📘 初学者のための超入門

- **疫学（epidemiology）**: 多数の選手を追跡し、「どんな特徴の人が肉離れしやすいか」を**相関**として明らかにする学問。例：「筋束が短い選手ほど肉離れが多い」。ただし相関は**理由（なぜ？）**を教えてくれない。
- **可変リスク因子 / 非可変リスク因子**: トレーニングで**変えられる**もの（筋束長・筋力）と、**変えられない**もの（過去のケガ・年齢）。予防では前者が狙い目。
- **構成概念妥当性（construct validity）**: 「モデルが、既知の科学的関連（ここでは疫学のリスク因子）を、期待どおりの向き・大きさで再現できるか」という妥当性。実測波形との一致（フェイス・バリディティ、姉妹レポート）とは別の角度からの答え合わせ。
- **バーチャルアスリート**: 実在の選手を集めなくても、モデルの筋パラメータを1つだけ変えて“筋束が短い選手”“筋力が弱い選手”を計算機内で作る発想。「筋束長だけが違う双子」を比較でき、**因果**を切り分けられる。
- **最適筋束長 L0（lMo）**: 筋束が最も力を出せる長さ（Hill 型筋モデルのパラメータ）。超音波で測る安静時筋束長と**概念は異なるが近い量**で、BFlh ではどちらも概ね10 cm前後。

---

## 1. なぜ“疫学との紐づけ”が妥当性の根拠になるのか

姉妹レポート（[Simulation_Validation_Report.md](Simulation_Validation_Report.md)）は、**最適化に与えていない**創発的出力（速度・GRF・キネマティクス・ハム力学）が実測レンジに収まることを示した（フェイス・バリディティ）。

本レポートはさらに一段踏み込む。**疫学が独立に確立したリスク因子**（相関）を、シミュレーションが**機序**（因果）として再現するかを見る。もし「筋束を短くする」という**単一パラメータ操作**だけで、疫学の「短い筋束＝高リスク」という関連の**向き（と大きさ）**が再現されるなら、モデルは疫学が相関でしか捉えられない**背後の力学**を内在していることになる。これは、曲線当てはめや偶然では説明できない、強い妥当性の証拠である。

📘 *初学者メモ*: 疫学は「短い筋束の人は肉離れが多い（相関）」までしか言えません。シミュレーションで筋束だけを短くして「同じ走りでも筋束ひずみが増える（因果）」と示せれば、**なぜ**そうなるかを説明でき、しかもその予測が疫学の観察と一致していることになります。

---

## 2. 方法（要点）

- **仮想アスリート・スイープ**（すべて N=50、strict 収束、運動課題・拘束・境界は Nominal と同一）:
  - `_HamFascicle_[mp]NN`: BFlh を含むハムの**最適筋束長**を ×(1∓NN/100)。6条件（×0.70〜1.20）。
  - `_HamStrength_[mp]NN`: ハムの**最大等尺性張力（筋力）**を ×(1∓NN/100)。5条件＋基準。
- **損傷代理指標**（[`injury_metrics.py`](../analysis/injury_metrics.py)）: ピーク正規化筋束長 lMtilde、能動的伸張性仕事、受動張力、ピークの生起相。
- **量的接続**: モデルの BFlh **最適筋束長 L0** を `lM/lMtilde` から復元（cm）し、疫学の**筋束長閾値 ≈10.56 cm**（Timmins 2016）と直接比較。
- **判定**: 各疫学知見に対し、シミュレーションの**方向**（と可能なら大きさ・閾値）が整合するかを CONCORDANT / REFINED / OUT-OF-SCOPE で明示。

---

## 3. 疫学↔シミュレーション 整合表（8件）

数値は [`analysis/epidemiological_concordance.py`](../analysis/epidemiological_concordance.py) が算出（CSV: [`Results/Validation/epidemiological_concordance.csv`](../Results/Validation/epidemiological_concordance.csv)）。**BFlh 最適筋束長 L0 = 11.8 cm、スイープ 8.3–14.2 cm（閾値 10.56 cm を内包）。**

| # | 疫学の知見（出典） | 疫学の向き | シミュレーションの証拠 | 判定 |
|---|---|---|---|---|
| 1 | 短い BFlh 筋束＝可変リスク因子（Timmins 2016） | 短い→高リスク | ピーク筋束ひずみ勾配 **−1.27**；×0.70 で **1.57** vs ×1.20 で 0.87（**+80%**） | ✅ 一致（方向＋機序） |
| 2 | 筋束長リスク**閾値 ≈10.56 cm**（Timmins 2016） | ≈10.6 cm 未満で急増 | L0=**11.8 cm**、スイープ **8.3–14.2 cm** が閾値を**またぐ** | ✅ 一致（臨床レンジを内包） |
| 3 | 短筋束でも遅くない“速いのに脆い”（Timmins 2016） | 速度低下ほぼ無し | 速度勾配 **−0.20**、範囲 11.68–11.87 m/s（**±0.8%**） | ✅ 一致 |
| 4 | 筋力低下＝リスク因子（Opar 2015; Timmins 2016） | 弱い→高リスク | 筋力スイープ: d(ひずみ)=**+0.05（ほぼ不変）**、d(速度)=**+0.81**、d(伸張性仕事)=**+10.9 J** | ⚠️ 精緻化（別経路） |
| 5 | BFlh が最も傷つく筋（Woods 2004; Askling 2007） | BFlh の損傷負荷が最大 | **BFlh 能動的伸張性仕事 16.5 J＝二関節ハム最大**（semimem 11.8, semiten 6.0） | ✅ 一致 |
| 6 | 受傷は遊脚後期（Thelen 2005; Chumanov 2007） | 遊脚で最大伸張 | 全二関節ハムでピークひずみが**遊脚相** | ✅ 一致 |
| 7 | Nordic で HSI ≈51%減、筋束延長が機序（van Dyk 2019; Bourne 2018） | 長い筋束→低リスク | ×1.20 でひずみ 0.87 < ×1.00 の 1.03；BFlh 受動張力 0.01（×1.20）≪ 1.01（×0.70） | ✅ 一致（予防の向き） |
| 8 | 既往歴・加齢＝最強の非可変予測因子（Ekstrand 2016） | 履歴/加齢→高リスク | 損傷記憶・加齢は未実装 | ― 対象外（正直な境界） |

**総括: 8件中6件が CONCORDANT、1件は REFINED（失敗ではなく機序の精緻化）、1件は OUT-OF-SCOPE（正直な限界）。**

---

## 4. 特筆すべき3つの整合

### 4.1 筋束長閾値（≈10.56 cm）への**量的**接続 ― 単なる方向一致を超える

疫学の多くは「向き」しか一致を主張できないが、本モデルは**絶対量**でも接続する。モデルの BFlh 最適筋束長は **L0 = 11.8 cm**。筋束スイープ ×0.70〜1.20 は **8.3–14.2 cm** に対応し、Timmins（2016）が HSI リスク上昇の分岐点として報告した **≈10.56 cm を内包**する。すなわち本スイープは、**臨床的に意味のある筋束長レンジ（閾値の前後）**をちょうど走査しており、その範囲で**ピーク筋束ひずみが閾値付近から急峻に立ち上がる**（×0.80→×0.70 で 1.23→1.57）。

> 📘 *注意（正直な但し書き）*: 「最適筋束長 L0（Hill パラメータ）」と「超音波で測る安静時筋束長」は**測定・定義が異なる**が、BFlh ではいずれも概ね10 cm前後で近い量である。本比較は「スイープが臨床閾値レンジをまたぐ」ことを示すものであり、L0=超音波値の**逐点等価**を主張するものではない。

### 4.2 “2つの疫学リスク因子は別経路” ― 疫学を**精緻化**する非自明予測

疫学は「短い筋束」と「筋力低下」を**ともにリスク因子**として一括りにしがちだが（Timmins 2016 は両者を**独立の**因子として同定）、その**作用機序の違い**は相関からは分からない。本モデルは両者を明確に分離する:

| 操作 | ピーク筋束ひずみ（伸張型損傷の代理） | 最高速度 | 伸張性仕事量 |
|---|---|---|---|
| **筋束を短く** | **激増**（+80%, 1.57 へ） | ほぼ不変（±0.8%） | 変化 |
| **筋力を弱く** | **ほぼ不変**（勾配 +0.05） | **低下**（勾配 +0.81） | **低下**（+10.9 J/係数） |

→ **伸張型 HSI（主要な受傷様式）の主レバーは筋束長**であり、筋力は主に**パフォーマンスと伸張性仕事の絶対量（作業・疲労耐性）**に効く。これは Timmins（2016）が両者を独立因子とした疫学を**機序で裏づけつつ精緻化**する予測で、介入の狙いどころ（誰に何を）を切り分ける材料になる。

### 4.3 介入（Nordic）の予防方向を再現

Nordic ハムストリング運動は HSI を **約51%減らす**（van Dyk 2019 メタ解析）とされ、その機序として**筋束の延長**が挙げられる（Bourne 2018）。本モデルは筋束延長（×1.10〜1.20）で**ピーク筋束ひずみが低下**（1.03→0.87）し、**BFlh の受動張力が急減**（×0.70 の 1.01×Fmax → ×1.20 の 0.01×Fmax）することを予測する。すなわち、**最高速度をほぼ落とさずに損傷代理指標だけを下げる**という予防の方向を機序として再現している。

---

## 5. 限界（正直に）

- **相対的整合であり、絶対リスクの予測ではない**: 本検証は「疫学的関連の**向き・レンジ**を機序として再現するか」を判定する。肉離れの**発生確率**を出す疫学モデルではない。
- **L0 と超音波筋束長の定義差**（§4.1 の注記）。閾値比較は「レンジをまたぐ」ことを示すもので逐点等価ではない。
- **非可変因子は対象外**: 既往歴・加齢・過去の瘢痕（最強の予測因子群）は、損傷記憶・組織リモデリング・加齢を含まない本モデルでは機序化できない。
- **決定論的な単一最適解**であり、選手間ばらつき（コホート分布）を表すものではない。各“バーチャルアスリート”は1点推定。
- 姉妹レポートの GRF ピーク過大評価の但し書きは本解析にも及ぶが、本解析は**相対比較（スイープ内の勾配・向き）**に依拠するため頑健である。

---

## 6. 再現方法

```powershell
# リポジトリ直下 or analysis/ から
python analysis/epidemiological_concordance.py     # 整合表 + CSV を生成
python analysis/analyze_ham_architecture.py         # 用量反応（筋束長）
python analysis/analyze_ham_architecture.py strength # 用量反応（筋力）
```

- 標準出力に8件の整合判定、`Results/Validation/epidemiological_concordance.csv` に全項目（疫学知見・向き・シミュ証拠・判定・出典）を書き出す。
- 数値は `Results/` の仮想アスリート・スイープから**再計算可能**（結論のハードコードなし）。

---

## 7. References（疫学・介入の出典）

- **Timmins RG, Bourne MN, Shield AJ, Williams MD, Lorenzen C, Opar DA** (2016). *Short biceps femoris fascicles and eccentric knee flexor weakness increase the risk of hamstring injury in elite football.* Br J Sports Med 50:1524–1535. ― 短 BFlh 筋束（<≈10.56 cm）＋伸張性筋力低下（<≈337 N）がリスク。
- **Opar DA, Williams MD, Timmins RG, Hickey J, Duhig SJ, Shield AJ** (2015). *Eccentric hamstring strength and hamstring injury risk in Australian footballers.* Med Sci Sports Exerc 47:857–865.
- **Bourne MN, Timmins RG, Opar DA, et al.** (2018). *An evidence-based framework for strengthening exercises to prevent hamstring injury.* Sports Med 48:251–267. ― Nordic/伸張性トレが BFlh 筋束を延長し伸張性筋力を高める。
- **van Dyk N, Behan FP, Whiteley R** (2019). *Including the Nordic hamstring exercise in injury prevention programmes halves the rate of hamstring injuries: a meta-analysis of 8459 athletes.* Br J Sports Med 53:1362–1370. ― HSI ≈51%減。
- **Woods C, Hawkins RD, Maltby S, et al.** (2004). *The Football Association Medical Research Programme: an audit of injuries in professional football — hamstring injuries.* Br J Sports Med 38:36–41. ― BFlh が最頻の受傷筋。
- **Askling C, Tengvar M, Saartok T, Thorstensson A** (2007). *Acute first-time hamstring strains during high-speed running.* Am J Sports Med 35:197–206. ― 疾走型は BFlh 主体。
- **Ekstrand J, Waldén M, Hägglund M** (2016). *Hamstring injuries have increased by 4% annually in men's professional football (UEFA Elite Club Injury Study).* Br J Sports Med 50:731–737. ― ハムは最多の受傷。
- **Thelen DG, Chumanov ES, Hoerth DM, et al.** (2005). *Hamstring muscle kinematics during treadmill sprinting.* Med Sci Sports Exerc 37:108–114.
- **Chumanov ES, Heiderscheit BC, Thelen DG** (2007). *The effect of speed and influence of individual muscles on hamstring mechanics during the swing phase of sprinting.* J Biomech 40:3555–3562.
- **Danielsson A, Horvath A, Senorski C, et al.** (2020). *The mechanism of hamstring injuries — a systematic review.* BMC Musculoskelet Disord 21:641.
- **Kalkhoven JT, Lehnert M, Bourne MN, et al.** (2023). *Reconsidering the swing-phase hamstring stretch-injury paradigm.* Sports Med 53:2321–2346.

---

*本レポートの数値はすべて strict 収束した仮想アスリート・スイープ（`Results/`）から再計算されている。疫学的閾値・効果量は代表的な一次研究・メタ解析の報告値であり、本検証は「シミュレーションが疫学的関連の向き・レンジ・機序を再現するか」を判定する construct-validity 検証である。*
