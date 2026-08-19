# -*- coding: utf-8 -*-
"""
build_site.py -- assemble the self-contained GitHub Pages thesis site.

Steps:
  1. copy figure PNGs (from output/thesis_figures_final_.../figures/png) and the
     two key musculoskeletal videos into site/assets/;
  2. render index.html (inline CSS + MathJax v3 CDN, sticky TOC, figure/video
     blocks, tables) from the ordered sections defined in content_ja.py;
  3. write .nojekyll so GitHub Pages serves the static files verbatim.

Run:  python site/build_site.py
Numbers are presentational (already reproduced by the independent audit); this
script does not re-derive them.
"""
import os
import shutil
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import content_ja as C  # noqa: E402

FIG_SRC = os.path.join(REPO, "output", "thesis_figures_final_20260819_163600", "figures", "png")
ASSET_FIG = os.path.join(HERE, "assets", "fig")
ASSET_VID = os.path.join(HERE, "assets", "video")

# Quick-access figure/video navigation (anchor, label).
FIGNAV = [
    ("fig-1", "図1 研究ロジック"),
    ("fig-4", "図4 基準妥当性"),
    ("vid-td", "動画1 接地骨盤傾斜アニメ"),
    ("fig-2", "図2 主結果"),
    ("fig-3", "図3 波形・時相"),
    ("figS1", "補足S1 力–長さ作用域"),
    ("figS2", "補足S2 筋×指標変化率"),
    ("fig-5", "図5 機序分解"),
    ("fig-7", "図7 速度–負荷パレート"),
    ("vid-pareto", "動画2 候補動作"),
    ("fig-6", "図6 数値頑健性"),
    ("figS4", "補足S4 解像度頑健性"),
    ("figS3", "補足S3 パラメータ感度"),
]


def copy_assets():
    os.makedirs(ASSET_FIG, exist_ok=True)
    os.makedirs(ASSET_VID, exist_ok=True)
    for fn in C.FIGURE_FILES:
        src = os.path.join(FIG_SRC, fn)
        if not os.path.isfile(src):
            raise SystemExit("missing figure: " + src)
        shutil.copy2(src, os.path.join(ASSET_FIG, fn))
    for rel, dst in C.VIDEO_FILES:
        src = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.isfile(src):
            raise SystemExit("missing video: " + src)
        shutil.copy2(src, os.path.join(ASSET_VID, dst))
    print("copied", len(C.FIGURE_FILES), "figures and", len(C.VIDEO_FILES), "video files")


def build_toc():
    items = []
    for s in C.SECTIONS:
        label = (s["num"] + ". " if s["num"] else "") + s["title"]
        items.append('<li><a href="#' + s["id"] + '">' + label + "</a></li>")
    fignav = "".join('<li><a href="#' + a + '">' + t + "</a></li>" for a, t in FIGNAV)
    return (
        '<nav class="sidebar" aria-label="目次">'
        '<div class="tocbox">'
        '<p class="toctitle">目次</p><ol class="toc">' + "".join(items) + "</ol>"
        '<details class="fignav"><summary>図・動画へジャンプ</summary>'
        '<ul>' + fignav + "</ul></details>"
        '</div></nav>'
    )


def build_body():
    out = []
    for s in C.SECTIONS:
        head = (('<span class="secnum">' + s["num"] + "</span> ") if s["num"] else "") + s["title"]
        out.append(
            '<section id="' + s["id"] + '" class="sec">'
            '<h2>' + head + "</h2>" + s["body"] + "</section>"
        )
    return "".join(out)


