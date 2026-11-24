from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MD = ROOT / "修士論文本番原稿_最終実装監査版.md"
HTML = ROOT / "修士論文本番原稿_最終実装監査版.html"
AUDIT = ROOT / "最終実装・論文監査報告.md"

text = MD.read_text(encoding="utf-8")
html = HTML.read_text(encoding="utf-8")
audit = AUDIT.read_text(encoding="utf-8")

required = [
    "主要TDPT解析の評価項目は、基準脚1ストライド全体",
    "速度–負荷Pareto解析の報告代理指標",
    "終末遊脚期窓内ピーク",
    "筋25パラメータのコメント–実装不一致",
    "femur-fixed/adaptive比は89.6–95.8%",
    "統合テストの不在",
    "純粋な活性化由来の能動力と完全に同義とは扱わない",
]
for item in required:
    assert item in text, item

for stale in [
    "二関節3筋の1ストライド最大lMtilde平均の変化",
    "femur-fixed条件のピーク変化はadaptive条件の84.4–88.8%",
    "その終末遊脚期ピーク変化はadaptive条件の84.4–88.8%",
]:
    assert stale not in text, stale

assert "Blocker 1" in audit and "Blocker 2" in audit
assert "Needs revision" in audit and "No-Go（現状）" in audit
assert "<html" in html and "</html>" in html
assert len(re.findall(r"<h[1-6]", html)) >= 20
assert html.count("<table>") >= 5

print("PASS final audit manuscript and report checks")
