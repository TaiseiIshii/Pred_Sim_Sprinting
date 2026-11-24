#!/usr/bin/env python
"""Build a styled PDF from the integrated report Markdown.

Pipeline: Markdown -> HTML (markdown-it-py) -> PDF (headless Edge print-to-pdf).
- Renders Mermaid diagrams from a locally bundled mermaid.min.js (offline-safe).
- Rewrites relative image paths to absolute file:/// URIs so figures embed.
- Uses Windows Japanese fonts (Yu Gothic / Meiryo).

Usage:
    python docs/build_report_pdf.py [input.md] [output.pdf]
"""
from __future__ import annotations

import os
import re
import sys
import json
import time
import base64
import shutil
import socket
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from markdown_it import MarkdownIt

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ASSETS = Path(__file__).resolve().parent / "_assets"


def latex_to_text(s: str) -> str:
    """Very small LaTeX->readable-HTML shim (no JS math engine needed)."""
    r = s
    r = r.replace(r"\operatorname{smoothpos}", "smoothpos")
    r = re.sub(r"\\text\{([^}]*)\}", r"\1", r)
    r = re.sub(r"\\operatorname\{([^}]*)\}", r"\1", r)
    r = r.replace(r"\tilde l_{M}", "l\u0303M").replace(r"\tilde l_M", "l\u0303M")
    r = r.replace(r"\cdot", "\u00b7").replace(r"\times", "\u00d7")
    r = r.replace(r"\sum", "\u03a3")
    r = r.replace(r"\approx", "\u2248").replace(r"\le", "\u2264").replace(r"\ge", "\u2265")
    r = r.replace(r"\big(", "(").replace(r"\big)", ")")
    r = r.replace(r"\!", "").replace(r"\,", " ").replace(r"\ ", " ")
    r = r.replace("^2", "\u00b2")
    r = re.sub(r"_\{([^}]*)\}", r"(\1)", r)
    r = re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", r)
    r = r.replace("-", "\u2212")
    return r.strip()


def preprocess_math(md: str) -> str:
    md = re.sub(r"\$\$(.+?)\$\$", lambda m: f'\n<div class="math-block">{latex_to_text(m.group(1))}</div>\n',
                md, flags=re.S)
    md = re.sub(r"\$([^$\n]+?)\$", lambda m: f'<span class="math-inline">{latex_to_text(m.group(1))}</span>', md)
    return md


def extract_mermaid(md: str):
    blocks = []

    def repl(m):
        blocks.append(m.group(1))
        return f"\n@@MERMAID{len(blocks) - 1}@@\n"

    md = re.sub(r"```mermaid\s*\n(.*?)```", repl, md, flags=re.S)
    return md, blocks


def abspath_images(html: str, base_dir: Path) -> str:
    def repl(m):
        src = m.group(2)
        if src.startswith(("http://", "https://", "file:", "data:")):
            return m.group(0)
        p = (base_dir / src).resolve()
        uri = "file:///" + str(p).replace("\\", "/")
        return f'{m.group(1)}="{uri}"'

    return re.sub(r'(src)="([^"]+)"', repl, html)


