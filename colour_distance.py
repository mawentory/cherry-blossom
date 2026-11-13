#!/usr/bin/env python3
"""Quantify Cherry Blossom's distinctness from upstream's pink `hepburn` skin.

A new pink appearance risks being rejected as a duplicate, so this computes real
CIELAB dE (76 and 2000) and WCAG contrast, rather than asserting 'it looks different'.
"""
import json, math

def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb2lab(rgb):
    r, g, b = (srgb2lin(c) for c in rgb)
    # sRGB -> XYZ (D65)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    xn, yn, zn = 0.95047, 1.0, 1.08883
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)
    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def de76(a, b):
    return math.dist(rgb2lab(hex2rgb(a)), rgb2lab(hex2rgb(b)))


def de2000(c1, c2):
    L1, a1, b1 = rgb2lab(hex2rgb(c1))
    L2, a2, b2 = rgb2lab(hex2rgb(c2))
    kL = kC = kH = 1.0
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb > 0 else 0
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0
    else:
        dh = h2p - h1p
        dhp = dh - 360 if dh > 180 else (dh + 360 if dh < -180 else dh)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    hbp = h1p + h2p
    if C1p * C2p != 0:
        if abs(h1p - h2p) > 180:
            hbp = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
        else:
            hbp /= 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dth = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp > 0 else 0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / (kL * Sl)) ** 2 + (dCp / (kC * Sc)) ** 2
                     + (dHp / (kH * Sh)) ** 2 + Rt * (dCp / (kC * Sc)) * (dHp / (kH * Sh)))


def lum(h):
    r, g, b = (srgb2lin(c) for c in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


HEPBURN = {"accent": "#c6246a", "hover": "#ec5597", "soft": "#f2abca"}
CB = {"dark_accent": "#F7B8CB", "light_accent": "#D96A93"}

print("=" * 78)
print("CHERRY BLOSSOM vs upstream HEPBURN (the existing pink skin)")
print("=" * 78)
JND = 2.3
print(f"\n{'pair':<44}{'dE76':>8}{'dE2000':>9}{'verdict':>12}")
print("-" * 78)
rows = []
for cbname, cbhex in CB.items():
    for hbname, hbhex in HEPBURN.items():
        d76, d2k = de76(cbhex, hbhex), de2000(cbhex, hbhex)
        v = "DISTINCT" if d2k > JND else "near-dup"
        rows.append((f"cb {cbname} {cbhex} vs {hbname} {hbhex}", d76, d2k, v))
        print(f"{rows[-1][0]:<44}{d76:>8.1f}{d2k:>9.1f}{v:>12}")

# how crowded is the pink region already?
SKINS = json.load(open("/home/ubuntu/workspace/cherry-blossom-probe/skins.json")) \
    if __import__("os").path.exists("/home/ubuntu/workspace/cherry-blossom-probe/skins.json") else {}
if SKINS:
    print("\n" + "=" * 78)
    print("CLOSEST EXISTING SKIN TO THE CHERRY-BLOSSOM ACCENT")
    print("=" * 78)
    for cbname, cbhex in CB.items():
        ranked = sorted(((de2000(cbhex, v), k, v) for k, v in SKINS.items()
                         if isinstance(v, str) and v.startswith("#")))
        if ranked:
            print(f"  {cbname} {cbhex}: nearest built-in = {ranked[0][1]} {ranked[0][2]} "
                  f"(dE2000 {ranked[0][0]:.1f}); next = {ranked[1][1]} {ranked[1][2]} "
                  f"(dE2000 {ranked[1][0]:.1f})" if len(ranked) > 1 else "")

print("\n" + "=" * 78)
print("WCAG CONTRAST (accent ink on accent, and text on ground)")
print("=" * 78)
for label, fg, bg in [
    ("cb dark   text on canvas", "#F6ECF2", "#160F17"),
    ("cb dark   accent-ink on accent", "#2A1020", "#F7B8CB"),
    ("cb light  text on canvas", "#2A1020", "#FDF6F8"),
    ("cb light  accent-ink on accent", "#FFFFFF", "#D96A93"),
    ("hepburn   accent on white", "#c6246a", "#FFFFFF"),
    ("cb light  accent on white", "#D96A93", "#FFFFFF"),
    ("cb dark   accent on canvas", "#F7B8CB", "#160F17"),
]:
    c = contrast(fg, bg)
    tag = "AAA" if c >= 7 else ("AA" if c >= 4.5 else ("AA-large" if c >= 3 else "FAIL"))
    print(f"  {label:<34}{c:>6.2f}:1   {tag}")
