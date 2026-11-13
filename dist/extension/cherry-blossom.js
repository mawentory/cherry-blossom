/* cherry blossom — hermes-webui extension skin

   Registers through window.registerHermesSkin(), which accepts only an allowlisted
   token vocabulary and colour values (hex / rgb / rgba / hsl / keyword). No
   --font-* tokens and no arbitrary selectors, by design.

   IMPORTANT — why this file registers only a FEW tokens:
   registerHermesSkin emits exactly ONE selector, `:root[data-skin="key"]{...}`
   (static/boot.js:3789), with no per-mode variant. Anything registered here
   therefore applies in BOTH light and dark. Registering the dark palette here
   would override the light palette in extension.css (later-injected stylesheet,
   same specificity, but the JS block is re-inserted on every skin apply).

   So: this file registers the identity only (name, picker swatches, scheme).
   The full two-mode palette lives in extension.css, which can express
   `:root[data-skin=]` (light) and `:root.dark[data-skin=]` (dark) separately.
   That is the same architecture the built-in full-palette skins use (cf. sienna
   in static/style.css).
*/

(function () {
  "use strict";
  if (typeof window.registerHermesSkin !== "function") return;

  window.registerHermesSkin({
    name: "Cherry Blossom",
    value: "cherry-blossom",
    /* picker swatches: light ground, dark ground, accent */
    colors: ["#FBEFF4", "#1A0C16", "#B0366A"],
    /* declare the default scheme so boot resolves the right base class */
    scheme: "dark",
    /* Identity-level tokens only; the two-mode palette is in extension.css. */
    tokens: {
      "--accent": "#B0366A",
      "--accent-hover": "#C2537F",
      "--accent-rgb": "176, 54, 106"
    }
  });
})();
