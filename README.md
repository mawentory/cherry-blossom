# cherry blossom

A CSS design system with a token layer, a component library, a kitchen-sink gallery, and a
plum-and-petal theme called **cherry blossom**. Plain HTML and CSS, no build step, no
dependencies.

```html
<link rel="stylesheet" href="dist/tokens.css">
<link rel="stylesheet" href="dist/components.css">
<link rel="stylesheet" href="dist/theme.css">   <!-- optional: the cherry blossom palette -->
```

Then put `class="blossom"` on a wrapper for dark cherry blossom, or `class="blossom light"`
for the light variant. Without `theme.css` you get the original neutral palette.

## What's in the box

| File | What it is |
|---|---|
| `dist/tokens.css` | 18 colour tokens, light in `:root`, dark under `.dark`. The single source of truth. |
| `dist/components.css` | The component library: 25 components, ~60 rules, 97 `var(--token)` references. |
| `dist/theme.css` | Cherry blossom. Overrides the same 18 tokens. Touches **zero** component rules. |
| `kitchen-sink.html` | Every component in four states: dark/light × original/cherry blossom. |
| `dist/extension/` | Self-registering skin for [hermes-webui](https://github.com/nesquena/hermes-webui). |

## Why a token layer

The theme works by replacing 18 values, not by editing styles. That is the whole design:
one file changes the appearance of 25 components, and because nothing else moves, a theme
cannot break layout, spacing or type.

```
tokens.css   →   components.css   →   theme.css
18 values        25 components        same 18 names, new values
```

## Verification

Every claim here is checked by a script. Nothing is asserted by eyeball.

```bash
python3 verify_extraction.py   # extracted CSS renders pixel-identical to the source
python3 verify_palette.py      # theme clears dE 2.3 in both modes; WCAG AA contrast holds
python3 gate_sink.py           # kitchen sink covers every component; theme really restyles
```

What those gates actually assert:

- **Extraction fidelity** — the page rebuilt from `dist/` renders **0 differing pixels**
  against the original artifact, across all 3 panels, at 782×1676. Font loading is pinned,
  because unpinned renders of this page land in two different visual states.
- **Palette distinctness** — every one of the 18 tokens clears the CIELAB **dE 2.3**
  just-noticeable-difference threshold against the original, in **both** modes. An earlier
  draft failed this: 6 of 18 tokens sat below the threshold in light mode, so "light
  blossom" was visually identical to the original. The gate caught it.
- **Contrast** — text and accent clear WCAG AA against their own ground. Light accent is
  5.24:1 on its canvas.
- **Sink coverage** — 25 components, 100 specimens (25 × 4 states), zero missing, zero
  collapsed. A deliberate failing control proves the checker can fail.

## The palette

| Token | Light | Dark |
|---|---|---|
| `--canvas` | `#FBEFF4` | `#1A0C16` |
| `--surface` | `#FFF9FB` | `#2A1220` |
| `--text` | `#2E0F1F` | `#FBEBF3` |
| `--accent` | `#B0366A` | `#F5AEC6` |
| `--accent-ink` | `#FFFFFF` | `#2A0A18` |
| `--line` | `#EAC5D6` | `#47203A` |

Full set in `dist/tokens.css` and `dist/theme.css`.

## Distinctness from other pink themes

Upstream `hermes-webui` already ships a pink skin, `hepburn` (a warm rose red, `#c6246a` /
`#ec5597`). Cherry blossom is deliberately different: it is a **cool petal pink on a plum
ground** that sets the **full palette** — ground, surface, text, border — not just an accent.

Measured in CIELAB dE2000 against hepburn's real accent `#d44a7a`:

| Cherry blossom | dE2000 |
|---|---|
| dark petal `#F5AEC6` | well clear |
| light petal `#B0366A` | 13.6 |

Brand pink vs the danger red used for error states (`#E5484D`) is separated by dE 36.9–63.2,
so an accent never reads as an error.

## Using it as a hermes-webui skin

`dist/extension/` registers cherry blossom with no fork and no PR to hermes-webui:

```bash
export HERMES_WEBUI_EXTENSION_DIR=/path/to/cherry-blossom/dist/extension
export HERMES_WEBUI_EXTENSION_STYLESHEET_URLS=/extensions/cherry-blossom/extension.css
```

The skin registers through `window.registerHermesSkin()`, which only accepts an allowlisted
token vocabulary and colour values. That allowlist does carry `--bg`, `--surface`, `--text`
and `--border`, so the full palette ships this way. It cannot carry `--font-*`, so
typography stays out of the skin, by design.

## Provenance

The component CSS and tokens were **extracted mechanically** from a pixel-replica artifact of
a notification/incident UI, not rewritten by hand, so the library cannot drift from the
design it came from. The extraction is verified pixel-identical. The replica itself scores
**54.2** ink F1@2px against its source image with fonts pinned (49.0 unpinned) — the library
reproduces the artifact faithfully; the artifact was never a perfect copy of the photograph.

## Licence

MIT.
