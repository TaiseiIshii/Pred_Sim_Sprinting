# -*- coding: utf-8 -*-
"""
content_ja.py -- structured Japanese content for the GitHub Pages thesis site.

This module holds ONLY data (title, sections, figure/video metadata). The
rendering engine lives in build_site.py. Bodies are raw HTML strings; LaTeX is
written with MathJax delimiters \\( \\) (inline) and \\[ \\] (display).

Numbers are taken from the frozen manuscript
(docs/修士論文学位審査提出候補稿_日本語.md), which was independently reproduced
from the raw MAT/.mot/.sto/.osim by Results/Independent_Audit_20260819/ and by
output/thesis_figures_final_20260819_163600/ (QA 23/23 PASS). They are not
re-derived here; this file only presents them.

IMPORTANT (implementation note): helper functions below use string
concatenation -- NOT f-strings / str.format / %-formatting -- because captions
and bodies contain literal "%", "{", "}" and LaTeX backslashes that would break
those mechanisms.
"""

# --------------------------------------------------------------------------- #
#  Asset manifests (consumed by build_site.py to copy files into site/assets)
# --------------------------------------------------------------------------- #
FIGURE_FILES = [
    "Fig1_study_logic.png",
    "Fig2_primary_N100.png",
    "Fig3_lMtilde_waveforms_N100.png",
    "Fig4_baseline_validation.png",
    "Fig5_pelvis_femur_mechanism.png",
    "Fig6_numerical_robustness.png",
    "Fig7_pareto_N100.png",
    "FigS1_force_length.png",
    "FigS2_muscle_metric_heatmap.png",
    "FigS3_param_sensitivity.png",
    "FigS4_mesh_robustness.png",
]

# (repo-relative source, destination filename under site/assets/video/)
VIDEO_FILES = [
    ("Results/PelvicTD_Study/pelvic_td_musculoskeletal_sidebyside.mp4", "pelvic_td_sidebyside.mp4"),
    ("Results/PelvicTD_Study/pelvic_td_musculoskeletal_sidebyside.gif", "pelvic_td_sidebyside.gif"),
    ("Results/HamPareto_Study/ham_pareto_musculoskeletal_sidebyside.mp4", "ham_pareto_sidebyside.mp4"),
    ("Results/HamPareto_Study/ham_pareto_musculoskeletal_sidebyside.gif", "ham_pareto_sidebyside.gif"),
]

TITLE = "最高速度スプリントにおける接地時骨盤前傾と二関節ハムストリング筋線維伸長の関係"
SUBTITLE = "予測筋骨格シミュレーションによる段階的関係、機序分解および速度–負荷最適化 ― 詳細解説版（Web補足）"


# --------------------------------------------------------------------------- #
#  Reusable HTML component helpers (concatenation only)
# --------------------------------------------------------------------------- #
def fig(anchor, src, tag, title, purpose, result, note, cap_en):
    """One figure block: image + purpose/result/caution/bilingual caption."""
    return (
        '<figure class="figblock" id="' + anchor + '">'
        '<a class="zia" href="assets/fig/' + src + '" target="_blank" rel="noopener">'
        '<img loading="lazy" src="assets/fig/' + src + '" alt="' + tag + '"></a>'
        '<figcaption>'
        '<p class="figtag"><b>' + tag + '</b> ｜ ' + title + '</p>'
        '<p class="purpose"><span class="lab labP">目的</span> ' + purpose + '</p>'
        '<p class="result"><span class="lab labR">結果（事実）</span> ' + result + '</p>'
        + (('<p class="note"><span class="lab labN">注意</span> ' + note + '</p>') if note else '')
        + '<p class="capen"><b>Caption (EN):</b> ' + cap_en + '</p>'
        '</figcaption></figure>'
    )


def vid(anchor, mp4, gif, tag, title, purpose, result, note):
    """One video block with mp4 source and an animated-GIF fallback link."""
    return (
        '<figure class="figblock vidblock" id="' + anchor + '">'
        '<video controls loop muted playsinline preload="metadata">'
        '<source src="assets/video/' + mp4 + '" type="video/mp4">'
        'お使いの環境では動画を再生できません。'
        '<a href="assets/video/' + gif + '">アニメーションGIFを開く</a>。'
        '</video>'
        '<figcaption>'
        '<p class="figtag"><b>' + tag + '</b> ｜ ' + title + '</p>'
        '<p class="purpose"><span class="lab labP">目的</span> ' + purpose + '</p>'
        '<p class="result"><span class="lab labR">内容</span> ' + result + '</p>'
        + (('<p class="note"><span class="lab labN">注意</span> ' + note + '</p>') if note else '')
        + '<p class="capen">再生できない場合は '
        '<a href="assets/video/' + gif + '">GIF版</a> / '
        '<a href="assets/video/' + mp4 + '">MP4を直接開く</a>。</p>'
        '</figcaption></figure>'
    )


def callout(kind, label, body):
    """Fact / Interpretation / Limitation coloured box."""
    return ('<div class="callout ' + kind + '"><span class="colabel">' + label
            + '</span> ' + body + '</div>')


# --------------------------------------------------------------------------- #
#  Section bodies
# --------------------------------------------------------------------------- #

READ_ME = r'''
<div class="howto">
<p><b>この補足ドキュメントについて。</b> 本ページは修士論文の内容を Web 上で詳しく解説するもので、
学会ポスターに書ききれない <b>数式の完全な定義</b>、<b>略語・記号の説明</b>、<b>図・表・動画</b> を一箇所にまとめています。
数式は本文で用いる記号をすべて <a href="#nomen">用語・略語・記号の定義</a> で説明しており、
このページだけを読めば主要な主張・方法・結果・限界を再構成できることを目標にしています。</p>
<ul>
<li><b>読み方の指針。</b> 各図には「目的（何を確かめる図か）」「結果（事実のみ）」「注意（言えないこと）」を併記しています。</li>
<li><b>証拠の水準。</b> 本研究は単一の予測モデルによる<b>計算実験</b>です。因果・受傷リスク・個人一般化は主張しません
（<a href="#limitations">限界</a>参照）。事実／解釈／仮説の区別は <a href="#appendix-b">付録B</a> にまとめています。</li>
<li><b>数値の来歴。</b> 図中の数値はすべて元の最適化結果（MAT ファイル）から再計算しており、独立監査
（<code>Results/Independent_Audit_20260819/</code>）および自動 QA（23項目 PASS）と一致します。</li>
</ul>
</div>
'''

ABSTRACT = r'''
<p>最高速度スプリントでは、終末遊脚期（<span class="term">terminal swing</span>：接地直前の遊脚後期）に
二関節ハムストリングが伸長位で力を発揮する。この力学的状態はスプリント型ハムストリング損傷を考えるうえで重要であるが、
受傷は多因子性であり、単一の運動学変数から直接推定することはできない。骨盤前傾はハムストリングを伸長させ得る運動学的要因として
注目されているものの、その根拠は固定肢位の標本研究または被験者間の観察的関連に大きく依存している。全身運動が動力学的に再協調する
最高速度スプリントにおいて、速度差を抑えながら接地時骨盤前傾を操作した場合に、筋線維レベルの力学量がどのように応答するかは
明らかでない。</p>

<p><b>目的。</b> 国際水準男子スプリンター1名に基づく三次元予測筋骨格モデルを用い、接地時骨盤前傾量と二関節ハムストリングの
1ストライド最大正規化筋線維長 \(\tilde l^{M}=l^{M}/l^{M}_{o}\) との<b>段階的関係</b>を定量化する。同一モデルの身体特性を保持したまま、
接地時骨盤傾斜のみを等式拘束し、その他の状態・制御変数を再最適化した。</p>

<p><b>方法。</b> 主解析には、内点法ソルバ <span class="term">IPOPT</span> が厳密に <code>Solve_Succeeded</code> を返した
\(N=100\)（時間メッシュ区間数）の8条件を用いた。達成接地時骨盤前傾量 \(A=-q_{\text{pelvis\_tilt}}(0)\) を独立変数とし、
半膜様筋（SM）、半腱様筋（ST）、大腿二頭筋長頭（BFlh）および短頭（BFsh）の1ストライド最大 \(\tilde l^{M}\) を評価した。</p>

<p><b>結果。</b> \(N=100\) の達成前傾量は 1.987–15.987°、速度は 11.7467–11.7978&nbsp;m·s\(^{-1}\)（相対レンジ 0.435%）であった。
二関節3筋の最大 \(\tilde l^{M}\) は前傾量とともに増加し、前傾1°当たりの傾きは SM 0.00678、ST 0.00374、BFlh 0.00538、
8設計点に対する決定係数 \(R^{2}=0.950\text{–}0.961\)、最小→最大前傾で +4.65–9.72% であった。股関節をまたがない BFsh の端点変化は −0.32% であった。
境界条件解析では、骨盤と大腿を共回転させた条件で筋腱単位長は変化せず、大腿の世界座標姿勢を固定した条件で二関節3筋が伸長した。
さらに、筋線維長ペナルティを加えた再最適化により、速度低下 −0.340±0.011% に対して終末遊脚期の筋線維長代理指標を
−5.189±0.077% 低減する候補解が得られた。</p>

<p><b>結論。</b> 本モデルの検討範囲では、接地時骨盤前傾量は二関節ハムストリングの1ストライド最大 \(\tilde l^{M}\) と段階的に関連し、
そのピークは終末遊脚期に生じた。この関係は骨盤角度単独の直接作用ではなく、股関節屈曲および大腿姿勢を含む<b>骨盤–大腿協調</b>の変化として
解釈すべきである。筋損傷、局所組織応力、個人間一般化および介入効果は検証しておらず、結果を受傷因果または予防法として解釈することはできない。</p>
'''