CSS = r'''
:root{
  --ink:#161a1d; --muted:#5b6670; --line:#e3e8ee; --bg:#ffffff; --soft:#f6f8fb;
  --brand:#1b4f8a; --brand2:#2166ac; --green:#1b7837; --amber:#b5730f; --purple:#762a83;
  --maxw:1180px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth; scroll-padding-top:14px}
body{margin:0; background:var(--bg); color:var(--ink);
  font-family:"Yu Gothic","YuGothic","Meiryo","Hiragino Kaku Gothic ProN",system-ui,sans-serif;
  line-height:1.85; font-size:16.5px; -webkit-text-size-adjust:100%}
a{color:var(--brand2); text-decoration:none}
a:hover{text-decoration:underline}

/* header band */
header.hero{background:linear-gradient(135deg,#12385f,#1b4f8a 55%,#2166ac);
  color:#fff; padding:34px 20px 30px}
header.hero .inner{max-width:var(--maxw); margin:0 auto}
header.hero h1{margin:0 0 8px; font-size:1.5rem; line-height:1.5; font-weight:700}
header.hero p.sub{margin:0 0 14px; font-size:.98rem; color:#dbe7f5}
.chips{display:flex; flex-wrap:wrap; gap:8px}
.chip{background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.28);
  padding:3px 11px; border-radius:999px; font-size:.8rem; color:#eef5fc}

/* layout */
.wrap{display:grid; grid-template-columns:290px minmax(0,1fr); gap:34px;
  max-width:var(--maxw); margin:26px auto 0; padding:0 20px}
.sidebar{position:sticky; top:12px; align-self:start; max-height:calc(100vh - 24px); overflow:auto}
.tocbox{background:var(--soft); border:1px solid var(--line); border-radius:12px; padding:14px 14px 10px}
.toctitle{margin:0 0 8px; font-weight:700; font-size:.82rem; letter-spacing:.06em; color:var(--muted)}
ol.toc{margin:0; padding:0 0 0 1.2em; font-size:.9rem}
ol.toc li{margin:.28em 0}
ol.toc a.active{font-weight:700; color:var(--brand)}
.fignav{margin-top:10px; border-top:1px dashed var(--line); padding-top:8px}
.fignav summary{cursor:pointer; font-size:.82rem; color:var(--muted); font-weight:700}
.fignav ul{margin:8px 0 0; padding:0 0 0 1.1em; font-size:.84rem}
.fignav li{margin:.22em 0}
.main{min-width:0}

/* sections */
section.sec{margin:0 0 30px; padding:0 0 6px; border-bottom:1px solid var(--line)}
section.sec h2{font-size:1.28rem; color:var(--brand); margin:26px 0 12px;
  padding:6px 0 6px 12px; border-left:6px solid var(--brand2); line-height:1.45}
.secnum{color:var(--brand2); font-weight:800; margin-right:.15em}
section.sec h3{font-size:1.06rem; color:#12385f; margin:22px 0 8px; padding-left:2px;
  border-bottom:2px solid var(--line); padding-bottom:4px}
p{margin:.55em 0}
.fine{font-size:.85rem; color:var(--muted)}
.term{background:#eef3f9; border-bottom:1px dotted #9db6d2; padding:0 2px}

/* how-to / abstract intro */
.howto{background:var(--soft); border:1px solid var(--line); border-radius:12px; padding:14px 18px}
.howto ul{margin:.4em 0 0; padding-left:1.3em}
.howto li{margin:.3em 0}

/* figures & videos */
figure.figblock{margin:20px 0; padding:12px; background:#fff; border:1px solid var(--line);
  border-radius:12px; box-shadow:0 1px 3px rgba(20,40,70,.05)}
figure.figblock img, figure.figblock video{width:100%; height:auto; border-radius:8px;
  background:#fff; display:block}
figure.figblock video{border:1px solid var(--line)}
.zia{display:block; cursor:zoom-in}
figcaption{margin-top:10px; font-size:.93rem}
.figtag{margin:.2em 0 .5em; font-size:1rem; color:var(--brand)}
.purpose{color:#0b3d66; background:#f0f6fc; border-left:3px solid var(--brand2);
  padding:6px 12px; margin:.4em 0; border-radius:0 6px 6px 0}
.result{background:#f1f8f2; border-left:3px solid var(--green); padding:6px 12px;
  margin:.4em 0; border-radius:0 6px 6px 0}
.note{background:#fff7ea; border-left:3px solid var(--amber); padding:6px 12px;
  margin:.4em 0; border-radius:0 6px 6px 0}
.capen{font-size:.82rem; color:var(--muted); margin:.4em 0 .1em}

/* inline labels */
.lab{display:inline-block; font-size:.72rem; font-weight:700; color:#fff;
  padding:1px 8px; border-radius:999px; margin-right:6px; vertical-align:.08em; white-space:nowrap}
.labP{background:var(--brand2)}
.labR{background:var(--green)}
.labN{background:var(--amber)}

/* callouts */
.callout{margin:14px 0; padding:11px 15px; border-radius:8px; font-size:.95rem;
  border:1px solid var(--line); border-left-width:5px}
.callout .colabel{font-weight:800; margin-right:.4em}
.callout.fact{background:#f1f8f2; border-left-color:var(--green)}
.callout.interp{background:#eff5fb; border-left-color:var(--brand2)}
.callout.limit{background:#fdf1ee; border-left-color:#c0442e}
.callout.warn{background:#fff7ea; border-left-color:var(--amber)}

/* tables */
.tablewrap{overflow-x:auto; margin:14px 0; border:1px solid var(--line); border-radius:10px}
table{border-collapse:collapse; width:100%; font-size:.92rem; background:#fff}
table.small{font-size:.85rem}
thead th{background:#eef3f9; color:#12385f; text-align:left; font-weight:700}
th,td{padding:7px 11px; border-bottom:1px solid var(--line); vertical-align:top}
tbody tr:nth-child(even){background:#fafcfe}
tbody tr:hover{background:#f3f8fd}

/* references / lists */
ol.reflist{padding-left:1.4em; font-size:.9rem}
ol.reflist li{margin:.55em 0; padding-left:.2em}
ol.limlist{padding-left:1.3em}
ol.limlist li{margin:.5em 0}
a.cref{font-size:.82em; vertical-align:.3em; color:var(--brand2); font-weight:700; padding:0 1px}
:target{scroll-margin-top:16px}
li:target, section:target > h2{animation:flash 1.6s ease}
@keyframes flash{from{background:#fff3c4}to{background:transparent}}

/* math sizing */
mjx-container{overflow-x:auto; overflow-y:hidden; max-width:100%}
mjx-container[display="true"]{margin:.7em 0}

/* footer + top link */
footer{max-width:var(--maxw); margin:20px auto 60px; padding:18px 20px;
  border-top:1px solid var(--line); color:var(--muted); font-size:.85rem}
#toplink{position:fixed; right:16px; bottom:16px; background:var(--brand);
  color:#fff; width:44px; height:44px; border-radius:50%; display:flex;
  align-items:center; justify-content:center; box-shadow:0 3px 10px rgba(20,40,70,.28);
  font-size:1.2rem; opacity:.86}
#toplink:hover{opacity:1; text-decoration:none}

@media (max-width:900px){
  .wrap{grid-template-columns:1fr; gap:16px}
  .sidebar{position:static; max-height:none; overflow:visible}
  ol.toc{columns:2; -webkit-columns:2}
  header.hero h1{font-size:1.25rem}
}
@media print{
  header.hero{background:#12385f !important; -webkit-print-color-adjust:exact; print-color-adjust:exact}
  .sidebar,#toplink{display:none}
  .wrap{grid-template-columns:1fr; margin-top:8px}
  section.sec{break-inside:avoid-page}
  figure.figblock{break-inside:avoid}
}
'''

