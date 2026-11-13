#!/usr/bin/env python3
"""Build the cherry-blossom library by EXTRACTING the real artifact, not rewriting it.

Rationale: mock.html already carries a genuine token layer (.dark/.light, 21 tokens) and
~60 component rules that all reference var(--token). Re-typing those by hand would
introduce drift, so we split the real CSS mechanically:
  - token declarations  -> dist/tokens.css
  - everything else     -> dist/components.css
Then the cherry-blossom theme overrides the SAME token names, which is why the theme can
restyle every component without touching one component rule.
"""
import re, os, json, pathlib

SRC = "/home/ubuntu/workspace/notify-mock/mock.html"
OUT = pathlib.Path("/home/ubuntu/workspace/cherry-blossom")
DIST = OUT / "dist"
DIST.mkdir(parents=True, exist_ok=True)

html = pathlib.Path(SRC).read_text()
css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
body = re.search(r"<body>(.*)</body>", html, re.S).group(1)


def block(name):
    """Pull a flat CSS block's declarations as an ordered dict."""
    m = re.search(r"\." + name + r"\{(.*?)\n\}", css, re.S)
    if not m:
        raise SystemExit(f"token block .{name} not found")
    decls = {}
    for part in m.group(1).split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            decls[k.strip()] = v.strip()
    return decls


dark = block("dark")
light = block("light")
print(f"extracted token blocks: light={len(light)} dark={len(dark)}")
missing = set(light) ^ set(dark)
assert not missing, f"token sets differ: {missing}"
TOKENS = list(light)

# ---- components.css : real CSS minus ONLY the token blocks.
# Everything else is preserved verbatim — including html/body/.canvas and the body
# font-family stack. Stripping those and re-adding them by hand silently dropped the
# font, which changed every glyph (measured: 11.5% of canvas differed).
comp = css
comp = re.sub(r"/\* -+ theme tokens -+ \*/\n\.dark\{.*?\n\}\n\.light\{.*?\n\}\n", "", comp, flags=re.S)
assert ".dark{" not in comp and ".light{" not in comp, "token block leaked into components"
varCount = len(re.findall(r"var\(--", comp))
assert varCount > 0, "no var() references found in extracted components"
assert "font-family:Inter" in comp, "body font stack was lost — extraction would change every glyph"

# ---- tokens.css : the design system, emitted from the real values
def emit_tokens(decls, indent="  "):
    return "\n".join(f"{indent}{k}:{v};" for k, v in decls.items())

tokens_css = f"""/* cherry-blossom · tokens.css
   GENERATED from notify-mock/mock.html — do not hand-edit.
   {len(TOKENS)} tokens, extracted mechanically so the system cannot drift from the source.
   Default = light. Add class .dark (or data-mode="dark") to switch.
*/
:root{{
{emit_tokens(light)}
}}
.dark, :root[data-mode="dark"]{{
{emit_tokens(dark)}
}}
"""
(DIST / "tokens.css").write_text(tokens_css)
(DIST / "components.css").write_text(
    "/* cherry-blossom · components.css\n"
    "   GENERATED from notify-mock/mock.html — the real component rules, unmodified.\n"
    f"   {varCount} var(--token) references; every colour comes from tokens.css.\n"
    "   Load tokens.css first.\n*/\n"
    "*{box-sizing:border-box;margin:0;padding:0}\n"
    + comp.strip() + "\n")

json.dump({"tokens": TOKENS, "light": light, "dark": dark,
           "components_bytes": len(comp), "var_refs": varCount},
          open(OUT / "extracted.json", "w"), indent=1)

print(f"wrote dist/tokens.css ({len(tokens_css)} B) and dist/components.css ({len(comp)} B)")
print(f"var(--token) references in components: {varCount}")
print("tokens:", ", ".join(TOKENS))