# ---- Nomenclature -------------------------------------------------------- #
NOMEN = r'''
<p>本ドキュメントで用いる略語・記号を以下にまとめる。数式で現れる量はすべてここで定義しており、
本文中でも初出時に簡潔に補足する。正規化量には上付きチルダ（例 \(\tilde l^{M}\)）を用いる。</p>

<h3 id="nomen-anat">解剖・筋（Muscles / anatomy）</h3>
<div class="tablewrap"><table>
<thead><tr><th>略語</th><th>英語</th><th>日本語</th><th>説明</th></tr></thead>
<tbody>
<tr><td>SM</td><td>semimembranosus</td><td>半膜様筋</td><td>二関節ハムストリング（股関節伸展＋膝屈曲）。</td></tr>
<tr><td>ST</td><td>semitendinosus</td><td>半腱様筋</td><td>二関節ハムストリング。</td></tr>
<tr><td>BFlh</td><td>biceps femoris, long head</td><td>大腿二頭筋 長頭</td><td>二関節ハムストリング。</td></tr>
<tr><td>BFsh</td><td>biceps femoris, short head</td><td>大腿二頭筋 短頭</td><td><b>単関節</b>（膝のみをまたぐ）。股関節をまたがない対照筋。</td></tr>
<tr><td>MTU</td><td>muscle–tendon unit</td><td>筋腱単位</td><td>筋線維＋腱を合わせた長さ要素。長さ \(l^{MT}\)。</td></tr>
<tr><td>CE / PE</td><td>contractile / parallel-elastic element</td><td>収縮要素 / 並列弾性要素</td><td>Hill型筋モデルの能動要素と受動要素。</td></tr>
</tbody></table></div>

<h3 id="nomen-len">長さ・角度（Lengths / angles）</h3>
<div class="tablewrap"><table>
<thead><tr><th>記号</th><th>読み</th><th>定義・単位</th></tr></thead>
<tbody>
<tr><td>\(l^{M}\)</td><td>muscle fibre length</td><td>筋線維長 [m]。</td></tr>
<tr><td>\(l^{M}_{o}\)</td><td>optimal fibre length</td><td>至適筋線維長（\(f^{L}\) が最大となる長さ）[m]。</td></tr>
<tr><td>\(\tilde l^{M}\)</td><td>normalized fibre length</td><td><b>主要評価項目</b>。\(\tilde l^{M}=l^{M}/l^{M}_{o}\)（無次元）。\(\tilde l^{M}=1\) が至適。<b>工学ひずみでも超音波筋束長でもない</b>。</td></tr>
<tr><td>\(l^{MT}\)</td><td>MTU length</td><td>筋腱単位長 [m]。一般化座標 \(q\) の多項式で評価。</td></tr>
<tr><td>\(l^{Ts}\)</td><td>tendon slack length</td><td>腱スラック長（腱が力を出し始める自然長）[m]。</td></tr>
<tr><td>\(\tilde l^{T}\)</td><td>normalized tendon length</td><td>正規化腱長（\(l^{Ts}\) 基準、無次元）。</td></tr>
<tr><td>\(\alpha,\ \alpha_{0}\)</td><td>pennation angle</td><td>羽状角、および至適長での羽状角 [rad]。</td></tr>
<tr><td>\(A\)</td><td>anterior pelvic tilt</td><td><b>前傾量</b> \(A=-\dfrac{180}{\pi}q_{\text{pelvis\_tilt}}(0)\) [deg]。モデル座標では前傾が負なので符号を反転し正値で表す。</td></tr>
</tbody></table></div>

<h3 id="nomen-force">力・速度（Forces / velocities）</h3>
<div class="tablewrap"><table>
<thead><tr><th>記号</th><th>読み</th><th>定義・単位</th></tr></thead>
<tbody>
<tr><td>\(F^{M}_{o}\)</td><td>max isometric force</td><td>最大等尺性力 [N]（本実装では全筋で OpenSim 値を2倍）。</td></tr>
<tr><td>\(F^{CE}\)</td><td>contractile-element force</td><td><b>収縮要素力（減衰項 \(0.01\,\tilde v^{M}\) を含む）</b> [N]。生体内で直接測定した張力ではない。</td></tr>
<tr><td>\(F^{pass}\)</td><td>passive fibre force</td><td>受動筋線維力 [N]（並列弾性要素）。</td></tr>
<tr><td>\(F^{T}\)</td><td>tendon force</td><td>腱力 [N]。</td></tr>
<tr><td>\(f^{SE},\ \tilde F^{T}\)</td><td>normalized tendon force</td><td>正規化腱力（状態変数、無次元）。</td></tr>
<tr><td>\(f^{L},\ f^{V}\)</td><td>force–length / force–velocity</td><td>力–長さ係数・力–速度係数（無次元乗数）。</td></tr>
<tr><td>\(v^{M},\ \tilde v^{M}\)</td><td>fibre velocity</td><td>筋線維速度 [m/s] と正規化値。\(v^{M}>0\) を<b>伸張</b>と定義。</td></tr>
<tr><td>\(v^{M}_{\max}\)</td><td>max shortening velocity</td><td>最大筋線維速度 \(=12\,l^{M}_{o}\) [m/s]。</td></tr>
<tr><td>\(v^{MT},\ v^{T}\)</td><td>MTU / tendon velocity</td><td>筋腱単位速度・腱速度 [m/s]。</td></tr>
<tr><td>\(P^{ecc}\)</td><td>eccentric power</td><td>能動伸張性パワー \(\max(F^{CE}v^{M},0)\) [W]（吸収エネルギーの大きさを正で報告）。</td></tr>
<tr><td>\(W^{neg}\)</td><td>negative fibre work</td><td>負の筋線維仕事 \(\int P^{ecc}\,dt\) [J]。</td></tr>
</tbody></table></div>

<h3 id="nomen-opt">最適制御・数値（Optimal control / numerics）</h3>
<div class="tablewrap"><table>
<thead><tr><th>記号・略語</th><th>意味</th></tr></thead>
<tbody>
<tr><td>\(q,\ \dot q,\ \ddot q\)</td><td>一般化座標・速度・加速度（37自由度）。先頭が骨盤6自由度、\(q_{\text{pelvis\_tilt}}\) は骨盤傾斜。</td></tr>
<tr><td>DOF</td><td>degrees of freedom（自由度）。本モデルは 37 DOF。</td></tr>
<tr><td>\(a\)</td><td>筋活性度（92筋、\(0\le a\le 1\)）。</td></tr>
<tr><td>\(N\)</td><td><b>時間メッシュ区間数</b>（被験者数ではない）。各区間に3個の Radau コロケーション点。</td></tr>
<tr><td>\(h,\ T\)</td><td>区間幅 \(h=T/N\)、1歩の総時間 \(T\)（自由変数）。</td></tr>
<tr><td>\(B,\ C,\ D\)</td><td>Radau コロケーションの求積係数・微分係数・区間終端係数。</td></tr>
<tr><td>IPOPT</td><td>Interior Point OPTimizer。非線形計画（NLP）の内点法ソルバ。</td></tr>
<tr><td>MUMPS</td><td>MUltifrontal Massively Parallel Sparse solver。IPOPT 内部の線形ソルバ。</td></tr>
<tr><td>NLP</td><td>nonlinear program（非線形計画問題）。</td></tr>
<tr><td><code>inf_pr</code></td><td>primal infeasibility（制約残差）。採用解は \(\ll 10^{-4}\)。</td></tr>
<tr><td>TD / TDPT</td><td>touchdown（接地）/ touchdown pelvic tilt（接地時骨盤傾斜）条件。実装名 <code>PelvisTD</code>。</td></tr>
<tr><td>HTD / IKTD</td><td>horizontal / inter-knee touchdown distance（接地時水平距離／膝間距離）。元研究の操作変数。</td></tr>
<tr><td>\(w,\ w_J\)</td><td>目的関数の重み。速度–負荷パレートの筋線維長ペナルティ重み。</td></tr>
</tbody></table></div>

<h3 id="nomen-eval">局面・統計・計測（Phases / statistics）</h3>
<div class="tablewrap"><table>
<thead><tr><th>記号・略語</th><th>意味</th></tr></thead>
<tbody>
<tr><td>TS</td><td>terminal swing（終末遊脚期）。筋指標窓は遊脚時間の最後25%、境界条件動画窓は1歩の最後15%（別定義）。</td></tr>
<tr><td>early stance</td><td>早期立脚期（接地時間の前半50%）。</td></tr>
<tr><td>BW</td><td>body weight（体重）。\(BW=72.17\times 9.80665\) N。</td></tr>
<tr><td>GRF</td><td>ground reaction force（床反力）。</td></tr>
<tr><td>EMG</td><td>electromyography（筋電図）。本データセットには被験者実測なし。</td></tr>
<tr><td>IK</td><td>inverse kinematics（逆運動学）。実験由来の関節角。</td></tr>
<tr><td>\(R^{2}\)</td><td>決定係数。8設計点に対する直線近似の適合度（母集団一般化可能性ではない）。</td></tr>
<tr><td>SD / IQR</td><td>標準偏差／四分位範囲。8<b>設計条件</b>の記述統計であり標本統計ではない。</td></tr>
<tr><td>tree-rigid / femur-fixed / adaptive</td><td>境界条件解析の3設定（本文 §2.17・§3.7 で定義）。</td></tr>
</tbody></table></div>

<div class="callout warn"><span class="colabel">重要</span>
\(N=50\) と \(N=100\) は<b>被験者数ではなく時間メッシュ区間数</b>である。各区間に3個の Radau 点があり、\(N\) を増やすことは
時間離散化誤差を調べる感度解析であって、標本数を増やすことではない。同様に8条件は同一モデルの<b>決定論的設計点</b>であり、
独立な生物学的反復ではない。</div>
'''

# ---- Introduction -------------------------------------------------------- #
INTRO = r'''
<h3 id="intro-1">1.1 高速走行時のハムストリング損傷は依然として競技医学上の課題である</h3>
<p>ハムストリング損傷は、スプリントを含む競技で頻度と再発率の高い外傷であり、競技離脱およびパフォーマンス低下の主要因となる。
UEFA Elite Club Injury Study では、欧州男子プロサッカー54チーム3909名を21シーズン追跡した結果、2636件のハムストリング損傷が記録され、
全損傷に占める割合は 2001/02 シーズンの 12% から 2021/22 シーズンの 24% へ増加した<a class="cref" href="#ref1">[1]</a>。
全離脱日数に占める割合も同期間に 10% から 20% へ増加しており、予防プログラムが普及した現在も競技現場における相対的負担は軽減していない。</p>
<p>受傷映像研究は、高速走行が重要な発生状況の一つであることを示す。ドイツ男子プロサッカーの52例を対象とした系統的映像解析では、
25例（48%）がスプリント関連であり、これらはすべて直線加速または高速走行中に発生していた<a class="cref" href="#ref2">[2]</a>。
ただしハムストリング損傷は、筋腱形態、既往歴、疲労、神経筋制御、走速度および外部環境が相互に関与する<b>多因子性</b>事象である。
したがって、特定姿勢を直ちに受傷原因とみなすのではなく、その姿勢がどのような筋力学的状態と対応するかを段階的に検証する必要がある。</p>

<h3 id="intro-2">1.2 終末遊脚期の二関節ハムストリングは伸長と力発揮が同時に生じる</h3>
<p>Thelen らはトレッドミルスプリントを解析し、SM・ST・BFlh の筋腱単位長が終末遊脚期に最大となり、直立位に対してそれぞれ
7.4%、8.1%、9.5% 長くなると報告した<a class="cref" href="#ref3">[3]</a>。Chumanov らは走速度の上昇に伴い、二関節ハムストリングの
伸長・負荷・負の仕事が増加することを示した<a class="cref" href="#ref4">[4]</a>。</p>
<p>Schache らは筋別の応答が一様でないことを明らかにした。最大ひずみは BFlh、伸張速度は ST、力および負の仕事は SM で大きかった
<a class="cref" href="#ref5">[5]</a>。走速度に対する伸長量・伸張速度・活性化後伸長の応答も筋間で異なる<a class="cref" href="#ref6">[6]</a>。
これらは「ハムストリング負荷」を単一量として扱うことが適切でないことを示す。筋線維長、収縮要素力、受動筋線維力、腱力および
負の筋線維仕事は異なる意味を持つため、<b>筋別かつ指標別</b>に評価する必要がある。</p>

<h3 id="intro-3">1.3 同じ運動学でも筋腱形態によって力学的意味は異なり得る</h3>
<p>Timmins らはエリート男子サッカー選手152名を前向きに追跡し、BFlh の短い筋束長および低い遠心性膝屈曲力が、その後の
ハムストリング損傷と関連したと報告した<a class="cref" href="#ref7">[7]</a>。同一の関節運動でも、至適筋線維長・腱コンプライアンス・
筋力が異なれば、正規化筋線維長や力発揮状態が異なり得る。したがって集団共通の単一「危険角度」を想定する前に、同一の身体特性を持つ
モデル内で運動学から筋力学へ至る経路を明確にする必要がある。</p>

<h3 id="intro-4">1.4 骨盤前傾はハムストリング伸長の候補要因だが動的スプリントでの作用は未確定</h3>
<p>SM・ST・BFlh は股関節と膝関節をまたぐため、骨盤と大腿の相対配置の影響を受ける。Mendiguchia らは新鮮凍結標本7体で、
大腿骨・脛骨を固定して骨盤前傾を増加させると二関節ハムストリングの組織伸長が増加することを示した<a class="cref" href="#ref8">[8]</a>。
しかし固定肢位の標本と最高速度スプリントでは境界条件が異なる。骨盤と大腿が同方向に共回転すれば股関節相対角は変化せず、
骨盤の絶対角度が変化しても筋腱単位長はほとんど変化しない可能性がある。実際のスプリントでは骨盤・体幹・股・膝・接地が相互に
再協調するため、骨盤前傾の力学的意味は<b>骨盤–大腿協調</b>として検討しなければならない。</p>

<h3 id="intro-5">1.5 観察研究と介入研究の間には運動学から筋力学へ至る説明の空白がある</h3>
<p>Bramah らはエリート男子サッカー選手126名を6か月追跡し、Sprint Mechanics Assessment Score が1点高いごとに、新規スプリント関連
ハムストリング損傷の調整発生率比が 1.33（95%CI 1.01–1.76）となることを報告した<a class="cref" href="#ref9">[9]</a>。一方 Mendiguchia らは
6週間の複合介入後に最大速度走の骨盤・下肢運動学が変化し得ることを示した<a class="cref" href="#ref10">[10]</a>。走動作が将来受傷と関連し、
介入で変化し得ることは示されたが、観察された骨盤運動が二関節ハムストリングの筋線維長や力にどう結び付くかは直接検証されていない。</p>

<h3 id="intro-6">1.6 予測筋骨格シミュレーションは同一個体内の仮想的運動学操作を可能にする</h3>
<p>実走者の被験者間比較では、骨盤傾斜が異なる者は走速度・筋力・体格・筋腱形態・他の走技術も異なる。予測筋骨格シミュレーションは、
同一モデルの身体特性を保持しながら特定条件を拘束し、動力学・接触・筋平衡・周期性を満たす全身運動を再最適化できる。
Haralabidis らは三次元全身筋骨格モデルと直接コロケーション法によるスプリントシミュレーションを構築し<a class="cref" href="#ref11">[11]</a>、
その後、コーチングで用いられる接地時水平距離（HTD）および接地時膝間距離（IKTD）を基準解から段階的に操作して、その他の座標・制御を
再最適化した<a class="cref" href="#ref12">[12]</a>。HTD の変更は最高速度に意味のある変化をもたらした一方、検討範囲の IKTD 変更に対して
速度は比較的鈍感であった。同じ系譜で Lin と Pandy は筋力・筋束長・最大短縮速度・腱コンプライアンスを段階的に操作し、最高走速度に対する
筋腱特性の感度を検討した<a class="cref" href="#ref13">[13]</a>。本研究はこの設計思想を、パフォーマンスから<b>筋線維力学</b>へ発展させる。</p>

<h3 id="intro-7">1.7 残された研究課題</h3>
<p>先行研究から、①終末遊脚期に二関節ハムが伸長位で力を発揮する、②固定大腿に対する骨盤前傾がハム組織を伸長させる、
③予測シミュレーションで同一モデル内の接地変数を段階的に操作できる、ことは示されている。しかし、最高速度近傍の全身動作を再最適化し、
速度差を限定したうえで、接地時骨盤前傾と<b>筋別</b>ハムストリング力学との段階的関係を検討した研究は不足している。</p>

<h3 id="intro-8">1.8 目的および仮説</h3>
<p><b>主目的。</b> 最高速度近傍の予測筋骨格シミュレーションにおいて、達成接地時骨盤前傾量と二関節ハムストリングの1ストライド最大
正規化筋線維長との段階的関係を定量化する。<b>副次目的。</b> 境界条件解析で骨盤–大腿配置と筋腱単位長変化の関係を分解し、筋線維長ペナルティを
加えた再最適化で速度と負荷代理指標の交換関係を探索する。</p>
<p><b>主要仮説。</b> 達成速度を基準の ±1% 以内に保った条件で、接地時骨盤前傾量が大きいほど SM・ST・BFlh の1ストライド最大 \(\tilde l^{M}\)
が増加し、股関節をまたがない BFsh の変化は相対的に小さい。<b>副次仮説。</b> 前傾増加に伴う筋長変化は骨盤回転単独ではなく大腿姿勢・股関節屈曲と
対応し、筋線維長代理指標を目的関数へ加えることで、速度低下 0.5% 以内かつ代理指標低下 3% 以上の候補解が得られる。</p>
''' + fig(
    "fig-1", "Fig1_study_logic.png", "図1 / Figure 1",
    "研究ギャップと検証の連鎖 / Research gap and validation chain",
    "観察研究の交絡（個体差・共変動学）を、単一モデルで接地時骨盤傾斜のみ拘束し全身再最適化することで切り分ける枠組みと、"
    "主解析（どのように関連するか）→ 機序分解（どの座標関係で生じるか）→ 最適化（代理指標を低減できるか）の解析連鎖を示す。",
    "概念図。3つの解析が順に「関連の定量化」「機序の限定」「候補動作の生成」を担う。",
    "この図は研究の論理構造であり、実測データではない。",
    "Schematic of the research logic: observational confounds are isolated by constraining only touchdown pelvis tilt in one "
    "model and re-optimizing the whole body; the three analyses chain from association to mechanism to candidate-motion generation.")

