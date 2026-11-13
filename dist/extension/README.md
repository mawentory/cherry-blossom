# cherry blossom for hermes-webui

A self-registering skin. No fork, no PR, no changes to hermes-webui.

## Install

```bash
git clone https://github.com/mawentory/cherry-blossom.git
export HERMES_WEBUI_EXTENSION_DIR=/path/to/cherry-blossom/dist/extension
export HERMES_WEBUI_EXTENSION_STYLESHEET_URLS=/extensions/cherry-blossom/extension.css
```

Restart hermes-webui, open Settings, and pick **Cherry Blossom** from the skin list.

## How it registers

`cherry-blossom.js` calls `window.registerHermesSkin()` with an allowlisted token
vocabulary. That API is real and hardened — it sanitises every value, rejects anything that
is not a colour, guards reserved core skins, and survives boot (see
`tests/test_extension_theme_registration.py` in hermes-webui, 41 assertions).

The allowlist (`static/boot.js:3745`) carries a **full palette**, not just accents:
`--bg`, `--surface`, `--text`, `--text2`, `--muted`, `--border`, `--code-bg`, `--sidebar`,
bubbles and semantic colours. That is why this ships as a complete identity rather than a
recolour of the accent.

## Limits, stated honestly

- **No fonts.** `_SAFE_SKIN_VALUE_RE` only accepts colour values, so `--font-*` cannot be set
  through this API. Typography is out of scope for the skin.
- **No arbitrary CSS.** Selectors cannot be injected; only allowlisted tokens are applied.
  `extension.css` carries static CSS for the light-mode palette and `color-scheme`.
- **Dark by default.** The `scheme` field declares `dark`; the light palette lives in
  `extension.css` under `.light`.

## Palette

| Token | Dark | Light |
|---|---|---|
| `--bg` | `#1A0C16` | `#FBEFF4` |
| `--surface` | `#2A1220` | `#FFF9FB` |
| `--text` | `#FBEBF3` | `#2E0F1F` |
| `--accent` | `#F5AEC6` | `#B0366A` |
| `--border` | `#47203A` | `#EAC5D6` |

All 18 tokens clear CIELAB dE 2.3 against the default palette in both modes, and text/accent
clear WCAG AA contrast. Verified by `verify_palette.py` in the repo root.

Distinct from the existing `hepburn` skin (warm rose red `#d44a7a`): dE2000 13.6 on the
light accent, and the identity lives in the full palette rather than the accent alone.

MIT.