TEMPLATE = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<script src="{mermaid_js}"></script>
<style>
:root {{ --accent:#1f6feb; --accent2:#0b7a5b; --warn:#b45309; --ink:#1c2530; --muted:#5b6673; --line:#d5dbe2; }}
* {{ box-sizing:border-box; }}
html {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ font-family:"Yu Gothic","Meiryo","Segoe UI",sans-serif; color:var(--ink);
  line-height:1.85; font-size:11pt; margin:0; }}
.wrap {{ max-width:900px; margin:0 auto; padding:6px 10px 40px; }}
h1 {{ font-size:22pt; line-height:1.35; border-bottom:4px solid var(--accent); padding-bottom:10px; margin:6px 0 4px; }}
h2 {{ font-size:16pt; color:var(--accent); border-left:7px solid var(--accent); padding:3px 0 3px 12px;
  margin:26px 0 10px; break-after:avoid; }}
h3 {{ font-size:13pt; color:var(--accent2); margin:18px 0 8px; break-after:avoid; }}
h4 {{ font-size:11.5pt; color:var(--ink); margin:14px 0 6px; }}
p {{ margin:8px 0; }}
a {{ color:var(--accent); text-decoration:none; }}
strong {{ color:#111; }}
hr {{ border:none; border-top:1px solid var(--line); margin:22px 0; }}
img {{ max-width:100%; height:auto; display:block; margin:12px auto; border:1px solid var(--line);
  border-radius:8px; padding:4px; background:#fff; break-inside:avoid; }}
table {{ border-collapse:collapse; width:100%; margin:12px 0; font-size:10pt; break-inside:avoid; }}
th,td {{ border:1px solid var(--line); padding:7px 10px; text-align:left; vertical-align:top; }}
th {{ background:var(--accent); color:#fff; font-weight:600; }}
tr:nth-child(even) td {{ background:#f4f7fb; }}
blockquote {{ margin:12px 0; padding:10px 16px; background:#f2f8ff; border-left:5px solid var(--accent);
  border-radius:0 8px 8px 0; color:#233; }}
blockquote strong {{ color:var(--accent); }}
code {{ background:#eef1f5; padding:1px 6px; border-radius:5px; font-family:"Consolas",monospace; font-size:0.92em; }}
pre {{ background:#0d1117; color:#e6edf3; padding:12px 14px; border-radius:8px; overflow:auto; }}
pre code {{ background:none; color:inherit; }}
ul,ol {{ margin:8px 0; padding-left:26px; }}
li {{ margin:4px 0; }}
.math-block {{ text-align:center; font-family:"Cambria Math","Segoe UI Symbol",serif; font-size:12.5pt;
  background:#f7f9fc; border:1px solid var(--line); border-radius:8px; padding:12px; margin:12px 0; }}
.math-inline {{ font-family:"Cambria Math","Segoe UI Symbol",serif; }}
.mermaid {{ background:#fbfdff; border:1px solid var(--line); border-radius:10px; padding:10px; margin:14px 0;
  text-align:center; break-inside:avoid; }}
h1+h2, h1+p {{ break-before:avoid; }}
@page {{ size:A4; margin:14mm 12mm; }}
</style></head>
<body><div class="wrap">
{body}
</div>
<script>
window.addEventListener('load', function() {{
  try {{ mermaid.initialize({{ startOnLoad:false, theme:'default', flowchart:{{ htmlLabels:true, curve:'basis' }} }});
        mermaid.run(); }} catch(e) {{}}
}});
</script>
</body></html>
"""


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def print_pdf_cdp(html_url: str, pdf_path: Path, mermaid_count: int = 0, edge: str = EDGE):
    """Print a local HTML page to PDF via the Chrome DevTools Protocol.

    Uses displayHeaderFooter:false (no date/URL/page footer) and waits for
    Mermaid diagrams to finish rendering before printing.
    """
    import websocket  # websocket-client

    port = _free_port()
    udir = tempfile.mkdtemp()
    proc = subprocess.Popen(
        [
            edge, "--headless=new", "--disable-gpu", "--no-first-run",
            "--no-default-browser-check", "--allow-file-access-from-files",
            "--disable-extensions", "--mute-audio",
            "--remote-allow-origins=*",
            f"--remote-debugging-port={port}", f"--user-data-dir={udir}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    ws = None
    try:
        ver = None
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1) as r:
                    ver = json.load(r)
                break
            except Exception:
                time.sleep(0.25)
        if not ver:
            raise RuntimeError("DevTools endpoint not reachable")

        ws = websocket.create_connection(ver["webSocketDebuggerUrl"], max_size=None, timeout=120)
        counter = {"n": 0}

        def cmd(method, params=None, sid=None):
            counter["n"] += 1
            mid = counter["n"]
            msg = {"id": mid, "method": method, "params": params or {}}
            if sid:
                msg["sessionId"] = sid
            ws.send(json.dumps(msg))
            while True:
                resp = json.loads(ws.recv())
                if resp.get("id") == mid:
                    if "error" in resp:
                        raise RuntimeError(f"{method}: {resp['error']}")
                    return resp.get("result", {})

        target = cmd("Target.createTarget", {"url": "about:blank"})
        sid = cmd("Target.attachToTarget", {"targetId": target["targetId"], "flatten": True})["sessionId"]
        cmd("Page.enable", sid=sid)
        cmd("Runtime.enable", sid=sid)
        cmd("Page.navigate", {"url": html_url}, sid=sid)

        # Wait for document ready.
        for _ in range(80):
            r = cmd("Runtime.evaluate",
                    {"expression": "document.readyState", "returnByValue": True}, sid=sid)
            if r.get("result", {}).get("value") == "complete":
                break
            time.sleep(0.2)

        # Wait for Mermaid SVGs to appear.
        if mermaid_count:
            for _ in range(60):
                r = cmd("Runtime.evaluate",
                        {"expression": "document.querySelectorAll('.mermaid svg').length",
                         "returnByValue": True}, sid=sid)
                if int(r.get("result", {}).get("value", 0) or 0) >= mermaid_count:
                    break
                time.sleep(0.25)
        time.sleep(0.8)

        res = cmd("Page.printToPDF", {
            "printBackground": True,
            "displayHeaderFooter": False,
            "preferCSSPageSize": True,
            "transferMode": "ReturnAsStream",
        }, sid=sid)

        handle = res["stream"]
        buf = bytearray()
        while True:
            chunk = cmd("IO.read", {"handle": handle, "size": 1 << 20}, sid=sid)
            payload = chunk.get("data", "")
            if chunk.get("base64Encoded"):
                buf += base64.b64decode(payload)
            else:
                buf += payload.encode("latin-1")
            if chunk.get("eof"):
                break
        cmd("IO.close", {"handle": handle}, sid=sid)
        Path(pdf_path).write_bytes(bytes(buf))
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        shutil.rmtree(udir, ignore_errors=True)


def main():
    args = sys.argv[1:]
    docs = Path(__file__).resolve().parent
    md_path = Path(args[0]) if len(args) > 0 else docs / "Hamstring_Injury_SpeedSafety_Integrated_Report.md"
    pdf_path = Path(args[1]) if len(args) > 1 else md_path.with_suffix(".pdf")
    md_path = md_path.resolve()
    base_dir = md_path.parent

    md_text = md_path.read_text(encoding="utf-8")
    md_text, mermaids = extract_mermaid(md_text)
    md_text = preprocess_math(md_text)

    mdit = MarkdownIt("default", {"html": True, "breaks": False, "linkify": False})
    html_body = mdit.render(md_text)

    # Restore mermaid diagrams as <div class="mermaid">.
    def merm_repl(m):
        idx = int(m.group(1))
        return f'<div class="mermaid">{mermaids[idx]}</div>'

    html_body = re.sub(r"<p>@@MERMAID(\d+)@@</p>", merm_repl, html_body)
    html_body = re.sub(r"@@MERMAID(\d+)@@", merm_repl, html_body)

    html_body = abspath_images(html_body, base_dir)

    mermaid_js = "file:///" + str((ASSETS / "mermaid.min.js").resolve()).replace("\\", "/")
    html = TEMPLATE.format(body=html_body, mermaid_js=mermaid_js)

    html_path = md_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"[ok] HTML written: {html_path}")

    if not Path(EDGE).exists():
        print(f"[warn] Edge not found at {EDGE}; HTML created but PDF skipped.")
        return

    mermaid_count = html_body.count('class="mermaid"')
    html_url = "file:///" + str(html_path).replace("\\", "/")
    print("[..] Printing PDF via DevTools Protocol ...")
    print_pdf_cdp(html_url, pdf_path, mermaid_count)
    if pdf_path.exists() and pdf_path.stat().st_size > 0:
        print(f"[ok] PDF written: {pdf_path} ({pdf_path.stat().st_size/1024:.0f} KB)")
    else:
        print("[err] PDF not created.")
        sys.exit(1)


if __name__ == "__main__":
    main()
