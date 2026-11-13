/* cherry blossom — hermes-webui extension skin

   Registers through window.registerHermesSkin(), which accepts only an allowlisted token
   vocabulary and colour values (hex / rgb / hsl / keyword). No --font-* tokens and no
   arbitrary selectors, so typography is intentionally not part of this skin.

   The allowlist in static/boot.js:3745 does include --bg, --surface, --text and --border,
   which is what lets a FULL palette ship this way instead of an accent-only skin.
*/

(function () {
  "use strict";
  if (typeof window.registerHermesSkin !== "function") return;

  window.registerHermesSkin({
    name: "Cherry Blossom",
    value: "cherry-blossom",
    colors: ["#FBEFF4", "#1A0C16", "#B0366A"],
    scheme: "dark",
    tokens: {
      /* dark: deep plum ground, petal light */
      "--bg": "#1A0C16",
      "--surface": "#2A1220",
      "--surface2": "#341628",
      "--text": "#FBEBF3",
      "--text2": "#FBEBF3",
      "--muted": "#B396A6",
      "--accent": "#F5AEC6",
      "--accent-hover": "#FBC9DC",
      "--accent-contrast": "#2A0A18",
      "--accent-text": "#2A0A18",
      "--accent-bg": "#5E1F3E",
      "--accent-bg-strong": "#47203A",
      "--accent-rgb": "245, 174, 198",
      "--border": "#47203A",
      "--border2": "#3D1B31",
      "--hover-bg": "#5E1F3E",
      "--code-bg": "#2A1220",
      "--code-text": "#FBEBF3",
      "--sidebar": "#2A1220",
      "--sidebar-text": "#FBEBF3",
      "--link": "#F5AEC6",
      "--info": "#F5AEC6",
      "--success": "#7FC29B",
      "--warning": "#F0C98E",
      "--danger": "#E5484D"
    }
  });
})();