MATHJAX = r'''
<script>
window.MathJax = {
  tex: { inlineMath: [['\\(','\\)']], displayMath: [['\\[','\\]']], tags:'none' },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] },
  svg: { fontCache: 'global' }
};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
'''

ACTIVE_JS = r'''
<script>
(function(){
  try{
    var links = {};
    document.querySelectorAll('ol.toc a').forEach(function(a){
      links[a.getAttribute('href').slice(1)] = a;
    });
    var obs = new IntersectionObserver(function(es){
      es.forEach(function(e){
        var a = links[e.target.id];
        if(!a) return;
        if(e.isIntersecting){
          document.querySelectorAll('ol.toc a.active').forEach(function(x){x.classList.remove('active');});
          a.classList.add('active');
        }
      });
    }, {rootMargin:'-10% 0px -80% 0px'});
    document.querySelectorAll('section.sec').forEach(function(s){obs.observe(s);});
  }catch(e){}
})();
</script>
'''

PAGE = r'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="@@SUBTITLE@@">
<title>@@TITLE@@</title>
<style>@@CSS@@</style>
@@MATHJAX@@
</head>
<body>
<header class="hero"><div class="inner">
<h1>@@TITLE@@</h1>
<p class="sub">@@SUBTITLE@@</p>
<div class="chips">
<span class="chip">予測筋骨格シミュレーション</span>
<span class="chip">国際水準男子スプリンター1名 / 単一モデル計算実験</span>
<span class="chip">主解析 N=100・8条件</span>
<span class="chip">図11点＋動画2点</span>
<span class="chip">commit e7b8de9</span>
<span class="chip">QA 23/23 PASS</span>
<span class="chip">生成日 @@DATE@@</span>
</div>
</div></header>
<div class="wrap">
@@TOC@@
<main class="main">
@@BODY@@
</main>
</div>
<footer>
本ページは修士論文（<code>docs/修士論文学位審査提出候補稿_日本語.md</code>）の Web 補足版であり、単一予測モデル内の
<b>相関・機序</b>を示すものである。肉離れの<b>因果</b>・受傷リスク低減・安全姿勢・個人一般化・絶対 GRF 妥当性は主張しない。
図は <code>output/thesis_figures_final_20260819_163600/</code>（自動 QA 23項目 PASS）から、動画は
<code>Results/PelvicTD_Study/</code> および <code>Results/HamPareto_Study/</code> から生成した。数値は独立監査
<code>Results/Independent_Audit_20260819/</code> と一致する。&copy; Taisei Ishii.
</footer>
<a id="toplink" href="#top" aria-label="ページ先頭へ">&#8593;</a>
@@ACTIVE_JS@@
</body>
</html>'''


def main():
    copy_assets()
    doc = PAGE
    doc = doc.replace("@@CSS@@", CSS)
    doc = doc.replace("@@MATHJAX@@", MATHJAX)
    doc = doc.replace("@@ACTIVE_JS@@", ACTIVE_JS)
    doc = doc.replace("@@TITLE@@", C.TITLE)
    doc = doc.replace("@@SUBTITLE@@", C.SUBTITLE)
    doc = doc.replace("@@DATE@@", datetime.date.today().isoformat())
    doc = doc.replace("@@TOC@@", build_toc())
    doc = doc.replace("@@BODY@@", build_body())

    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    with open(os.path.join(HERE, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")
    print("wrote index.html (%d chars)" % len(doc))


if __name__ == "__main__":
    main()