# ---- Methods ------------------------------------------------------------- #
METHODS_1 = r'''
<h3 id="m-1">2.1 研究デザイン</h3>
<p>本研究は、国際水準男子スプリンター1名に基づく筋骨格モデルを対象とした<b>計算実験</b>である。Haralabidis ら
<a class="cref" href="#ref12">[12]</a>の予測シミュレーション設計を基盤とし、接地時の一つの運動学変数を拘束したうえで、
その他の状態変数および制御変数を再最適化する、仮想的な同一個体内比較を行った。主解析は接地時骨盤傾斜を独立変数とする
\(N=100\) の8条件比較、機序解析は3種類の境界条件比較、発展解析は負荷ペナルティ重みを独立変数とする速度–負荷最適化で構成した。</p>
<div class="tablewrap"><table>
<thead><tr><th>要素</th><th>定義</th></tr></thead>
<tbody>
<tr><td>対象</td><td>国際水準男子スプリンター1名に基づく全身筋骨格モデル（24歳・身長1.79&nbsp;m・体重72.2&nbsp;kg・100&nbsp;m自己記録10.33&nbsp;s）</td></tr>
<tr><td>主条件</td><td>ソルバが厳密に <code>Solve_Succeeded</code> を返した接地時骨盤傾斜8条件、\(N=50\) および \(N=100\)</td></tr>
<tr><td>独立変数</td><td>達成接地時骨盤前傾量 \(A=-q_{\text{pelvis\_tilt}}(0)\)（1.987–15.987°）</td></tr>
<tr><td>主要従属変数</td><td>筋別1ストライド最大正規化筋線維長 \(\tilde l^{M}\)</td></tr>
<tr><td>副次従属変数</td><td>収縮要素力 \(F^{CE}\)（減衰項含む）、受動筋線維力 \(F^{pass}\)、腱力 \(F^{T}\)、伸張速度、伸張性パワー \(P^{ecc}\)、負の筋線維仕事 \(W^{neg}\)</td></tr>
<tr><td>設計確認</td><td>達成速度、solver status、制約残差 <code>inf_pr</code>、メッシュ \(N=50/100\)</td></tr>
<tr><td>媒介候補</td><td>接地・最大股関節屈曲、大腿骨世界座標姿勢</td></tr>
<tr><td>解剖学的対照筋</td><td>股関節をまたがない大腿二頭筋短頭（BFsh）</td></tr>
</tbody></table></div>

<h3 id="m-2">2.2 モデルと最適制御</h3>
<p>モデルは20剛体・37自由度・左右合計92筋腱単位・上肢トルクアクチュエータ・足部接触要素・空気抵抗から構成され、上記スプリンターの
身体寸法にスケーリングされた<a class="cref" href="#ref12">[12]</a>。筋腱単位は Hill 型モデルで表現した。1歩を左右対称性で表現し、平均速度を
高めつつ、加速度・筋活動・筋活動変化・腱力変化・予備アクチュエータ・上肢制御などを正則化する目的関数を、直接コロケーション法で解いた。
時間離散化は3次 Radau コロケーションであり、\(N=50\) および \(N=100\) はメッシュ区間数を表す。基準モデルの外部妥当性を図4に示す。</p>
''' + fig(
    "fig-4", "Fig4_baseline_validation.png", "図4 / Figure 4",
    "基準シミュレーション（Nominal \\(N=100\\)）の妥当性 / Baseline validity",
    "内部筋力学を論じる前提として、基準解が被験者本人の最高速度スプリントの<b>外部特徴</b>をどの程度再現するかを確認する。",
    "股・膝・足の関節角は形状一致良好（相関 \\(r=0.90\\text{–}0.97\\)、系統オフセットあり）。"
    "pelvis_tilt は raw IK とモデルで規約・姿勢が異なり（接地 +5.0° 対 −8.0°）、オフセット除去後の形状相関 \\(r=-0.31\\)・RMSE 5.9°。"
    "被験者の実験 GRF・EMG は本データに含まれず、GRF・活動は<b>シミュレーションのみ</b>（鉛直ピーク 5.9 BW は接触モデル由来で過大）。",
    "外部一致は内部の筋線維長・力の妥当性を保証しない。pelvis_tilt の規約差は隠さず明示している。",
    "Kinematic shape agreement (hip/knee/ankle r=0.90–0.97) with systematic offsets; pelvis_tilt differs by a "
    "convention/posture offset (flagged, not silently aligned). GRF and activations are simulation-only.")

METHODS_2 = r'''
<h3 id="m-3">2.3 接地時骨盤傾斜8条件</h3>
<p><code>PelvisTD</code> および <code>PelvisTDwide</code> 系列から、solver status が厳密に <code>Solve_Succeeded</code> で、
要求オフセットごとに制約残差が最小の条件を選択した。主解析は要求角度ではなく、<b>実際に達成した</b>接地時骨盤傾斜を横軸とした。
\(N=100\) では8条件すべてが速度誤差 ±1% 以内であった。速度誤差は各条件の Nominal 参照値に対する値であり、条件選択後に速度で
再選別したものではない。</p>
<div class="tablewrap"><table class="small">
<thead><tr><th>条件</th><th>要求offset</th><th>達成前傾量 \(A\)</th><th>速度 [m/s]</th><th>速度誤差</th><th>制約残差</th><th>solver</th></tr></thead>
<tbody>
<tr><td>PelvisTDwide_m8</td><td>−8°</td><td>15.987°</td><td>11.74666</td><td>−0.743%</td><td>7.87e−9</td><td>Solve_Succeeded</td></tr>
<tr><td>PelvisTDwide_m6</td><td>−6°</td><td>13.987°</td><td>11.76596</td><td>−0.580%</td><td>1.36e−8</td><td>Solve_Succeeded</td></tr>
<tr><td>PelvisTDwide_m4</td><td>−4°</td><td>11.987°</td><td>11.79676</td><td>−0.319%</td><td>5.50e−8</td><td>Solve_Succeeded</td></tr>
<tr><td>PelvisTDwide_m2</td><td>−2°</td><td>9.987°</td><td>11.79784</td><td>−0.310%</td><td>9.18e−8</td><td>Solve_Succeeded</td></tr>
<tr><td>PelvisTDwide_p0</td><td>+0°</td><td>7.987°</td><td>11.79239</td><td>−0.356%</td><td>1.30e−7</td><td>Solve_Succeeded</td></tr>
<tr><td>PelvisTDwide_p2</td><td>+2°</td><td>5.987°</td><td>11.78729</td><td>−0.399%</td><td>5.74e−8</td><td>Solve_Succeeded</td></tr>
<tr><td>PelvisTDwide_p4</td><td>+4°</td><td>3.987°</td><td>11.76106</td><td>−0.621%</td><td>2.28e−8</td><td>Solve_Succeeded</td></tr>
<tr><td>PelvisTDwide_p6</td><td>+6°</td><td>1.987°</td><td>11.78850</td><td>−0.389%</td><td>6.54e−9</td><td>Solve_Succeeded</td></tr>
</tbody></table></div>
<div class="tablewrap"><table class="small">
<thead><tr><th>記述統計（\(N=100\)）</th><th>値</th></tr></thead>
<tbody>
<tr><td>条件数</td><td>8</td></tr>
<tr><td>達成前傾量</td><td>1.987–15.987°</td></tr>
<tr><td>速度 平均±SD</td><td>11.7796±0.0191 m/s</td></tr>
<tr><td>速度 中央値 [IQR]</td><td>11.7879 [11.7647, 11.7935] m/s</td></tr>
<tr><td>速度範囲 / 相対レンジ</td><td>11.7467–11.7978 m/s / 0.435%</td></tr>
</tbody></table></div>
<p class="fine">表中の平均・SD・中央値・IQR は8つの<b>設計条件</b>を要約する記述統計であり、8名の被験者から推定した標本統計ではない。</p>
''' + vid(
    "vid-td", "pelvic_td_sidebyside.mp4", "pelvic_td_sidebyside.gif",
    "動画1 / Video 1", "接地時骨盤傾斜条件の筋骨格アニメーション / Musculoskeletal animation of touchdown pelvis-tilt conditions",
    "接地時骨盤前傾を変えた条件間で、全身動作とハムストリング経路がどう再協調するかを視覚的に示す。",
    "前傾が異なる条件を並べて再生した3次元筋骨格アニメーション（OpenSim ジオメトリ）。骨盤・股関節・大腿の姿勢差と、"
    "それに伴う二関節ハムストリング経路長の変化を確認できる。",
    "可視化は解釈補助であり定量指標ではない。定量値は図2–3・図5を参照。")

# ----- Methods: mechanics / statistics text ------------------------------- #
METHODS_3 = r'''
<h3 id="m-4">2.4 1ストライド再構成と局面</h3>
<p>保存された1歩の右脚信号に、左右対称性で対応する左脚信号を連結し、基準右脚の1ストライドを再構成した。早期立脚期は接地時間の前半50%、
終末遊脚期は次回接地前の遊脚時間最後25%とした。接地は右床反力3軸のうち peak-to-peak 範囲が最大の軸を鉛直候補とみなし、その値が
体重の5%を超える区間とした。なお、境界条件動画解析の terminal swing は別定義で、1歩の最後15%である。両者を同じ窓として扱っていない。</p>

<h3 id="m-5">2.5 力学的負荷代理指標</h3>
<p>正規化筋線維長は \(\tilde l^{M}=l^{M}/l^{M}_{o}\) である（工学ひずみではない）。物理筋線維速度は \(v^{M}=\tilde v^{M}\,v^{M}_{\max}\) とし、
\(v^{M}>0\) を伸張と定義した。能動伸張性パワーは \(\max(F^{CE}v^{M},0)\) [W]、負の能動筋線維仕事は実時間上の積分
\(\int \max(F^{CE}v^{M},0)\,dt\) [J] とした。保存された時刻節点は非一様であるため、すべての積分を実節点に対する台形則で計算した。
正規化筋線維長・収縮要素力・受動筋線維力・腱力・負の筋線維仕事は相互に関連するが、同一の力学量ではない。したがって各指標を個別に算出し、
<b>筋別・局面別</b>に評価した。</p>

<h3 id="m-6">2.6 統計・数値解析</h3>
<p>前傾量と各指標の関係は、最小二乗直線の傾き、決定係数 \(R^{2}\)、Spearman 順位相関、および端点変化で記述した。主要な効果量は
「前傾1°当たりの傾き」と「最小前傾条件を分母とする端点変化率」である。\(N=8\) はシミュレーション条件数であり被験者標本ではない。
そのため p 値および母集団推論としての 95% 信頼区間を主要結果として用いない。\(R^{2}\) も母集団一般化可能性ではなく、検討した8設計点における
直線近似の適合度を示す。主解析は \(N=100\) の8条件とし、\(N=50\) は方向の一致を確認する補助解析と位置づけた。</p>
<p>残存する速度差による交絡可能性を調べるため、\(N=100\) について探索的に \(y=\beta_{0}+\beta_{A}A+\beta_{V}v\)（\(A\)：達成前傾量、
\(v\)：速度）を当てはめた。また各条件を1点ずつ除外した8通りの単回帰から、前傾量係数の範囲を求めた。これらは事後的な感度解析であり、
\(n=8\) の設計点から母集団効果や因果効果を推定する解析ではない。\(N=50\) と \(N=100\) の条件系列は完全には同一でないため
（\(N=50\) は −8/−6/−4° に wide 系列、−2〜+6° に standard 系列、\(N=100\) は全8条件に wide 系列）、両者の差には時間離散化だけでなく
探索境界系列の差も含まれ得る。本稿ではこれを「解像度をまたぐ方向的一致の確認」として扱う。</p>

<h3 id="m-7">2.7 境界条件分解</h3>
<p><b>tree-rigid</b> では骨盤角度のみを変更し股関節相対角を固定したため、大腿骨が骨盤と共回転する。<b>femur-fixed</b> では骨盤角度を
変更しつつ股関節屈曲を補正し、大腿骨の世界座標姿勢を名目上固定した。<b>adaptive</b> は実際に再最適化された PelvisTDwide_m8 解である。
静的解析は前傾 0–25°、動作解析は名目 −8° オフセットを対象とした。</p>

<h3 id="m-8">2.8 速度–負荷パレート</h3>
<p>二関節ハムストリング左右6筋の \(\tilde l^{M}-1\) の正部分を滑らかな hinge で二乗し、1歩で積分した項に重み \(w_J(13)\) を与えた。
報告軸は目的関数値そのものではなく、事後計算した二関節3筋の終末遊脚期窓内ピーク \(\tilde l^{M}\) 平均である。\(N=100\) では
\(w=0,\,0.05,\,0.10,\,0.20\) を解き、候補 \(w=0.10\) は forward・Nominal 初期値・\(w=0.20\) からの backward の3ウォームスタート経路で確認した。
候補基準は計算前に文書化した「速度低下 0.5% 以内、代理指標低下 3% 以上」である。3解は独立標本ではなく、局所解の初期値感度をみる反復である。</p>
'''

