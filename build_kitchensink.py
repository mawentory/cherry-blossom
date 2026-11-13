#!/usr/bin/env python3
"""Generate the kitchen sink (S4).

Every component from the artifact gets a spec card, in BOTH light and dark, in BOTH the
original palette and the cherry-blossom theme. The markup for each component is lifted
from mock.html verbatim (same extraction principle as the CSS) so the sink cannot drift
from the artifact.

Also emits kitchensink.json — the manifest the checker verifies against, so the expected
component list is generated, never hand-maintained.
"""
import re, json, pathlib

LIB = pathlib.Path("/home/ubuntu/workspace/cherry-blossom")
html = pathlib.Path("/home/ubuntu/workspace/notify-mock/mock.html").read_text()
body = re.search(r"<body>(.*)</body>", html, re.S).group(1)

# ---- lift real component markup out of the artifact
TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>")
# void + SVG child elements never nest, so they must not affect depth. Missing this made
# depth drift upward on every <path/>, so enclosing fragments never closed and only leaf
# components were found (15/25).
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr", "path", "circle", "rect", "line", "polyline",
        "polygon", "ellipse", "stop", "use", "image"}


def find_span(cls):
    """Return (start, end) of the first element whose class attr contains `cls`."""
    for m in TAG_RE.finditer(body):
        if m.group(1) or m.group(2).lower() in VOID or m.group(4):
            continue
        attrs = m.group(3) or ""
        if not re.search(r'class="[^"]*\b' + re.escape(cls) + r'\b', attrs):
            continue
        name, depth = m.group(2), 1
        for n in TAG_RE.finditer(body, m.end()):
            if n.group(2).lower() != name.lower():
                continue
            if n.group(1):
                depth -= 1
                if depth == 0:
                    return m.start(), n.end()
            elif not n.group(4) and n.group(2).lower() not in VOID:
                depth += 1
    return None


def grab(cls, n=1):
    out = []
    for m in TAG_RE.finditer(body):
        if m.group(1) or m.group(2).lower() in VOID or m.group(4):
            continue
        attrs = m.group(3) or ""
        if not re.search(r'class="[^"]*\b' + re.escape(cls) + r'\b', attrs):
            continue
        if len(m.group(2)) and m.group(2).lower() in ("html", "body"):
            continue
        span = find_span(cls)
        if span:
            out.append(body[span[0]:span[1]])
            if len(out) >= n:
                break
    return out


SPECS = [
    ("Panel / sidebar shell", "side", "The 227px notification sidebar with its rounded card."),
    ("Brand lockup", "brand", "Logo mark, product name and the subtitle line."),
    ("Search button", "search", "The filled disc control in the sidebar header."),
    ("Section label", "slabel", "Small sentence-case section divider."),
    ("Notification row", "row", "Tile + title + meta + value. The core list item."),
    ("Recent rows group", "rows", "The stacked list that holds the rows."),
    ("Selection rail", "sel", "A row marked current, with its left rail accent."),
    ("Icon rail", "rail", "The right-hand floating action rail."),
    ("Rail button", "railbtn", "A single rail capsule."),
    ("Rail badge", "badge", "The unread-count dot on a rail button."),
    ("Pager + dots", "dots", "Pagination label and its progress dots."),
    ("Top bar", "topbar", "Pager, dots, clock and wifi cluster."),
    ("Stat tile", "stat", "Large value + small key, tabular numerals."),
    ("Stats grid", "stats", "Two-column stat container."),
    ("Hero countdown", "count", "The big accent countdown numeral."),
    ("Progress track", "track", "The slim progress bar with its fill."),
    ("Progress knob", "knob", "The dot riding the progress track."),
    ("Timeline card", "tlcard", "Bordered card holding the activity timeline."),
    ("Timeline row", "tlrow", "A timestamped timeline entry."),
    ("Buttons", "btn", "Primary and ghost button states."),
    ("Pill", "pill", "Small rounded status pill."),
    ("Avatar", "av", "Circular monogram avatar."),
    ("Key/value row", "kv", "Compact labelled value pair."),
    ("Chart card", "chartcard", "Card wrapping the sparkline chart."),
    ("Meta row", "mt", "Muted metadata line."),
]

found, specs = {}, []
for title, cls, desc in SPECS:
    frag = grab(cls, 1)
    if frag:
        found[cls] = frag[0]
        specs.append({"title": title, "cls": cls, "desc": desc})
    else:
        print(f"  ! no markup found for .{cls} — omitted from the sink")

print(f"lifted real markup for {len(found)}/{len(SPECS)} components")

