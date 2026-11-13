#!/usr/bin/env python3
"""S4 gate — JS half. Prints a JSON result; driven by check_kitchensink.py via the
browser harness (CDP), which avoids hand-rolling a websocket client.
"""
import json, sys, pathlib

WANT = json.load(open("/home/ubuntu/workspace/cherry-blossom/kitchensink.json"))["components"]

CHECK_JS = """
(() => {
  const out = {errors: [], missing: [], invisible: [], zero: [], styles: {}};
  const want = %s;
  for (const cls of want) {
    const els = document.querySelectorAll('.' + CSS.escape(cls));
    if (!els.length) { out.missing.push(cls); continue; }
    let anyVisible = false;
    for (const el of els) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 || r.height > 0) anyVisible = true;
      if (r.width === 0 && r.height === 0) out.zero.push(cls);
    }
    if (!anyVisible) out.invisible.push(cls);
  }
  const b = document.querySelector('.ks-stage.blossom');
  if (b) {
    const cs = getComputedStyle(b);
    out.styles.blossomAccent = cs.getPropertyValue('--accent').trim();
    out.styles.blossomCanvas = cs.getPropertyValue('--canvas').trim();
  }
  const o = document.querySelector('.ks-stage:not(.blossom)');
  if (o) out.styles.originalAccent = getComputedStyle(o).getPropertyValue('--accent').trim();
  out.stageCount = document.querySelectorAll('.ks-stage').length;
  out.cardCount = document.querySelectorAll('.ks-card').length;
  out.title = document.title;
  return JSON.stringify(out);
})()
""" % json.dumps(WANT)

if __name__ == "__main__":
    print(CHECK_JS)