# ----- Methods: full mathematical implementation (2.9-2.17) --------------- #
METHODS_MATH = r'''
<h3 id="m-9">2.9 数理モデルおよび解析実装</h3>
<p>本節では、論文中の記号を実装（公開コード）へ追跡できるように、式・変数・コード位置を対応づける。モデルは37自由度の三次元全身剛体系で、
左右合計92筋腱単位を含む。一般化座標 \(q\in\mathbb{R}^{37}\) の先頭6成分は骨盤の傾斜・側屈・回旋・3方向並進、7–20成分は左右下肢、
21–23成分は体幹、24–37成分は左右上肢である。下肢筋腱長とモーメントアームは、OpenSim モデルから作成された多項式近似により評価される。</p>
<p>多項式で得た筋腱単位長を \(l^{MT}(q)\) とすると、モーメントアーム \(r_i\) と筋腱単位速度 \(v^{MT}\) は次の関係にある。</p>
\[ r_i(q) = -\frac{\partial l^{MT}(q)}{\partial q_i},\qquad
   v^{MT}(q,\dot q) = \sum_i \frac{\partial l^{MT}(q)}{\partial q_i}\,\dot q_i = -\sum_i r_i(q)\,\dot q_i. \]
<p>ここで \(r_i\) は座標 \(q_i\) に対するモーメントアーム、\(\dot q_i\) は一般化速度である。実装では、負の長さ微分を \(\mathrm{dM}\) に格納し、
\(v^{MT}\) へ \(-\mathrm{dM}\cdot\dot q\) を加える処理として表現されている。</p>
<div class="tablewrap"><table class="small">
<thead><tr><th>数理要素</th><th>記号・定義</th><th>実装箇所</th></tr></thead>
<tbody>
<tr><td>一般化座標</td><td>\(q\in\mathbb{R}^{37}\)、一般化速度 \(\dot q\in\mathbb{R}^{37}\)</td><td>MainFunctions/main_pred_sim_sprinting.m（Joint Indices, 約664–738行）</td></tr>
<tr><td>筋状態</td><td>活性度 \(a\in\mathbb{R}^{92}\)、正規化腱力 \(\tilde F^{T}\in\mathbb{R}^{92}\)</td><td>同 buildNLP（約1962行以降）</td></tr>
<tr><td>骨格制御</td><td>一般化加速度 \(\ddot q\in\mathbb{R}^{37}\)</td><td>同（約2300行）</td></tr>
<tr><td>筋制御</td><td>\(da/dt\in\mathbb{R}^{92}\)、\(d\tilde F^{T}/dt\in\mathbb{R}^{92}\)</td><td>同（約2300–2315行）</td></tr>
<tr><td>時間離散化</td><td>3次 Radau、\(N=50\) または \(100\)、区間幅 \(h=T/N\)</td><td>同（795–798, 1032–1040行）; CollocationScheme.m</td></tr>
<tr><td>接地時骨盤制約</td><td>\(q_{\text{pelvis\_tilt}}(0)=q_{\text{Nominal}}(0)+\text{offset}\times\pi/180\)</td><td>同（2724–2737行）</td></tr>
<tr><td>平均速度</td><td>\(\bar v=(q_{tx}(T)-q_{tx}(0))/T\)</td><td>同（1047, 3094行）</td></tr>
<tr><td>筋力学</td><td>Hill 型、腱力を状態とする平衡式</td><td>MuscleModel/ForceEquilibrium_FtildeState_all_tendon_M.m</td></tr>
<tr><td>解析指標</td><td>筋線維長・力・物理速度・仕事・局面ピーク</td><td>analysis/validation/ham_load_metrics.py</td></tr>
</tbody></table></div>

<h3 id="m-10">2.10 Radau 直接コロケーションによる最適制御問題</h3>
<p>1歩の総時間 \(T\) は自由変数で、実験的1歩時間の ±15% に制限される。各メッシュ区間 \(k\) を幅 \(h=T/N\) とし、3次 Radau 点 \(\tau_j\) で
状態と制御を評価する。Lagrange 基底から、微分係数 \(C\)、区間終端係数 \(D\)、求積係数 \(B\) を生成する。状態 \(X\) について、
コロケーション条件・連続条件・積分近似は概念的に次式である。</p>
\[ \sum_r C_{r,j}\,X_{k,r} = h\, f\!\left(X_{k,j},\,U_{k,j}\right),\qquad
   X_{k+1,0} = \sum_r D_r\,X_{k,r},\qquad
   \int_0^T L\,dt \approx \sum_k \sum_j h\,B_j\,L\!\left(X_{k,j},U_{k,j}\right). \]
<p>ここで \(X\) は状態、\(U\) は制御、\(f\) は状態方程式の右辺、\(L\) は目的関数の被積分項である。実装では骨格状態 \(X=[q;\dot q]\)、
筋活性度 \(a\)、正規化腱力 \(\tilde F^{T}\)、上肢活性度に同じ構造の連続条件を課す。骨格状態の右辺は \([\dot q;\ddot q]\)、筋活性度と腱力の右辺は
それぞれ \(da/dt\) と \(d\tilde F^{T}/dt\) である。筋収縮については後述の Hill 平衡残差を各コロケーション点で 0 にする。左右半歩の周期性は、
最終点で左右の下肢・上肢・筋状態・制御を入れ替える対称条件として実装される。</p>
<div class="callout warn"><span class="colabel">重要</span>
\(N=50\) と \(N=100\) は被験者数ではなく<b>時間メッシュ区間数</b>である。各区間に3個の Radau コロケーション点があるため、\(N\) を増やすことは
時間離散化誤差を調べる感度解析であり、標本数を増やすことではない。</div>

<h3 id="m-11">2.11 目的関数</h3>
<p>基準最適化は、平均速度を最大化しながら、数値的・生理学的に極端な制御を二乗正則化する。最小化問題として書くと次の形である。</p>
\[ J_{\text{base}} = \int_0^T\!\Big[\,0.05\,J_{\text{acc}} + 0.10\,J_{\text{act}} + 0.01\,J_{\text{dact}}
   + 0.00\,J_{FT} + 0.01\,J_{dFT} + 0.01\,J_{\text{res}} + 0.10\,J_{\text{arm}}\,\Big]\,dt \;-\; 10.0\,\frac{\Delta x}{T}. \]
<p>各 \(J_z\) は原則として、コード内で定義された範囲 \(r_i\) を用いる二乗和 \(J_z=\sum_i (z_i/r_i)^2\) である。項の意味は
\(J_{\text{acc}}\)：加速度、\(J_{\text{act}}\)：筋活動、\(J_{\text{dact}}\)：筋活動変化、\(J_{FT}\)：腱力、\(J_{dFT}\)：腱力変化、
\(J_{\text{res}}\)：予備アクチュエータ、\(J_{\text{arm}}\)：上肢制御であり、\(\Delta x/T\) は平均速度（負符号で最大化）。骨盤・下肢・上肢の
実験運動学追跡項は本予測条件では 0 であり、参照運動学に追従させるのではなく、初期姿勢範囲・動力学・接触・周期性などの制約下で速度を予測する。
IPOPT 設定は limited-memory Hessian、adaptive barrier、線形ソルバ MUMPS、収束許容 \(\text{tol}=10^{-5}\)、最大50000反復である。</p>
<p>速度–負荷パレートでは、左右の SM・ST・BFlh の6筋について、\(\tilde l^{M}\) が 1 を超える部分を滑らかな片側関数で罰する。</p>
\[ \operatorname{smoothpos}(z;\varepsilon)=\tfrac12\!\left(z+\sqrt{z^2+\varepsilon^2}\right),\qquad
   J_{\text{len}} = 10^{4}\,w \sum_k\sum_j h\,B_j \!\!\sum_{m\in H_{bi}}\! \operatorname{smoothpos}\!\left(\tilde l^{M}_m-1;\,10^{-3}\right)^{2},\qquad
   J_{\text{total}} = J_{\text{base}} + J_{\text{len}}. \]
<p>ここで \(\operatorname{smoothpos}\) は正部分の滑らか近似、\(\varepsilon=10^{-3}\)、\(H_{bi}\) は二関節ハム6筋の集合、\(w\) はペナルティ重み
（条件名 <code>wXXXX</code> は \(w=\text{XXXX}/1000\)）。最適化が直接最小化するのは<b>時間積分された滑らかな二乗超過量</b>である一方、結果図の縦軸は
事後計算した「二関節3筋の終末遊脚期窓内ピーク \(\tilde l^{M}\) 平均」である。両者は関連するが同一ではない。</p>

<h3 id="m-12">2.12 Hill 型筋モデルの式</h3>
<p>各筋について、最大等尺性力 \(F^{M}_{o}\)、至適筋線維長 \(l^{M}_{o}\)、腱スラック長 \(l^{Ts}\)、至適羽状角 \(\alpha_0\)、最大筋線維速度
\(v^{M}_{\max}\) を用いる。本実装では \(F^{M}_{o}\) を全筋で2倍、\(v^{M}_{\max}=12\,l^{M}_{o}\)、腱剛性 \(a^{T}=35\)、\(\text{shift}=0\) とする。
正規化腱力 \(f^{SE}=\tilde F^{T}\) から正規化腱長を逆算する。</p>
\[ \tilde l^{T} = \frac{\ln\!\big[5\,(f^{SE}+0.25-\text{shift})\big]}{a^{T}} + 0.995. \]
<p>一定筋厚を仮定する羽状筋幾何から筋線維長・正規化長・羽状角余弦を求める。</p>
\[ l^{M} = \sqrt{\big(l^{M}_{o}\sin\alpha_0\big)^2 + \big(l^{MT}-l^{Ts}\tilde l^{T}\big)^2},\qquad
   \tilde l^{M} = \frac{l^{M}}{l^{M}_{o}},\qquad
   \cos\alpha = \frac{l^{MT}-l^{Ts}\tilde l^{T}}{l^{M}}. \]
<p>腱速度 \(v^{T}\) と筋線維速度 \(v^{M}\)（および正規化 \(\tilde v^{M}\)）は次式である。</p>
\[ v^{T} = \frac{l^{Ts}\,(df^{SE}/dt)}{0.2\,a^{T}\exp\!\big[a^{T}(\tilde l^{T}-0.995)\big]},\qquad
   v^{M} = \big(v^{MT}-v^{T}\big)\cos\alpha,\qquad
   \tilde v^{M} = \frac{v^{M}}{v^{M}_{\max}}. \]
<p>収縮要素の力–長さ曲線 \(f^{L}\) は3個の Gauss 型項の和、力–速度曲線 \(f^{V}\) は asinh 型の滑らかな式で、係数 \(b^{1..4}_i\)（Faparam）と
\(e_{1..4}\)（Fvparam）から計算される。収縮要素力 \(F^{CE}\) は活性化 \(a\) に加え、減衰項 \(0.01\,\tilde v^{M}\) を含む。</p>
\[ f^{L} = \sum_{i=1}^{3} b^{1}_i\,\exp\!\left\{-0.5\left[\frac{\tilde l^{M}-b^{2}_i}{\,b^{3}_i+b^{4}_i\,\tilde l^{M}\,}\right]^{2}\right\},\qquad
   f^{V} = e_1\,\ln\!\left[(e_2\tilde v^{M}+e_3)+\sqrt{(e_2\tilde v^{M}+e_3)^2+1}\right] + e_4, \]
\[ F^{CE} = F^{M}_{o}\,\big[\,a\,f^{L}f^{V} + 0.01\,\tilde v^{M}\,\big]. \]
<p>受動力–長さ曲線 \(f^{PE}\)、受動力 \(F^{pass}\)、腱力 \(F^{T}\) は次式である（\(F^{pparam}_{1,2}\) はモデル係数）。</p>
\[ f^{PE} = \frac{\big[\exp\!\big(4(\tilde l^{M}-1)/0.6\big)-1\big]-F^{pparam}_1}{F^{pparam}_2},\qquad
   F^{pass} = F^{M}_{o}\,f^{PE},\qquad F^{T} = F^{M}_{o}\,f^{SE}. \]
<p>筋線維方向の力を腱方向へ投影した平衡残差は次式であり、各コロケーション点で 0 に制約される。</p>
\[ \mathrm{err} = \left(\frac{F^{CE}}{F^{M}_{o}} + \frac{F^{pass}}{F^{M}_{o}}\right)\cos\alpha - f^{SE} = 0. \]
<div class="callout interp"><span class="colabel">用語の正確さ</span>
コード上の \(F^{CE}\) は、活性化に依存する \(a\,f^{L}f^{V}\) だけでなく減衰項 \(0.01\,\tilde v^{M}\) を含む。このため本稿の「能動筋線維力」は、
より厳密には「<b>収縮要素力（減衰項を含む）</b>」であり、生体内で直接測定した筋張力ではない。</div>

<h3 id="m-13">2.13 接地時骨盤傾斜の操作</h3>
<p>モデル座標では \(q_{\text{pelvis\_tilt}}\) が負になるほど前傾が大きい。本稿では直感的な正値として前傾量 \(A\) を定義する。</p>
\[ A\,[\deg] = -\frac{180}{\pi}\,q_{\text{pelvis\_tilt}}(0). \]
<p>TDPT 条件は接地初期点だけに次の等式を加える（\(\text{offset}\) は要求オフセット [deg]）。</p>
\[ q_{\text{pelvis\_tilt}}(0) = q_{\text{pelvis\_tilt,Nominal}}(0) + \text{offset}\times\frac{\pi}{180}. \]
<p><code>PelvisTDwide</code> は操作式を変えず、骨盤傾斜の初期姿勢照合窓と座標範囲を ±25° まで緩和する。したがって standard と wide の違いは
「異なる介入」ではなく、前傾側の解を座標境界で人工的に遮断しないための<b>実行可能領域の拡張</b>である。他の時点の骨盤傾斜・股・膝・体幹・接触・
筋活動は再最適化される。主解析条件は、要求 offset ごとに制約残差 <code>inf_pr</code> が最小の1行を選び、横軸には達成接地角度を用いる。</p>

<h3 id="m-14">2.14 1ストライド再構成と局面定義の式</h3>
<p>保存解は左右対称な1歩である。基準を右脚とし、右脚信号 \(x_R(t)\) の後ろに同じ1歩の左脚信号 \(x_L(t)\) を時間 \(T\) だけ移して連結する。</p>
\[ x_{\text{stride}}(t) = \begin{cases} x_R(t), & 0\le t\le T,\\[2pt] x_L(t-T), & T< t\le 2T. \end{cases} \]
<p>筋線維速度だけは各脚で \(v^{M}=\tilde v^{M}\,v^{M}_{\max}\) へ物理単位変換してから連結する。左右対称条件があるため、これは右脚の接地から
次の右脚接地までを表す。右床反力の鉛直候補軸が体重 \(BW=72.17\times 9.80665\) N の5%を超える連続区間を接地とする。</p>
\[ \text{contact}=\{\,t:\ \mathrm{GRF}_{\text{vertical}}(t)>0.05\,BW\,\},\quad
   \text{early stance}=[\,0,\ 0.5\,t_{\text{contact}}\,],\quad
   \text{terminal swing}=[\,2T-0.25(2T-t_{\text{contact}}),\ 2T\,]. \]
<p>境界条件動画解析だけは「1歩の最後15%（phase ≥ 85%）」を terminal swing 窓としており、上記の筋指標窓とは異なる。この違いを統合せず、
目的別の窓として扱う。</p>

<h3 id="m-15">2.15 力学的負荷代理指標の計算式</h3>
<p>筋 \(m\) の1ストライド信号から次を計算する（\(\max_t\) は1ストライド全体の最大）。</p>
\[ L^{\text{peak}}_m=\max_t \tilde l^{M}_m(t),\quad F^{CE,\text{peak}}_m=\max_t F^{CE}_m(t),\quad
   F^{pass,\text{peak}}_m=\max_t F^{pass}_m(t),\quad F^{T,\text{peak}}_m=\max_t F^{T}_m(t), \]
\[ P^{ecc}_m(t)=\max\!\big[F^{CE}_m(t)\,v^{M}_m(t),\,0\big],\qquad
   W^{neg}_m=\int P^{ecc}_m(t)\,dt. \]
<p>\(P^{ecc}\) は「筋線維が伸張されながら収縮要素が力を発揮するパワーの正の大きさ」であり、吸収エネルギーの大きさを正値で報告する。
非一様な保存時刻 \(t_i\) に対し、積分は次の台形則で行う。</p>
\[ W^{neg} \approx \sum_i \tfrac12\big[P^{ecc}(t_i)+P^{ecc}(t_{i+1})\big]\,(t_{i+1}-t_i). \]
<p>正規化筋線維長 \(\tilde l^{M}=l^{M}/l^{M}_{o}\) は、工学ひずみ \((l^{M}-l_0)/l_0\) でも、超音波で測る筋束長そのものでもない。</p>

<h3 id="m-16">2.16 記述統計・回帰・効果量</h3>
<p>\(N=100\) の8設計条件について、\(A_i=-\text{achieved\_td\_tilt\_deg}\)、指標 \(y_i\) として最小二乗直線を当てる。</p>
\[ y_i=\beta_0+\beta_1 A_i+\varepsilon_i,\qquad
   \beta_1=\frac{\sum_i (A_i-\bar A)(y_i-\bar y)}{\sum_i (A_i-\bar A)^2},\qquad
   R^{2}=1-\frac{\sum_i (y_i-\hat y_i)^2}{\sum_i (y_i-\bar y)^2}. \]
<p>端点変化率と平均基準レンジは異なる量である（前者は最小前傾条件を分母、後者は平均を分母）。</p>
\[ \text{endpoint change}\,[\%]=100\,\frac{y_{A_{\max}}-y_{A_{\min}}}{|y_{A_{\min}}|},\qquad
   \text{relative span}\,[\%]=100\,\frac{\max y-\min y}{|\overline{y}|}. \]
<p>速度交絡の探索には \(y=\beta_0+\beta_A A+\beta_V v\) を用いる。\(R^{2}\)・SD・IQR は8名からの推定ではなく<b>8設計条件の記述</b>であり、
p 値や母集団 95%CI は主張しない。Spearman 係数の現実装は二重 argsort による順位で、主独立変数の達成角度には同値がないため主要傾向への
影響はない。</p>

<h3 id="m-17">2.17 境界条件分解の再現方法</h3>
<p>静的解析は骨盤前傾 0–25°、左股関節屈曲30°、左膝角度 −20° を基準とする。tree-rigid では股・膝角度を固定したまま骨盤だけを回転する。
femur-fixed では、骨盤を回転した各姿勢で、左大腿骨の世界座標矢状面回転が基準値へ戻るよう股関節屈曲を1°有限差分で解く。</p>
\[ \text{hip\_correction}=\frac{\text{target femur rotation}-\text{rotation at current hip}}
   {\text{rotation at hip}+1^{\circ}-\text{rotation at current hip}}. \]
<p>各姿勢を OpenSim の <code>Model.assemble</code> 後に <code>realizePosition</code> し、OpenSim API の <code>Muscle.getLength</code> から MTU 長を取得する。
tree-rigid と femur-fixed は<b>幾何学的反実仮想</b>であり、動力学的実行可能性を検証した最適化解ではない。adaptive のみが実際の再最適化解である。</p>
'''

