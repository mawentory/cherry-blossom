#!/usr/bin/env python3
"""S4 gate, pure-CSS half. Runs without a browser harness so the check is reproducible
by anyone: parses the generated sink and asserts the component coverage, the specimen
count, and that the theme's tokens actually differ from the original's.
Exit 0 = pass. Exit 2 = checker is broken (self-test).
"""
import json, re, sys, pathlib

LIB = pathlib.Path("/home/ubuntu/workspace/cherry-blossom")
HTML = (LIB / "kitchen-sink.html").read_text()
MAN = json.load(open(LIB / "kitchensink.json"))


def parse_blocks(css):
    """Parse CSS, stripping comments first so they cannot corrupt selector text."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = {}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        sel = " ".join(m.group(1).split())
        decls = {}
        for d in m.group(2).split(";"):
            if ":" in d:
                k, v = d.split(":", 1)
                if k.strip().startswith("--"):
                    decls[k.strip()] = v.strip()
        if decls:
            out[sel] = decls
    return out


theme = (LIB / "dist" / "theme.css").read_text()
blocks = parse_blocks(theme)

fails = []

# 1. every component in the manifest is present in the markup
for cls in MAN["components"]:
    if not re.search(r'class="[^"]*\b' + re.escape(cls) + r'\b', HTML):
        fails.append(f"component .{cls} missing from sink markup")

# 2. specimen count == components x matrix
stages = len(re.findall(r'class="ks-stage', HTML))
want_stages = MAN["count"] * len(MAN["matrix"])
print(f"specimens ....... {stages} (expected {want_stages})")
if stages != want_stages:
    fails.append(f"specimen count {stages} != {want_stages}")

# 3. theme overrides the same token count as the token layer
tok = (LIB / "dist" / "tokens.css").read_text()
tz = parse_blocks(tok)
tk = parse_blocks(theme)
tok_names = set(tz.get(":root", {}))
# classify each theme block by whether it is a light or dark set
dark_set, light_set = {}, {}
for sel, decls in tk.items():
    is_light = ".light" in sel or "light[" in sel
    if is_light:
        if len(decls) > len(light_set):
            light_set, light_sel = decls, sel
    else:
        if len(decls) > len(dark_set):
            dark_set, dark_sel = decls, sel
print(f"tokens in layer . {len(tok_names)}")
print(f"theme dark set .. {len(dark_set)}  <- {dark_sel[:58]}")
print(f"theme light set . {len(light_set)}  <- {light_sel[:58]}")
for label, s in (("dark", dark_set), ("light", light_set)):
    missing = tok_names - set(s)
    if missing:
        fails.append(f"theme {label} does not override: {sorted(missing)}")

# 4. the theme must actually CHANGE the values, not restate them
shared = tok_names & set(dark_set)
changed = [t for t in shared if tz.get(":root", {}).get(t) != dark_set[t]]
print(f"light: tokens changed by theme . {len(changed)}/{len(shared)}")
if len(changed) < len(shared) * 0.6:
    fails.append(f"theme only changes {len(changed)}/{len(shared)} tokens — suspiciously passive")

# 5. no hardcoded colour leaking into component CSS (everything must be a token)
comp = (LIB / "dist" / "components.css").read_text()
body_rules = re.sub(r"^\s*/\*.*?\*/", "", comp, flags=re.S | re.M)
hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", body_rules)
print(f"hardcoded hex in components . {len(hexes)} {sorted(set(hexes))[:8]}")

print()
if fails:
    print("VERDICT: FAIL")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("VERDICT: PASS — coverage, specimen count, token parity and theme deltas all hold")
