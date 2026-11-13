# cherry blossom for hermes-webui

A self-registering skin. No fork, no PR, no changes to hermes-webui.

**Verified end-to-end** against a live hermes-webui instance (`exp-v0.52.627`), not merely by
reading source: the skin registers, appears in the Settings picker as "Cherry Blossom", and
resolves a correct palette in **both** light and dark.

| State | `--bg` | `--accent` |
|---|---|---|
| default | `#FEFCF7` | `#B8860B` |
| cherry blossom, light | `#FBEFF4` | `#B0366A` |
| cherry blossom, dark | `#1A0C16` | `#F5AEC6` |

## Install

```bash
git clone https://github.com/mawentory/cherry-blossom.git

export HERMES_WEBUI_EXTENSION_DIR=/path/to/cherry-blossom/dist/extension
export HERMES_WEBUI_EXTENSION_STYLESHEET_URLS=/extensions/cherry-blossom/extension.css
export HERMES_WEBUI_EXTENSION_SCRIPT_URLS=/extensions/cherry-blossom/cherry-blossom.js
```

Restart hermes-webui, open Settings, and pick **Cherry Blossom**.

## How it registers, and why there are two files

`cherry-blossom.js` calls `window.registerHermesSkin()` with the skin's identity: name,
picker swatches, `scheme`, and three accent tokens. `extension.css` carries the full
two-mode palette.

That split is not stylistic — it is forced by the API. `registerHermesSkin` emits exactly
**one** selector:

```js
:root[data-skin="cherry-blossom"]{ /* whatever you registered */ }
```

There is no per-mode variant, so anything registered applies to light *and* dark. A
two-mode skin therefore cannot express its palette through the JS API alone; the
light/dark split has to live in CSS, using the same architecture as the built-in
full-palette skins (cf. `sienna` in `static/style.css`):

```css
:root[data-skin="cherry-blossom"]      { /* light */ }
:root.dark[data-skin="cherry-blossom"] { /* dark  */ }
```

Note the app has **no `.light` class** — light is the absence of `.dark`
(`boot.js:3586` toggles only `dark`). A `:root.light[...]` selector never matches. That was
a real bug in the first version of this file, and it is why the light palette is written on
the bare `:root[data-skin]` selector.

The registration API itself is real and hardened — it sanitises every value, rejects
anything that is not a colour, guards reserved core skins, and survives boot
(`tests/test_extension_theme_registration.py`, 41 assertions).

## Limits, stated honestly

- **No fonts.** `_SAFE_SKIN_VALUE_RE` accepts only colour values, so `--font-*` cannot be
  set through the skin API. (Fonts *are* possible via a plain extension stylesheet — a
  different mechanism — but not through skin registration.)
- **No arbitrary selectors** in registration; the key is slug-filtered and the emitted
  selector form is fixed. Arbitrary CSS is only possible via the extension stylesheet.
- **Server-side persistence does not work for extension skins.** `api/config.py` validates
  `skin` against a closed 16-value set and silently rewrites anything unknown to `default`
  on `POST /api/settings`. An extension skin therefore persists in browser `localStorage`
  only. This contradicts `THEMES.md`, which claims no server changes are needed; the code
  wins.

## Palette

| Token | Dark | Light |
|---|---|---|
| `--bg` | `#1A0C16` | `#FBEFF4` |
| `--surface` | `#2A1220` | `#FFF9FB` |
| `--text` | `#FBEBF3` | `#2E0F1F` |
| `--accent` | `#F5AEC6` | `#B0366A` |
| `--border` | `#47203A` | `#EAC5D6` |

Every token used here is inside the extension allowlist (`boot.js:3745`). In the standalone
library, all 18 tokens clear CIELAB dE 2.3 against the default palette in both modes, and
text/accent clear WCAG AA contrast (verified by `verify_palette.py`).

Distinct from the existing `hepburn` skin (warm rose red `#d44a7a`): dE2000 13.6 on the
light accent, and the identity lives in the full palette rather than the accent alone.
Brand pink vs the danger red `#E5484D` is separated by dE 36.9-63.2, so the accent never
reads as an error.

MIT.