# ---- Results ------------------------------------------------------------- #
RESULTS_1 = r'''
<h3 id="r-1">3.1 最適化の成立性と主結果の概要</h3>
<p>速度範囲が 11.7467–11.7978&nbsp;m/s に収まる8条件において、達成接地時骨盤前傾量の増加に伴い、二関節ハムストリング3筋の最大
正規化筋線維長は一貫して増加した。単関節の BFsh はほぼ不変であった。一方、収縮要素力・腱力・負の仕事は筋別・メッシュ別に異なり、
「前傾増加によってハムストリング張力全体が一様に増える」という結果ではなかった。</p>

<h3 id="r-2">3.2 接地時骨盤前傾量と最大正規化筋線維長（主結果）</h3>
''' + fig(
    "fig-2", "Fig2_primary_N100.png", "図2 / Figure 2",
    "接地前傾量に対する1ストライド最大 \\(\\tilde l^{M}\\)（\\(N=100\\) 主結果） / Primary result",
    "速度をほぼ維持した条件間で、接地前傾量の増加が二関節ハムの1ストライド最大 \\(\\tilde l^{M}\\) 増加と関連するかを検証する。",
    "（A）速度は Nominal ±1% 内（スプレッド 0.43%）。（B）二関節3筋の最大 \\(\\tilde l^{M}\\) は前傾量とともに段階的に増加し、"
    "傾きは SM +0.0068・ST +0.0037・BFlh +0.0054（\\(R^{2}=0.95\\text{–}0.96\\)）。単関節 BFsh は平坦（−0.0003）。"
    "（C）傾き＋単一条件除外の感度範囲＋速度調整係数。すべて正。",
    "8点は同一モデルの決定論的設計点であり、母集団の信頼区間ではない。C のバーは信頼区間ではなく除外感度範囲。",
    "A: operability (speed within Nominal ±1%). B: peak lMtilde rises graded with anterior tilt for the three biarticular "
    "muscles; single-joint BFsh is flat. C: slope with leave-one-out range (not a CI) and speed-adjusted coefficient.")

RESULTS_2 = r'''
<div class="tablewrap"><table>
<thead><tr><th>筋</th><th>関節</th><th>最小前傾→最大前傾</th><th>端点変化</th><th>前傾1°当たりの傾き</th><th>\(R^{2}\)</th><th>判定</th></tr></thead>
<tbody>
<tr><td>半膜様筋 SM</td><td>二関節</td><td>0.973 → 1.068</td><td>+9.72%</td><td>+0.00678</td><td>0.961</td><td>増加</td></tr>
<tr><td>半腱様筋 ST</td><td>二関節</td><td>1.129 → 1.181</td><td>+4.65%</td><td>+0.00374</td><td>0.957</td><td>増加</td></tr>
<tr><td>大腿二頭筋長頭 BFlh</td><td>二関節</td><td>1.038 → 1.112</td><td>+7.19%</td><td>+0.00538</td><td>0.950</td><td>増加</td></tr>
<tr><td>大腿二頭筋短頭 BFsh</td><td>単関節（対照）</td><td>0.945 → 0.942</td><td>−0.32%</td><td>−0.00025</td><td>0.927</td><td>ほぼ不変</td></tr>
</tbody></table></div>
<p>二関節3筋では、最小前傾から最大前傾への最大 \(\tilde l^{M}\) 変化は +4.65–9.72% であった。\(R^{2}\) は 0.950–0.961 で、\(N=50\) と \(N=100\)
の方向も一致した。対照の BFsh は傾き自体はわずかに負であったが、端点差 −0.32%、平均基準レンジ 0.36% であり、二関節3筋と比較して実質的に
不変と判断した。これは「統計的にゼロを証明した」のではなく、事前に置いた解剖学的比較との効果量比較である。</p>

<h3 id="r-3">3.3 残存速度差および単一条件依存性に対する感度解析</h3>
<p>\(N=100\) の8条件では、前傾量と速度の Pearson 相関は −0.359 であった。速度を共変量として同時投入した探索的回帰でも、前傾量係数は
SM 0.00640・ST 0.00351・BFlh 0.00504 で、単回帰係数からの減少はそれぞれ 5.64%・6.19%・6.36% にとどまり、符号はすべて正のままであった
（モデル \(R^{2}\) はそれぞれ 0.982・0.982・0.976）。BFsh の前傾量係数は −0.00027 であった。1条件ずつ除外した単回帰における前傾量係数の範囲は、
SM 0.00626–0.00734・ST 0.00344–0.00403・BFlh 0.00493–0.00587 であり、全8通りで正であった。以上は、主結果が特定の1条件または残存速度差だけで
生じたという説明と整合しにくい。ただし設計点は8点のみで、速度と前傾量を無作為化していないため、速度調整後係数を因果効果とは解釈しない。</p>
''' + fig(
    "fig-6", "Fig6_numerical_robustness.png", "図6 / Figure 6",
    "数値的成立性・解選択・感度 / Numerical robustness",
    "主結果が角度未達・制約違反・単一条件・速度差・成功解選択だけで説明されないかを確認する。",
    "全95 MAT を「発見→読込→PelvisTD→\\(N=100\\)→wide→strict」の順に絞り、要求 offset ごとに <code>inf_pr</code> 最小の8条件を採用。"
    "採用8条件は <code>inf_pr</code> ≈ 1e−9…1e−7（≪ 1e−4）、失敗解は > 1e−2 で低速へ崩壊。",
    "この図は数値的頑健性を示すもので、生物学的一般化ではない。",
    "Discovery-to-adoption funnel (95 MAT to 8 adopted). Adopted inf_pr much less than 1e-4; failed solves collapse to low "
    "speed. The result is not an artefact of unmet angle, constraint violation, or solution selection.")

RESULTS_3 = r'''
<h3 id="r-4">3.4 筋別の収縮要素力・受動筋線維力・腱力</h3>
<div class="tablewrap"><table class="small">
<thead><tr><th>筋</th><th>収縮要素力 \(F^{CE}\) [N]（端点変化）</th><th>受動力 \(F^{pass}\) [N]（端点変化）</th><th>腱力 \(F^{T}\) [N]（端点変化）</th><th>受動力の平均基準レンジ</th></tr></thead>
<tbody>
<tr><td>SM</td><td>3099.5→3311.8 (+6.85%)</td><td>39.9→75.2 (+88.31%)</td><td>3012.8→3253.1 (+7.98%)</td><td>66.15%</td></tr>
<tr><td>ST</td><td>816.2→789.8 (−3.23%)</td><td>36.0→51.1 (+42.02%)</td><td>845.7→830.5 (−1.80%)</td><td>36.00%</td></tr>
<tr><td>BFlh</td><td>2302.1→2320.3 (+0.79%)</td><td>42.8→70.6 (+64.73%)</td><td>2333.0→2366.0 (+1.42%)</td><td>51.93%</td></tr>
<tr><td>BFsh</td><td>1719.1→1683.0 (−2.10%)</td><td>20.6→20.2 (−2.00%)</td><td>1575.6→1544.6 (−1.97%)</td><td>2.30%</td></tr>
</tbody></table></div>
<p>収縮要素力の応答は筋間で一様でなく、SM で増加、ST で減少、BFlh では変化が小さかった。受動力は二関節3筋で増加したが、増加幅は筋により
異なった（端点変化 SM +88.31%、ST +42.02%、BFlh +64.73%）。</p>
''' + callout(
    "fact", "Fact",
    "前傾増加とともに二関節3筋の受動力の方向は増加した。") + callout(
    "interp", "Interpretation",
    "筋線維が至適長を越える領域へ近づく／入ることで、受動力–長さ曲線の寄与が増した可能性がある。") + callout(
    "limit", "言えないこと",
    "生体内の局所組織応力・損傷閾値・受傷確率が同じ割合で増えたとは言えない。") + fig(
    "figS1", "FigS1_force_length.png", "補足図S1 / Figure S1",
    "力–長さ作用域 / Force-length operating region",
    "二関節ハムが力–長さ関係上のどこで作動し、前傾でどう移動するかを示す。",
    "前傾大（m8）の終末遊脚期作用点は、前傾小（p6）より長い \\(\\tilde l^{M}\\) 側へ移動する。\\(F^{CE}\\) は減衰項を含む収縮要素力。",
    "", 
    "Fce (incl. damping) vs lMtilde for min vs max tilt; the max-tilt terminal-swing operating point sits at longer lMtilde.") + fig(
    "figS2", "FigS2_muscle_metric_heatmap.png", "補足図S2 / Figure S2",
    "筋×指標 変化率 / Muscle × metric change",
    "各負荷代理指標が最小→最大前傾でどう変化するかを一覧する。",
    "受動力 \\(F^{pass}\\) が最大の上昇（二関節 +42…+88%）、負の仕事 +16…+33%、最大 \\(\\tilde l^{M}\\) +4.7…+9.7%。BFsh はほぼ中立／負。",
    "",
    "Percent change min to max tilt per metric; passive force rises most, biarticular metrics rise, BFsh near zero.")

