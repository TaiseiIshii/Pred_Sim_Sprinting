#!/usr/bin/env python3
"""Package a markdown report and its referenced image/GIF assets into a single folder and zip it.
Usage: python docs/package_report.py [--md PATH] [--out DIR] [--zip NAME]
Defaults:
  --md docs/Hamstring_Injury_SpeedSafety_Integrated_Report.md
  --out docs/report_bundle
  --zip docs/Hamstring_Report_bundle
"""
import re
import sys
import shutil
from pathlib import Path
import argparse

IMAGE_REGEX = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
HTML_IMG_REGEX = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']')


def find_image_paths(md_text):
    paths = []
    for m in IMAGE_REGEX.finditer(md_text):
        paths.append(m.group(1).strip())
    for m in HTML_IMG_REGEX.finditer(md_text):
        paths.append(m.group(1).strip())
    # Remove anchors or title parts: image.png#fragment or image.png "title"
    clean = []
    for p in paths:
        # strip title after space
        if ' ' in p and not p.startswith('http'):
            p = p.split(' ')[0]
        # strip fragments
        p = p.split('#')[0]
        clean.append(p)
    # unique while preserving order
    seen = set()
    out = []
    for p in clean:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def copy_asset(src_path: Path, workspace_root: Path, out_root: Path):
    if not src_path.exists():
        return False, f"missing: {src_path}"
    try:
        try:
            rel = src_path.relative_to(workspace_root)
            dest = out_root / rel
        except Exception:
            # external file: put into assets/external/<basename>
            dest = out_root / 'assets' / 'external' / src_path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest)
        return True, str(dest)
    except Exception as e:
        return False, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--md', default='docs/Hamstring_Injury_SpeedSafety_Integrated_Report.md')
    p.add_argument('--out', default='docs/report_bundle')
    p.add_argument('--zip', default='docs/Hamstring_Report_bundle')
    args = p.parse_args()

    md_path = Path(args.md)
    workspace_root = Path.cwd()
    out_root = Path(args.out)
    zip_base = Path(args.zip)

    if not md_path.exists():
        print(f"ERROR: md file not found: {md_path}")
        sys.exit(2)

    out_root.mkdir(parents=True, exist_ok=True)

    md_text = md_path.read_text(encoding='utf-8')
    img_paths = find_image_paths(md_text)

    print(f"Found {len(img_paths)} referenced asset(s).")

    results = []
    # resolve relative paths relative to the markdown file location
    md_base = md_path.parent.resolve()
    for pth in img_paths:
        # skip remote URLs
        if pth.startswith('http://') or pth.startswith('https://'):
            results.append((pth, 'skipped (remote URL)'))
            continue
        # resolve relative to the markdown file's folder (handles ../ references correctly)
        candidate = (md_base / pth).resolve()
        ok, info = copy_asset(candidate, workspace_root, out_root)
        results.append((pth, 'copied:' + info if ok else info))

    # copy the md file into out_root preserving relative path
    try:
        try:
            md_rel = md_path.resolve().relative_to(workspace_root.resolve())
            md_dest = out_root / md_rel
        except Exception:
            md_dest = out_root / md_path.name
        md_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(md_path, md_dest)
    except Exception as e:
        print(f"ERROR copying md: {e}")
        sys.exit(3)

    # create zip
    zip_path = shutil.make_archive(str(zip_base), 'zip', root_dir=out_root)
    print("-- Summary --")
    for r in results:
        print(f"{r[0]} -> {r[1]}")
    print(f"MD copied to: {md_dest}")
    print(f"Bundle folder: {out_root}")
    print(f"Zip archive created: {zip_path}")


if __name__ == '__main__':
    main()
