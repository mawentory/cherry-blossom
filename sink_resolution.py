#!/usr/bin/env python3
"""Per-specimen THEME RESOLUTION check (JS payload for the browser harness).

Presence is not enough: a component can be present, correctly sized, and still show the
wrong palette because a `.dark` class outranked a `.light` one. That exact bug shipped once
in this repo. This asserts, for EVERY specimen in the sink, that the computed token values
resolve to the palette its caption claims.

Emits JSON: {ok, checked, bad:[{card, state, token, got, want}]}
"""
import json

MAN = json.load(open("/home/ubuntu/workspace/cherry-blossom/kitchensink.json"))

JS = """
(() => {
  // expected palettes, read from the stylesheets themselves so this cannot drift
  const cs = getComputedStyle(document.documentElement);
  const probeDark = (() => {
    const d = document.createElement('div');
    d.className = 'blossom dark'; d.style.position='absolute'; d.style.opacity='0';
    document.body.appendChild(d);
    const g = getComputedStyle(d);
    const v = {canvas:g.getPropertyValue('--canvas').trim(),
               accent:g.getPropertyValue('--accent').trim()};
    d.remove(); return v;
  })();
  const probeLight = (() => {
    const d = document.createElement('div');
    d.className = 'blossom light'; d.style.position='absolute'; d.style.opacity='0';
    document.body.appendChild(d);
    const g = getComputedStyle(d);
    const v = {canvas:g.getPropertyValue('--canvas').trim(),
               accent:g.getPropertyValue('--accent').trim()};
    d.remove(); return v;
  })();
  const origDark = (() => {
    const d = document.createElement('div');
    d.className = 'dark'; d.style.position='absolute'; d.style.opacity='0';
    document.body.appendChild(d);
    const g = getComputedStyle(d);
    const v = {canvas:g.getPropertyValue('--canvas').trim(),
               accent:g.getPropertyValue('--accent').trim()};
    d.remove(); return v;
  })();
  const origLight = (() => {
    const d = document.createElement('div');
    d.className = 'light'; d.style.position='absolute'; d.style.opacity='0';
    document.body.appendChild(d);
    const g = getComputedStyle(d);
    const v = {canvas:g.getPropertyValue('--canvas').trim(),
               accent:g.getPropertyValue('--accent').trim()};
    d.remove(); return v;
  })();

  const EXPECT = {
    'dark:original':        origDark,
    'dark:cherry-blossom':  probeDark,
    'light:original':       origLight,
    'light:cherry-blossom': probeLight,
  };

  const bad = [];
  let checked = 0;
  document.querySelectorAll('.ks-card').forEach(card => {
    const title = card.querySelector('b') ? card.querySelector('b').textContent : '?';
    card.querySelectorAll('.ks-stage').forEach(stage => {
      // the caption is the stage's PREVIOUS SIBLING inside the same wrapper div.
      // (Reading the parent's previousElementSibling instead paired every specimen with
      //  its neighbour's caption, which produced 18 bogus failures.)
      const cap = stage.previousElementSibling;
      const label = cap ? cap.textContent.trim() : '';
      const m = label.match(/^(dark|light)\s*·\s*(original|blossom|cherry-blossom)$/);
      if (!m) return;
      // captions abbreviate "cherry-blossom" to "blossom"
      const key = m[1] + ':' + (m[2] === 'original' ? 'original' : 'cherry-blossom');
      const want = EXPECT[key];
      if (!want) return;
      const g = getComputedStyle(stage);
      const got = {canvas: g.getPropertyValue('--canvas').trim(),
                   accent:  g.getPropertyValue('--accent').trim()};
      checked += 1;
      for (const t of ['canvas', 'accent']) {
        if (got[t].toUpperCase() !== want[t].toUpperCase()) {
          bad.push({card: title, state: key, token: t, got: got[t], want: want[t]});
        }
      }
    });
  });

  return JSON.stringify({
    ok: bad.length === 0,
    checked,
    distinct: {
      'dark:original': EXPECT['dark:original'],
      'dark:cherry-blossom': EXPECT['dark:cherry-blossom'],
      'light:original': EXPECT['light:original'],
      'light:cherry-blossom': EXPECT['light:cherry-blossom'],
    },
    bad: bad.slice(0, 12),
    badCount: bad.length,
  });
})()
"""

if __name__ == "__main__":
    print(JS)