RESULTS_4 = r'''
<h3 id="r-5">3.5 終末遊脚期の負の筋線維仕事</h3>
<div class="tablewrap"><table class="small">
<thead><tr><th>筋</th><th>最小前傾→最大前傾</th><th>端点変化</th><th>平均基準レンジ</th><th>N50–N100 平均絶対差</th><th>判定</th></tr></thead>
<tbody>
<tr><td>SM</td><td>13.70 → 28.50 J</td><td>+108.0%</td><td>73.7%</td><td>8.55%</td><td>増加</td></tr>
<tr><td>ST</td><td>3.17 → 7.66 J</td><td>+141.6%</td><td>88.3%</td><td>28.42%</td><td>増加</td></tr>
<tr><td>BFlh</td><td>5.95 → 15.82 J</td><td>+165.8%</td><td>100.4%</td><td>33.36%</td><td>増加</td></tr>
<tr><td>BFsh</td><td>19.76 → 17.71 J</td><td>−10.4%</td><td>16.2%</td><td>17.98%</td><td>結論保留</td></tr>
</tbody></table></div>
<p>終末遊脚期の負の仕事は二関節3筋で増加方向が再現したが、ST と BFlh では N50–N100 差が 28.4% および 33.4% であった。したがって「方向」は
条件付きで支持できるが、+142% や +166% という<b>大きさ</b>はメッシュに依存する。主結論は線維長に置き、仕事量は副次的・条件付き結果とするのが妥当である。</p>

<h3 id="r-6">3.6 最大値の出現時相</h3>
<div class="tablewrap"><table class="small">
<thead><tr><th>筋</th><th>最大 \(\tilde l^{M}\) の時相</th><th>最大収縮要素力時に伸張中か</th></tr></thead>
<tbody>
<tr><td>SM</td><td>88.0–90.8% stride</td><td>True</td></tr>
<tr><td>ST</td><td>85.5–88.3% stride</td><td>True</td></tr>
<tr><td>BFlh</td><td>86.0–89.1% stride</td><td>True</td></tr>
<tr><td>BFsh</td><td>2.1–2.8% stride</td><td>True</td></tr>
</tbody></table></div>
<p>二関節3筋の最大 \(\tilde l^{M}\) はストライドの 85.5–90.8% に生じた。主要評価項目は1ストライド全体から抽出した最大値であり、終末遊脚期窓内に
限定して探索したものではない。それにもかかわらずピーク時相が終末遊脚期へ集中した。BFsh のピークは 2.1–2.8% であり、二関節筋とは異なる局面であった。</p>
''' + fig(
    "fig-3", "Fig3_lMtilde_waveforms_N100.png", "図3 / Figure 3",
    "\\(\\tilde l^{M}\\) 波形とピーク時相 / Waveforms and peak phase",
    "1ストライド最大 \\(\\tilde l^{M}\\) はどの局面でどのように前傾量へ応答するかを示す。",
    "8条件の \\(\\tilde l^{M}\\) 波形（濃色＝前傾大）。marker は1ストライド最大（全ストライド）で、二関節筋では終末遊脚期（85.5–90.8%）に位置。"
    "BFsh は早期立脚（〜2–3%）にピークをもち平坦。",
    "主評価は1ストライド全体の最大値であり、Pareto の terminal-swing-window peak（図7）とは別定義。",
    "lMtilde vs % stride for the 8 conditions, coloured by anterior tilt. Markers = 1-stride max, which lands in terminal "
    "swing for the biarticular muscles. Distinct from the Pareto TS-window peak.")

RESULTS_5 = r'''
<h3 id="r-7">3.7 境界条件による筋腱単位長変化の分解</h3>
''' + fig(
    "fig-5", "Fig5_pelvis_femur_mechanism.png", "図5 / Figure 5",
    "骨盤–大腿協調による機序分解 / Pelvis-femur mechanism decomposition",
    "観察されたハム伸長は骨盤絶対角ではなく骨盤–大腿の<b>相対配置</b>で説明されるかを検証する。",
    "正規化位相・OpenSim 厳密 MTU で、adaptive の終末遊脚期 ΔMTU は SM +7.67 / ST +9.73 / BFlh +8.44 mm。"
    "大腿世界姿勢を固定した femur-fixed が adaptive の 89.6–95.8% を再現（骨盤と共回転する tree-rigid は ΔMTU≈0）。",
    "tree-rigid・femur-fixed は幾何学的反実仮想（実行不能）、adaptive のみ実行可能解。89.6–95.8% は<b>媒介割合ではない</b>。",
    "tree-rigid (pelvis & femur co-rotate) gives dMTU~0; femur-fixed (femur world pose held) reproduces 89.6-95.8% of the "
    "adaptive terminal-swing MTU rise. A/B are geometric counterfactuals; only adaptive is feasible. Not a mediation fraction.")

RESULTS_6 = r'''
<p>静的 femur-fixed 条件の 25° 前傾による MTU 長変化は SM +21.6・ST +26.9・BFlh +24.6・BFsh +0.0 mm/25° であった。動作解析における
終末遊脚期ピーク変化は次の通りである。</p>
<div class="tablewrap"><table class="small">
<thead><tr><th>筋</th><th>tree-rigid</th><th>femur-fixed</th><th>adaptive</th><th>fixed/adaptive</th></tr></thead>
<tbody>
<tr><td>SM</td><td>+0.00 mm</td><td>+7.06 mm</td><td>+7.67 mm</td><td>92.1%</td></tr>
<tr><td>ST</td><td>+0.00 mm</td><td>+8.72 mm</td><td>+9.73 mm</td><td>89.6%</td></tr>
<tr><td>BFlh</td><td>+0.00 mm</td><td>+8.08 mm</td><td>+8.44 mm</td><td>95.8%</td></tr>
<tr><td>BFsh</td><td>+0.00 mm</td><td>+0.00 mm</td><td>+1.23 mm</td><td>0.0%</td></tr>
</tbody></table></div>
<p>二関節3筋では、femur-fixed 条件のピーク MTU 長変化は adaptive 条件の 89.6–95.8% に相当した。この比率は分散説明率ではなく、正規化位相で
対応させた終末遊脚期ピーク差の比である。残差には膝・骨盤並進・体幹・時相など再最適化協調の寄与が含まれ得る。BFsh は femur-fixed で 0、
adaptive で +1.23 mm と小さく、股関節をまたぐ二関節筋との比較所見となった。</p>

<h3 id="r-8">3.8 \(N=100\) における速度–負荷代理指標の交換関係</h3>
''' + fig(
    "fig-7", "Fig7_pareto_N100.png", "図7 / Figure 7",
    "速度–負荷代理指標の Pareto（\\(N=100\\)、複数ウォームスタート） / Speed-load Pareto",
    "速度損失を事前基準内に保ちつつ、筋線維長代理指標が低い候補解を計算上生成できるかを検証する。",
    "\\(w=0.1\\) の3ウォームスタート経路で平均 dSpeed −0.340%・dSurrogate（二関節TS窓ピーク平均）−5.189%。"
    "事前基準（速度損失 ≤0.5% かつ代理指標 ≤−3%）を \\(w=0.05/0.10\\) が満たし、\\(w=0.2\\) は速度予算超過。",
    "3解は独立反復でなく3決定論的経路。最適化が直接罰する平滑積分項と報告ピークは別指標。候補解は実走可能性・受傷低減を証明しない。",
    "w=0.1 (3 warm-start paths) reduces the biarticular terminal-swing-window peak surrogate by ~5.2% for ~0.34% speed loss; "
    "w=0.05/0.10 meet the pre-registered target, w=0.2 exceeds the speed budget.")

RESULTS_7 = r'''
<div class="tablewrap"><table class="small">
<thead><tr><th>解</th><th>\(w\)</th><th>初期値</th><th>速度 [m/s]</th><th>Δ速度</th><th>代理指標</th><th>Δ代理指標</th><th>反復数</th></tr></thead>
<tbody>
<tr><td>w0000_F</td><td>0.00</td><td>forward from NominalN100</td><td>11.83460</td><td>+0.000%</td><td>1.0726</td><td>+0.00%</td><td>153</td></tr>
<tr><td>w0050_F</td><td>0.05</td><td>forward cont from w0000</td><td>11.81750</td><td>−0.144%</td><td>1.0375</td><td>−3.27%</td><td>682</td></tr>
<tr><td>w0100_B</td><td>0.10</td><td>from NominalN100</td><td>11.79509</td><td>−0.334%</td><td>1.0175</td><td>−5.14%</td><td>553</td></tr>
<tr><td>w0100_C</td><td>0.10</td><td>backward cont from w0200</td><td>11.79286</td><td>−0.353%</td><td>1.0160</td><td>−5.28%</td><td>532</td></tr>
<tr><td>w0100_F</td><td>0.10</td><td>forward cont from w0050</td><td>11.79510</td><td>−0.334%</td><td>1.0174</td><td>−5.15%</td><td>446</td></tr>
<tr><td>w0200_B</td><td>0.20</td><td>from NominalN100</td><td>11.74307</td><td>−0.773%</td><td>0.9857</td><td>−8.10%</td><td>702</td></tr>
<tr><td>w0200_F</td><td>0.20</td><td>forward cont from w0100</td><td>11.74548</td><td>−0.753%</td><td>0.9871</td><td>−7.97%</td><td>915</td></tr>
</tbody></table></div>
<p>\(w=0.1\) の3ウォームスタート経路における速度は 11.79435±0.00129 m/s、範囲 11.79286–11.79510 m/s であった。速度変化は −0.340±0.011%、
代理指標変化は −5.189±0.077% であった。3解はすべて事前基準を満たした。ただし、これらの SD は個人差でも再現性係数でもなく、選択した3ウォーム
スタート経路に対する局所解の散らばりである。</p>
''' + vid(
    "vid-pareto", "ham_pareto_sidebyside.mp4", "ham_pareto_sidebyside.gif",
    "動画2 / Video 2", "基準解と候補動作の筋骨格比較 / Baseline vs candidate motion",
    "筋線維長ペナルティで得た候補動作が、基準解に対してどのように骨盤・股関節運動と筋経路を変えるかを視覚化する。",
    "基準（\\(w=0\\)）と負荷低減候補（\\(w>0\\)）の3次元筋骨格アニメーションを並置。骨盤傾斜・股関節屈曲の縮小と二関節ハム経路の短縮が確認できる。",
    "この動画だけで代理指標低下が速度差から独立した効果だと因果分離したわけではない。実走可能なコーチング指示も未検証。")

