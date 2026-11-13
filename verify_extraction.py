#!/usr/bin/env python3
"""Verify the extraction is faithful: rebuild the page from dist/tokens.css +
dist/components.css + the ORIGINAL markup, render it, and compare to mock.html's own
render. Must be pixel-identical, else the extraction lost something.

Fonts are pinned (the artifact's score is nondeterministic otherwise — proven: unpinned
renders land in 2 distinct states).
"""
import os, re, subprocess, sys

LIB = "/home/ubuntu/workspace/cherry-blossom"
MOCK = "/home/ubuntu/workspace/notify-mock/mock.html"
OUT = os.path.join(LIB, "verify")
os.makedirs(OUT, exist_ok=True)
W, H = 782, 1676

# ---- pin fonts (same technique as probe_components.py; the artifact needs it)
FONTDIR = os.path.join(LIB, "fonts")
API = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
       "&family=JetBrains+Mono:wght@400;500;700&display=swap")


def ensure_fonts():
    os.makedirs(FONTDIR, exist_ok=True)
    css = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", "Mozilla/4.0", API],
                         capture_output=True, text=True).stdout
    faces, seen = [], set()
    for b in re.findall(r"@font-face\s*\{(.*?)\}", css, re.S):
        fam = re.search(r"font-family:\s*'([^']+)'", b).group(1)
        wt = re.search(r"font-weight:\s*(\d+)", b).group(1)
        m = re.search(r"url\((https://[^)]+\.(?:ttf|woff2))\)", b)
        if not m or (fam, wt) in seen:
            continue
        seen.add((fam, wt))
        ext = m.group(1).rsplit(".", 1)[1]
        p = os.path.join(FONTDIR, f"{fam.replace(' ', '')}-{wt}.{ext}")
        if not os.path.exists(p) or os.path.getsize(p) < 5000:
            subprocess.run(["curl", "-sL", "--max-time", "60", "-A", "Mozilla/4.0",
                            "-o", p, m.group(1)], capture_output=True)
        faces.append((fam, wt, p))
    return faces


FACE_CSS = "\n".join(
    f"@font-face{{font-family:'{f}';font-style:normal;font-weight:{w};"
    f"font-display:block;src:url('file://{p}') format('{p.rsplit('.', 1)[1]}');}}"
    for f, w, p in ensure_fonts())
LINK_RE = re.compile(r'<link href="https://fonts\.googleapis\.com/css2[^"]*" rel="stylesheet">')

src_html = open(MOCK).read()
body = re.search(r"(<body>.*</body>)", src_html, re.S).group(1)
src_css = re.search(r"<style>(.*?)</style>", src_html, re.S).group(1)

tokens = open(f"{LIB}/dist/tokens.css").read()
components = open(f"{LIB}/dist/components.css").read()
pinned_src = LINK_RE.sub("<style>\n" + FACE_CSS + "\n</style>", src_html)

# A: original, fonts pinned.  B: rebuilt from the extracted CSS, fonts pinned.
rebuilt = (
    "<!doctype html><html><head><meta charset='utf-8'>\n<style>\n" + FACE_CSS + "\n</style>\n"
    "<style>\n" + tokens + "\n</style>\n<style>\n" + components + "\n</style>\n"
    "</head>\n" + body + "\n</html>\n")

open(f"{OUT}/pinned_original.html", "w").write(pinned_src)
open(f"{OUT}/rebuilt.html", "w").write(rebuilt)


def render(path, png):
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-sandbox", "--force-device-scale-factor=1",
                    f"--window-size={W},{H}", f"--screenshot={png}",
                    "file://" + os.path.abspath(path)], check=False, capture_output=True)


render(f"{OUT}/pinned_original.html", f"{OUT}/a_original.png")
render(f"{OUT}/rebuilt.html", f"{OUT}/b_rebuilt.png")

# render twice each to prove determinism before trusting the comparison
render(f"{OUT}/rebuilt.html", f"{OUT}/b_rebuilt2.png")

r = subprocess.run(["/home/ubuntu/.venv-vision/bin/python", "-c", f"""
import numpy as np
from PIL import Image
def L(p): return np.array(Image.open(p).convert('RGB')).astype(int)
a=L("{OUT}/a_original.png"); b=L("{OUT}/b_rebuilt.png"); b2=L("{OUT}/b_rebuilt2.png")
print("dims", a.shape, b.shape)
det=int((np.abs(b-b2).sum(axis=2)>0).sum())
print(f"determinism: rebuilt vs rebuilt  differing px = {{det}}  {{'OK' if det==0 else 'NONDETERMINISTIC'}}")
d=int((np.abs(a-b).sum(axis=2)>0).sum())
tot=a.shape[0]*a.shape[1]
print(f"FAITHFULNESS: original vs rebuilt  differing px = {{d}}  ({{d/tot*100:.4f}}% of canvas)")
for nm,(y0,y1) in (('p1',(6,555)),('p2',(564,1113)),('p3',(1123,1676))):
    s=(np.abs(a[y0:y1]-b[y0:y1]).sum(axis=2)>0).sum()
    print(f"    {{nm}}: {{s:>6}} px")
print("VERDICT:", "IDENTICAL" if d==0 else "DIFFERS")
"""], capture_output=True, text=True)
print(r.stdout or r.stderr)