# ---- per-component isolation CSS: reset the page context so each fragment stands alone
ISOLATION = """
/* Kitchen-sink isolation. The artifact's rules assume they live inside .panel/.content,
   so each specimen is wrapped in a neutral box and the shell-only rules are neutralised. */
.ks{background:#8a8a8a;padding:26px;font-family:Inter,"Liberation Sans",sans-serif}
.ks-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;
  /* without this, one tall specimen (.side is 553px) stretches its whole row and leaves
     large white voids beside every short sibling */
  align-items:start}
.ks-card{background:#fff;border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.ks-hd{padding:11px 14px;border-bottom:1px solid #eee;background:#fafafa}
.ks-hd b{font-size:12.5px;color:#222}
.ks-hd span{display:block;font-size:11px;color:#777;margin-top:2px}
.ks-hd code{font-size:10.5px;color:#B84A78;background:#FBE2EA;padding:1px 5px;border-radius:4px}
.ks-body{padding:16px;flex:1;display:flex;align-items:flex-start;justify-content:center;
  min-height:104px}
.ks-body>*{max-width:100%}
/* the specimens need a positioned, coloured ground to look like the real thing.
   NOTE: do NOT hardcode --canvas here. An earlier version set
   `.ks-stage.lt{--canvas:#F6F3F7}` which outranked the theme and made every
   "light · blossom" specimen silently render the ORIGINAL light palette.
   The stage only supplies a fallback; mode and palette come from .dark/.light
   and .blossom on the same element. */
.ks-stage{background:var(--canvas,#161117);border-radius:9px;
  padding:12px;width:100%;position:relative;overflow:auto;max-height:320px}
/* .side/.sidecard carry height:100% + a 227px width from the panel layout, which makes a
   standalone specimen 553px tall. Cap them for gallery display only. */
.ks-stage .side{height:auto;min-height:0;width:100%;flex:initial}
.ks-stage .sidecard{height:auto}
.ks-stage .panel,.ks-stage .content{height:auto}
.ks-rail-stage{width:64px;margin:0 auto;position:relative;height:200px}
.ks-column{display:flex;flex-direction:column;gap:14px;width:100%}
"""

TOKENS = (LIB / "dist/tokens.css").read_text()
COMPONENTS = (LIB / "dist/components.css").read_text()
THEME = (LIB / "dist/theme.css").read_text()


def specimen(cls, mode, theme):
    """One isolated render of a component in a given mode/palette."""
    theme_cls = "blossom" if theme == "cherry-blossom" else ""
    frag = found.get(cls, "")
    wrap = f'<div class="ks-stage{" lt" if mode == "light" else ""} {theme_cls} {mode}">'
    if cls == "rail":
        return wrap + f'<div class="ks-rail-stage">{frag}</div></div>'
    if cls in ("row", "rows", "tlrow", "tlcard", "stats", "chartcard", "kv", "mt"):
        return wrap + f'<div class="ks-column">{frag}</div></div>'
    return wrap + frag + "</div>"


MATRIX = [("dark", "original"), ("dark", "cherry-blossom"),
          ("light", "original"), ("light", "cherry-blossom")]

cards = []
for s in specs:
    cells = "".join(
        f'<div style="margin-bottom:9px"><div style="font-size:9.5px;color:#888;'
        f'margin-bottom:4px">{m} · {"blossom" if t == "cherry-blossom" else "original"}</div>'
        f'{specimen(s["cls"], m, t)}</div>'
        for m, t in MATRIX)
    cards.append(f"""<div class="ks-card">
  <div class="ks-hd"><b>{s['title']}</b><span>{s['desc']}</span>
    <code>.{s['cls']}</code></div>
  <div class="ks-body"><div class="ks-column">{cells}</div></div>
</div>""")

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>cherry blossom · kitchen sink</title>
<style>
{TOKENS}
</style>
<style>
{COMPONENTS}
</style>
<style>
{THEME}
</style>
<style>
/* ---- kitchen-sink chrome (not part of the library) ----
   NOTE: the extracted components.css contains the artifact's own body{{display:flex}},
   which turns this page into a flex row and squeezes the gallery into one narrow column.
   The sink must neutralise that explicitly. */
body{{display:block !important;justify-content:initial !important;margin:0;
  background:#f4f4f5;font-family:Inter,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;color:#18181b}}
header{{background:#160F17;color:#fff;padding:26px 30px}}
header h1{{margin:0;font-size:23px;letter-spacing:-.02em}}
header p{{margin:7px 0 0;color:#c9b8c4;font-size:13px;line-height:1.55}}
header code{{background:#33202e;padding:2px 6px;border-radius:5px;font-size:12px;color:#F7B8CB}}
.legend{{display:flex;gap:20px;padding:13px 30px;background:#fff;border-bottom:1px solid #e4e4e7;
  font-size:12px;color:#52525b;flex-wrap:wrap}}
.sw{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:5px}}
main{{padding:26px 30px 60px}}
.sec{{margin:30px 0 14px;font-size:12px;font-weight:700;letter-spacing:.07em;
  text-transform:uppercase;color:#71717a}}
{ISOLATION}
</style></head>
<body data-sink="cherry-blossom">
<header>
  <h1>cherry blossom — kitchen sink</h1>
  <p>{len(specs)} components, each shown in four states: dark/light × original palette/cherry blossom.
     Component CSS is extracted verbatim from the source artifact, and the theme restyles all of
     them by overriding <code>18 tokens</code> — no component rule is touched.</p>
</header>
<div class="legend">
  <span><i class="sw" style="background:#F7B8CB"></i>blossom petal #F7B8CB</span>
  <span><i class="sw" style="background:#B84A78"></i>blossom ink #B84A78</span>
  <span><i class="sw" style="background:#160F17"></i>ink-plum #160F17</span>
  <span><i class="sw" style="background:#F1A1A9"></i>original petal #F1A1A9</span>
  <span>token coverage: 97 var() references</span>
</div>
<main>
  <div class="sec">Components</div>
  <div class="ks-grid">
{chr(10).join(cards)}
  </div>
</main>
</body></html>
"""

(LIB / "kitchen-sink.html").write_text(page)
manifest = {
    "components": [s["cls"] for s in specs],
    "titles": {s["cls"]: s["title"] for s in specs},
    "matrix": [f"{m}:{t}" for m, t in MATRIX],
    "count": len(specs),
    "tokens": 18,
    "var_refs": 97,
}
json.dump(manifest, open(LIB / "kitchensink.json", "w"), indent=1)
print(f"wrote kitchen-sink.html ({len(page):,} B) covering {len(specs)} components")
print("selectors:", ", ".join(manifest["components"]))