RESULTS_8 = r'''
<h3 id="r-9">3.9 探索的解析：目的関数の違いによる候補解の変化</h3>
<div class="tablewrap"><table class="small">
<thead><tr><th>目的</th><th>\(w\)</th><th>Δ速度</th><th>Δ線維長</th><th>Δ能動伸張性power</th><th>Δ負の仕事</th><th>Δ受動力</th><th>候補判定</th></tr></thead>
<tbody>
<tr><td>線維長</td><td>0.1</td><td>−0.241%</td><td>−4.14%</td><td>−9.47%</td><td>−5.63%</td><td>−25.53%</td><td>True</td></tr>
<tr><td>能動伸張性</td><td>0.1</td><td>−0.062%</td><td>−0.20%</td><td>−16.52%</td><td>−20.38%</td><td>−1.39%</td><td>True</td></tr>
<tr><td>能動伸張性・高重み</td><td>8</td><td>−1.909%</td><td>+1.70%</td><td>−97.59%</td><td>−94.23%</td><td>+13.79%</td><td>False</td></tr>
<tr><td>受動力</td><td>0.2</td><td>−0.034%</td><td>+0.92%</td><td>+0.41%</td><td>+0.46%</td><td>+6.82%</td><td>False</td></tr>
<tr><td>複合（等係数）</td><td>0.1</td><td>−0.335%</td><td>−4.54%</td><td>−28.54%</td><td>−27.41%</td><td>−27.60%</td><td>True</td></tr>
</tbody></table></div>
<p>能動伸張性目的 \(w=0.1\) は線維長をほぼ変えず、能動伸張性 power と負の仕事を約 16.5% および 20.4% 低下させた。複合 \(w=0.1\) は速度 −0.335% で、
線維長 −4.54%、能動伸張性 power −28.54%、負の仕事 −27.41%、受動力 −27.60% を同時に示した。ただし、これらは \(N=50\) の探索結果であり、
\(N=100\) 複数ウォームスタート確認を終えていない。能動伸張性目的は \(F^{CE}\times\max(\tilde v^{M},0)\) を積分しており、\(\tilde v^{M}\) が無次元である
ため物理的な W／J ではない。この構成概念差のため、本節は探索結果として主解析から分離する。</p>

<h3 id="r-10">3.10 解像度および条件系列をまたぐ効果方向の確認</h3>
''' + fig(
    "figS4", "FigS4_mesh_robustness.png", "補足図S4 / Figure S4",
    "解像度頑健性 / Resolution robustness",
    "接地前傾の用量反応はメッシュ解像度に頑健か（\\(N=50\\) wide 対 \\(N=100\\) wide、達成角で比較）。",
    "主結果である最大 \\(\\tilde l^{M}\\) の N50–N100 平均絶対相対差は SM 1.54%・ST 0.81%・BFlh 1.28%・BFsh 0.12%。方向は頑健、\\(N=50\\) 傾きは約20%急。"
    "受動力は最大約20%、負の仕事は最大約34%の差をもつため、後二者の大きさは条件付き。",
    "基準の 0.524° 差はメッシュ依存の最適点シフト。純粋な mesh convergence ではない（探索境界系列も一部異なる）。",
    "N=50 wide vs N=100 wide dose-response at achieved touchdown angle. Direction robust; N=50 slope ~20% steeper. Base "
    "differs 0.524 deg (mesh-dependent optimum shift): resolution robustness, not pure mesh convergence.")

# ---- Discussion ---------------------------------------------------------- #
DISCUSSION = r'''
<h3 id="d-1">4.1 接地時骨盤前傾量は二関節ハムの最大 \(\tilde l^{M}\) と段階的に関連した</h3>
<p>本研究の主要所見は、速度が 11.7467–11.7978&nbsp;m·s\(^{-1}\) の狭い範囲に保たれた \(N=100\) の8設計条件において、接地時骨盤前傾量の増加に伴い、
SM・ST・BFlh の1ストライド最大 \(\tilde l^{M}\) が増加したことである。最小前傾から最大前傾への増加は +4.65–9.72% であり、8設計点における直線近似の
決定係数は 0.950–0.961 であった。これに対し BFsh の端点変化は −0.32% であった。したがって、本結果は全ハムストリングに共通する一様な変化ではなく、
股関節をまたぐという解剖学的特徴を持つ筋に選択的な応答と整合する。二関節3筋の最大値は 85.5–90.8% stride に出現し、Thelen ら
<a class="cref" href="#ref3">[3]</a>、Chumanov ら<a class="cref" href="#ref4">[4]</a>、Schache ら<a class="cref" href="#ref5">[5]</a><a class="cref" href="#ref6">[6]</a>が
示した二関節ハムの伸長時相と一致する。本研究はこれらの知見を、接地時骨盤前傾という具体的な運動学変数へ接続した。</p>

<h3 id="d-2">4.2 「接地変数を独立に操作する」枠組みを筋線維力学へ拡張した</h3>
<p>Haralabidis ら<a class="cref" href="#ref12">[12]</a>は HTD または IKTD を基準解から段階的に拘束し、残りの全身運動を再最適化することで、接地変数と
最高速度の関係を検討した。本研究でも接地時骨盤傾斜以外の座標・制御を固定せず再最適化した結果、前傾量が約14°異なる条件間でも速度範囲は 0.435% に
とどまった一方、二関節3筋の最大 \(\tilde l^{M}\) は系統的に変化した。すなわち、速度が維持されたことは<b>筋線維力学が不変であることを意味しない</b>。
元研究が「接地変数がパフォーマンスをどう変えるか」を扱ったのに対し、本研究は「パフォーマンスがほぼ維持された条件間でも、内部の筋力学がどう
再配分されるか」を示した。</p>

<h3 id="d-3">4.3 骨盤前傾の力学的意味は骨盤角度単独ではなく骨盤–大腿協調にある</h3>
<p>Mendiguchia ら<a class="cref" href="#ref8">[8]</a>は固定標本で骨盤前傾が二関節ハム組織伸長を増加させることを示した。本研究の femur-fixed 条件でも
同方向の伸長が生じ、正規化位相で対応させた動作解析では femur-fixed のピーク変化は adaptive の 89.6–95.8% であった。一方、骨盤と大腿を共回転させて
股関節相対角を保持した tree-rigid 条件では筋腱単位長は変化しなかった。したがって、骨盤前傾の絶対角度だけからハム伸長を決定することはできない。
adaptive では接地時骨盤前傾量と最大股関節屈曲が共変しており、本モデルで支持される経路は「接地時骨盤傾斜制約 → 骨盤・股関節・大腿姿勢の再協調 →
二関節ハム伸長」である。骨盤角度と股関節屈曲の独立寄与を識別するには、両者を独立に操作する要因計画または局所感度解析が必要である。</p>

<h3 id="d-4">4.4 筋線維長の増加は一貫したが、力・仕事の応答は筋特異的であった</h3>
<p>最大 \(\tilde l^{M}\) は二関節3筋で一貫して増加したが、収縮要素力は SM で増加、ST で減少、BFlh で変化小、腱力も同一方向でなかった。受動力は
二関節3筋で増加したが、その増加率は N=50/N=100 の条件系列差に対して最大 \(\tilde l^{M}\) より感度が高かった。この不均一性は、最大ひずみ・伸張速度・
力・仕事を最も大きく担う筋が一致しないという Schache らの結果<a class="cref" href="#ref5">[5]</a><a class="cref" href="#ref6">[6]</a>と整合する。
\(\tilde l^{M}\) の増加を、そのまま「ハム張力の増加」と表現することはできない。とくに本研究の \(F^{CE}\) は活性化・力–長さ・力–速度・減衰項から
構成される収縮要素力であり、純粋な活性化由来の力と完全には同義でない。したがって主結論は最大 \(\tilde l^{M}\) に置き、力・仕事は筋別の副次結果とする。</p>

<h3 id="d-5">4.5 主要な段階的関係は残存速度差だけでは説明しにくいが因果効果とは断定できない</h3>
<p>全8条件は基準速度の ±1% 以内であり、速度を共変量として加えた探索的回帰でも前傾量係数は符号がすべて正であった。1条件ずつ除外した解析でも
二関節3筋の傾きは全パターンで正であった。これらは主要所見が特定の1条件または小さな速度差だけで生じたという説明と整合しにくい。ただし8点は独立な
被験者ではなく同一モデルの決定論的設計点であり、速度と前傾量は無作為化されていない。したがって速度調整回帰は母集団因果効果を推定するものではない。
本研究で支持されるのは、採用した \(N=100\) 成功解の範囲における<b>モデル内の段階的関係</b>である。</p>

<h3 id="d-6">4.6 速度–負荷最適化は主結果を候補動作生成へ接続した</h3>
<p>筋線維長超過ペナルティを加えた \(N=100\) 解析では、\(w=0.1\) の3ウォームスタート経路から、速度変化 −0.340±0.011% に対し、二関節3筋の終末遊脚期
窓内ピーク \(\tilde l^{M}\) 平均が −5.189±0.077% となる解が得られた。一方、最適化が直接最小化した量は \(\tilde l^{M}>1\) の平滑二乗時間積分であり、報告した
終末遊脚期ピークとは同一でない。3解も独立反復ではなく3つのウォームスタート経路である。したがってこの結果は大域最適性・実走可能性・介入効果・受傷
予防効果を保証しない。ここで得られた動作は、実験的に検証すべき<b>設計候補</b>として位置づける必要がある。</p>

<h3 id="d-7">4.7 本研究の学術的貢献</h3>
<p>第一に、固定標本で示された骨盤前傾–ハム伸長関係を、全身が再協調する最高速度近傍の予測スプリントへ拡張し、速度を狭い範囲に保った8条件の段階的応答
として示した。第二に、二関節3筋と単関節 BFsh を比較し、筋線維長・収縮要素力・受動力・腱力・負の仕事を分離した。第三に、tree-rigid・femur-fixed・
adaptive という異なる境界条件を比較し、骨盤前傾の力学的意味が骨盤–大腿配置に依存することを示した。第四に、接地変数操作フレームワーク
<a class="cref" href="#ref12">[12]</a>を筋力学的代理指標へ拡張し、運動学–筋力学の理解を候補動作生成へ接続した。これらは骨盤前傾を単独の危険因子や
矯正目標として提示するものではなく、観察可能な接地時運動学・内部の筋線維力学・パフォーマンス制約を同一の計算枠組みで関連づけた点に新規性がある。</p>

<h3 id="d-8">4.8 今後検証すべき課題</h3>
<p>第一に、異なる被験者モデルおよび筋腱パラメータ集合で主要効果の方向の頑健性を確認する。第二に、至適筋線維長・最大等尺性筋力・腱コンプライアンス・
受動力–長さ特性の感度解析でモデルパラメータ不確実性を定量化する。第三に、同一の探索境界系列を用いた複数メッシュで再計算し、時間離散化と境界条件系列の
影響を分離する。第四に、実走者の骨盤・大腿運動学と生体内筋束挙動を同時計測し、本仮説を被験者内で検証する。最後に、候補動作の遂行可能性および受傷
アウトカムとの関連は、独立した介入研究および前向き研究で評価しなければならない。</p>
'''

# ---- Limitations --------------------------------------------------------- #
LIMITATIONS = r'''
<p>本研究の結果は、以下の制約のもとで解釈する必要がある。</p>
<ol class="limlist">
<li><b>単一モデルの計算実験。</b> 国際水準男子スプリンター1名に基づく単一モデルであり、8条件は独立した被験者・試行ではなく同一モデルの設計点である。
母集団推論に基づく p 値・95%CI は提示せず、女性・異なる競技水準・既往歴・疲労状態・異なる筋腱形態へ一般化できない。</li>
<li><b>局所最適化。</b> すべての主条件は厳密に <code>Solve_Succeeded</code> を満たしたが、大域最適性や、要求全角度範囲に連続的な実行可能解が存在することは
保証されない。成功解の採用規則・warm-start・探索境界は結果へ影響し得る<a class="cref" href="#ref12">[12]</a>。</li>
<li><b>メッシュと条件系列。</b> \(N=50\) と \(N=100\) では一部条件の standard/wide 系列が一致しない。両者の比較には時間離散化だけでなく探索境界系列・
達成接地角の差が含まれる。受動力・負の仕事の効果量はメッシュ・系列に対する感度が高く、定量的確度は最大 \(\tilde l^{M}\) より低い。</li>
<li><b>筋腱モデルの仮定。</b> 全筋の \(F^{M}_{o}\) 2倍化、\(v^{M}_{\max}=12\,l^{M}_{o}\)、共通の腱・受動力特性などの仮定を含む。体系的感度解析は未完了。
また実装では筋25（quad_fem_r）の <code>muscProperties</code> 第2行を10%増加しており、コード上は至適筋線維長の変更に相当する一方、コメントには腱自然長の
変更と記載されている。この意図は未確定である（全条件共通のため用量反応の<b>差</b>には無影響）。</li>
<li><b>外部検証の範囲。</b> モデル検証は主として関節運動・関節モーメント・床反力・筋活動の全体的特徴に基づく。内部の筋線維長・受動力・腱力・局所組織応力が
生体内で正確であることを直接保証しない。\(\tilde l^{M}\) は筋損傷そのものではなく、局所組織ひずみ・筋腱接合部応力・受傷確率とも同一でない。</li>
<li><b>境界条件解析の性質。</b> tree-rigid・femur-fixed は幾何学的反実仮想であり、動力学的に実行可能なスプリント動作ではない。89.6–95.8% は統計的媒介割合や
骨盤前傾の独立寄与ではない。OpenSim の assemble 処理・位相補間が結果に影響し得る。</li>
<li><b>再現環境。</b> 公開 clone には元 MAT が含まれないため、シミュレーション出力から最終表までの完全な統合再現は元データ保存環境で最終確認する必要がある
（合成データ単体テストは通過）。</li>
</ol>
''' + fig(
    "figS3", "FigS3_param_sensitivity.png", "補足図S3 / Figure S3",
    "筋腱パラメータ感度 / Muscle-tendon parameter sensitivity",
    "基準ハムストリング作用点は筋腱パラメータ ±10% にどれだけ感度をもつか。",
    "至適筋線維長 oMFL が支配的（−10% で二関節平均 peak \\(\\tilde l^{M}\\) 約 +0.09、+10% で約 −0.08）。最大等尺性筋力 Fmax は小（±10% で ±0.008 程度）。"
    "腱自然長 TSL は脆弱（−10% で速度・傾斜ドリフト、+10% で失敗）。",
    "これは基準作用点の感度であり、用量反応<b>傾き</b>の感度ではない。受動力–長さはモデルの per-muscle 化が必要で未実施。",
    "Sensitivity of the baseline biarticular hamstring peak lMtilde to +/-10% muscle-tendon parameters (oMFL dominant; Fmax "
    "small; TSL fragile). Baseline operating-point sensitivity, not dose-response-slope sensitivity.")

# ---- Conclusion ---------------------------------------------------------- #
CONCLUSION = r'''
<p>本研究は、単一の国際水準男子スプリンターモデルを用い、最高速度近傍の全身運動を再最適化しながら接地時骨盤前傾量を段階的に操作した。その結果、
速度が 11.7467–11.7978&nbsp;m·s\(^{-1}\) の範囲に保たれた \(N=100\) の8設計条件において、接地時骨盤前傾量の増加は、SM・ST・BFlh の1ストライド最大
\(\tilde l^{M}\) の増加と一貫して関連した。これらのピークは終末遊脚期に生じた一方、股関節をまたがない BFsh の変化は小さかった。</p>
<p>境界条件解析は、観察された筋長変化が骨盤の絶対角度だけで決まるのではなく、股関節屈曲および大腿姿勢を含む骨盤–大腿協調に依存することを示した。
また、筋線維長代理指標を目的関数へ加えた再最適化により、速度損失を 0.5% 以内に保ちながら代理指標を低減する候補解を生成できた。</p>
<div class="callout fact"><span class="colabel">結論</span>
<b>最高速度近傍の単一モデル内では、接地時骨盤前傾量は二関節ハムストリングの最大正規化筋線維長と関連する運動学的指標であり、その力学的意味は
骨盤–大腿協調の中で解釈すべきである。</b> 本研究の貢献は、骨盤前傾を受傷原因または一律の矯正目標として提示することではなく、接地時運動学・筋線維力学・
速度制約を同一の予測シミュレーション枠組みで接続し、実測研究で検証可能な仮説と候補動作を提示した点にある。</div>
'''

# ---- References ---------------------------------------------------------- #
REFERENCES = r'''
<ol class="reflist">
<li id="ref1">Ekstrand J, Bengtsson H, Waldén M, Davison M, Khan KM, Hägglund M. Hamstring injury rates have increased during recent
seasons and now constitute 24% of all injuries in men's professional football: the UEFA Elite Club Injury Study from 2001/02 to
2021/22. <i>Br J Sports Med.</i> 2023;57(5):292–298.
<a href="https://doi.org/10.1136/bjsports-2021-105407" target="_blank" rel="noopener">doi:10.1136/bjsports-2021-105407</a></li>
<li id="ref2">Gronwald T, Klein C, Hoenig T, et&nbsp;al. Hamstring injury patterns in professional male football (soccer): a systematic
video analysis of 52 cases. <i>Br J Sports Med.</i> 2022;56(3):165–171.
<a href="https://doi.org/10.1136/bjsports-2021-104769" target="_blank" rel="noopener">doi:10.1136/bjsports-2021-104769</a></li>
<li id="ref3">Thelen DG, Chumanov ES, Hoerth DM, et&nbsp;al. Hamstring muscle kinematics during treadmill sprinting.
<i>Med Sci Sports Exerc.</i> 2005;37(1):108–114.
<a href="https://doi.org/10.1249/01.MSS.0000150078.79120.C8" target="_blank" rel="noopener">doi:10.1249/01.MSS.0000150078.79120.C8</a></li>
<li id="ref4">Chumanov ES, Heiderscheit BC, Thelen DG. The effect of speed and influence of individual muscles on hamstring mechanics
during the swing phase of sprinting. <i>J Biomech.</i> 2007;40(16):3555–3562.
<a href="https://doi.org/10.1016/j.jbiomech.2007.05.026" target="_blank" rel="noopener">doi:10.1016/j.jbiomech.2007.05.026</a></li>
<li id="ref5">Schache AG, Dorn TW, Blanch PD, Brown NAT, Pandy MG. Mechanics of the human hamstring muscles during sprinting.
<i>Med Sci Sports Exerc.</i> 2012;44(4):647–658.
<a href="https://doi.org/10.1249/MSS.0b013e318236a3d2" target="_blank" rel="noopener">doi:10.1249/MSS.0b013e318236a3d2</a></li>
<li id="ref6">Schache AG, Dorn TW, Wrigley TV, Brown NAT, Pandy MG. Stretch and activation of the human biarticular hamstrings across a
range of running speeds. <i>Eur J Appl Physiol.</i> 2013;113(11):2813–2828.
<a href="https://doi.org/10.1007/s00421-013-2713-9" target="_blank" rel="noopener">doi:10.1007/s00421-013-2713-9</a></li>
<li id="ref7">Timmins RG, Bourne MN, Shield AJ, Williams MD, Lorenzen C, Opar DA. Short biceps femoris fascicles and eccentric knee
flexor weakness increase the risk of hamstring injury in elite football (soccer): a prospective cohort study.
<i>Br J Sports Med.</i> 2016;50(24):1524–1535.
<a href="https://doi.org/10.1136/bjsports-2015-095362" target="_blank" rel="noopener">doi:10.1136/bjsports-2015-095362</a></li>
<li id="ref8">Mendiguchia J, Garrues MA, Schilders E, Myer GD, Dalmau-Pastor M. Anterior pelvic tilt increases hamstring strain and is a
key factor to target for injury prevention and rehabilitation. <i>Knee Surg Sports Traumatol Arthrosc.</i> 2024;32(3):573–582.
<a href="https://doi.org/10.1002/ksa.12045" target="_blank" rel="noopener">doi:10.1002/ksa.12045</a></li>
<li id="ref9">Bramah C, Rhodes S, Clarke-Cornwell A, Dos'Santos T. Sprint running mechanics are associated with hamstring strain injury:
a 6-month prospective cohort study of 126 elite male footballers. <i>Br J Sports Med.</i> 2026;60(3):178–185.
<a href="https://doi.org/10.1136/bjsports-2024-108600" target="_blank" rel="noopener">doi:10.1136/bjsports-2024-108600</a></li>
<li id="ref10">Mendiguchia J, Castaño-Zambudio A, Jiménez-Reyes P, et&nbsp;al. Can We Modify Maximal Speed Running Posture? Implications
for Performance and Hamstring Injury Management. <i>Int J Sports Physiol Perform.</i> 2022;17(3):374–383.
<a href="https://doi.org/10.1123/ijspp.2021-0107" target="_blank" rel="noopener">doi:10.1123/ijspp.2021-0107</a></li>
<li id="ref11">Haralabidis N, Serrancolí G, Colyer S, Bezodis I, Salo A, Cazzola D. Three-dimensional data-tracking simulations of
sprinting using a direct collocation optimal control approach. <i>PeerJ.</i> 2021;9:e10975.
<a href="https://doi.org/10.7717/peerj.10975" target="_blank" rel="noopener">doi:10.7717/peerj.10975</a></li>
<li id="ref12">Haralabidis N, Eaton AJ, Delp SL, Hicks JL. Simulations Reveal How Touchdown Kinematic Variables Affect Top Sprinting
Speed: Implications for Coaching. <i>Med Sci Sports Exerc.</i> 2025;57(12):2807–2815.
<a href="https://doi.org/10.1249/MSS.0000000000003797" target="_blank" rel="noopener">doi:10.1249/MSS.0000000000003797</a></li>
<li id="ref13">Lin YC, Pandy MG. Predictive Simulations of Human Sprinting: Effects of Muscle-Tendon Properties on Sprint Performance.
<i>Med Sci Sports Exerc.</i> 2022;54(11):1961–1972.
<a href="https://doi.org/10.1249/MSS.0000000000002978" target="_blank" rel="noopener">doi:10.1249/MSS.0000000000002978</a></li>
</ol>
'''

# ---- Appendices ---------------------------------------------------------- #
APPENDIX = r'''
<h3 id="appendix-a">付録A. 再現手順と実装上の未解決事項</h3>
<p>再現性には二つの水準がある。<b>水準1（公開 clone だけで可能な派生結果の検証）：</b> リポジトリを clone し、commit
<code>e7b8de9</code> を checkout、conda 環境を構築のうえ、単体テスト <code>python analysis/validation/test_unit_metrics.py</code> を
実行する。コミット済み CSV・PNG、<code>manifest_provenance.csv</code>、<code>output_hashes.csv</code> を照合できる（source MAT が
ないため MAT からの再計算はスキップ）。<b>水準2（source MAT からの完全再計算）：</b> Windows 上で MATLAB・CasADi・MUMPS を用意し、
<code>setup_paths</code> 実行後に <code>main_pred_sim_sprinting('_Nominal', 50)</code> / <code>('_Nominal', 100)</code> を実行、
続いて8条件スイープと Python 解析（<code>build_manifest.py</code> → <code>analyze_eight_conditions.py</code> →
<code>phaseA_muscle_tension.py</code> → …）を順に実行する。IPOPT/BLAS/MUMPS/CPU 環境による最終桁差があり得るため、byte 一致では
なく、solver status・メッシュ \(N\)・達成角度・速度・制約残差・主要効果の方向と大きさを <code>manifest_provenance.csv</code> と照合する。</p>
<div class="callout limit"><span class="colabel">未解決</span>
約360&nbsp;MB の source MAT が公開 clone にない／README の一部例が現行 API と不一致／既定 runner は −8° と wide 条件を含まない／
OpenSim 4.4 境界解析用 environment が未定義／筋25 の変更意図が未確定。これらは提出版確定前に解決すべき項目である（付録C）。</div>

<h3 id="appendix-b">付録B. 証拠水準に基づく主張の整理</h3>
<div class="tablewrap"><table>
<thead><tr><th>区分</th><th>内容</th></tr></thead>
<tbody>
<tr><td><span class="lab labR">Fact</span></td><td>\(N=100\) の8条件で速度は 11.7467–11.7978 m/s、二関節3筋の最大 \(\tilde l^{M}\) は前傾とともに増加した。</td></tr>
<tr><td><span class="lab labR">Fact</span></td><td>BFsh の最大 \(\tilde l^{M}\) 端点変化は −0.32% であった。</td></tr>
<tr><td><span class="lab labR">Fact</span></td><td>tree-rigid の MTU 長差は 0、femur-fixed は adaptive 二関節差の 89.6–95.8% であった。</td></tr>
<tr><td><span class="lab labR">Fact</span></td><td>\(w=0.1\) の3ウォームスタート経路で速度変化平均 −0.340%、代理指標変化平均 −5.189% であった。</td></tr>
<tr><td><span class="lab labP">Interpretation</span></td><td>前傾–線維長関係は骨盤–大腿協調、特に股関節屈曲を介する可能性が高い。</td></tr>
<tr><td><span class="lab labP">Interpretation</span></td><td>BFsh の不変性は股関節をまたぐことの機序特異性を支持する。</td></tr>
<tr><td><span class="lab labN">Hypothesis</span></td><td>実走者で接地時骨盤前傾を減らすと終末遊脚期の生体内筋束伸長を減らせる（未検証）。</td></tr>
<tr><td><span class="lab labN">Hypothesis</span></td><td>代理指標低下候補が肉離れリスクを下げる（未検証）。</td></tr>
</tbody></table></div>

<h3 id="appendix-c">付録C. 提出版確定前の検証課題</h3>
<ol class="limlist">
<li>source MAT を公開または審査者が取得可能な保管場所に置き、SHA256 を固定する。</li>
<li>\(N=50\) と \(N=100\) で同一の探索境界系列を用いた再 solve を行い、純粋なメッシュ収束を確認する。</li>
<li>至適筋線維長・腱コンプライアンス・受動力–長さ特性・最大等尺性筋力の感度解析を行う。</li>
<li>不成功試行を含む全条件フローと除外理由を保存・報告する。</li>
<li>\(N=100\) 複合目的関数を複数ウォームスタート経路で確認する。</li>
<li>Spearman 順位計算を tie 補正済み標準実装へ統一する。</li>
<li>筋25 の変更意図を確認し、コメント修正または全条件再計算を行う。</li>
<li>境界条件解析を正規化位相対応で再生成し、source file を hash で固定する。</li>
<li>README・publication runner・環境 lockfile・hash を論文の再現手順と一致させる。</li>
</ol>
<p class="fine">来歴：監査対象の公開状態 <code>e7b8de9</code>、派生結果の simulation commit <code>59877aa</code>、analysis commit <code>bb0433a</code>。
本 Web 版の図は <code>output/thesis_figures_final_20260819_163600/</code> の QA 済み図（23項目 PASS）を用いており、数値は独立監査
<code>Results/Independent_Audit_20260819/</code> と一致する。</p>
'''


# --------------------------------------------------------------------------- #
#  Section ordering (consumed by build_site.py to build TOC + body)
# --------------------------------------------------------------------------- #
SECTIONS = [
    {"id": "readme",      "num": "",   "title": "この補足ドキュメントについて",           "body": READ_ME},
    {"id": "abstract",    "num": "",   "title": "要旨",                                     "body": ABSTRACT},
    {"id": "nomen",       "num": "",   "title": "用語・略語・記号の定義",                   "body": NOMEN},
    {"id": "intro",       "num": "1",  "title": "緒言",                                     "body": INTRO},
    {"id": "methods",     "num": "2",  "title": "方法",                                     "body": METHODS_1 + METHODS_2 + METHODS_3 + METHODS_MATH},
    {"id": "results",     "num": "3",  "title": "結果",                                     "body": RESULTS_1 + RESULTS_2 + RESULTS_3 + RESULTS_4 + RESULTS_5 + RESULTS_6 + RESULTS_7 + RESULTS_8},
    {"id": "discussion",  "num": "4",  "title": "考察",                                     "body": DISCUSSION},
    {"id": "limitations", "num": "5",  "title": "研究の限界",                               "body": LIMITATIONS},
    {"id": "conclusion",  "num": "6",  "title": "結論",                                     "body": CONCLUSION},
    {"id": "references",  "num": "",   "title": "参考文献",                                 "body": REFERENCES},
    {"id": "appendix",    "num": "",   "title": "付録",                                     "body": APPENDIX},
]







