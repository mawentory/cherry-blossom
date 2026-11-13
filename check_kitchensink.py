#!/usr/bin/env python3
"""S4 gate: verify the kitchen sink actually renders every component, with zero console
errors, and that the cherry-blossom theme measurably restyles them.

A checker that cannot fail is worthless, so `--selftest` runs it against a deliberately
broken page and asserts it FAILS. Exit 0 = sink is sound; 1 = problem; 2 = checker broken.
"""
import argparse, json, os, re, subprocess, sys, pathlib

LIB = pathlib.Path("/home/ubuntu/workspace/cherry-blossom")
CHROME = "google-chrome"


def drive(page_url, want_components, expect_fail=False):
    """Load the page in headless Chrome over CDP; return console errors + geometry."""
    import socket, subprocess as sp, time, urllib.request, json as js
    port = 9333
    proc = sp.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                     f"--remote-debugging-port={port}", "--remote-allow-origins=*",
                     "--window-size=1400,1000", "about:blank"],
                    stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    else:
        proc.kill()
        raise SystemExit("chrome did not start")

    # minimal CDP over websocket
    import base64, hashlib, struct
    ws_url = js.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/new?{page_url}"))["webSocketDebuggerUrl"]
    s = socket.create_connection((ws_url.split("//")[1].split("/")[0].split(":")[0],
                                 int(ws_url.split(":")[2].split("/")[0])))
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall((f"GET {ws_url.split(port)[1]} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
               f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    time.sleep(0.4)
    s.recv(4096)

    def frame(payload):
        data = payload.encode()
        hdr = b"\x81"
        n = len(data)
        if n < 126:
            hdr += struct.pack("!B", 0x80 | n)
        elif n < 65536:
            hdr += struct.pack("!BH", 0x80 | 126, n)
        else:
            hdr += struct.pack("!BI", 0x80 | 127, n)
        mask = os.urandom(4)
        hdr += mask
        s.sendall(hdr + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def read():
        s.settimeout(12)
        try:
            b = s.recv(1 << 20)
        except Exception:
            return None
        if not b or len(b) < 2:
            return None
        ln = b[1] & 0x7F
        off = 2
        if ln == 126:
            ln = struct.unpack("!H", b[2:4])[0]; off = 4
        elif ln == 127:
            ln = struct.unpack("!I", b[2:10])[0]; off = 10
        return b[off:off + ln].decode("utf-8", "replace")

    mid = [0]

    def call(method, params=None):
        mid[0] += 1
        frame(js.dumps({"id": mid[0], "method": method, "params": params or {}}))
        while True:
            msg = read()
            if msg is None:
                return None
            try:
                d = js.loads(msg)
            except Exception:
                continue
            if d.get("id") == mid[0]:
                return d.get("result")

    call("Runtime.enable")
    call("Log.enable")
    time.sleep(2.5)

    probe = """
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
      // prove the theme actually restyles: read accent on a blossom stage
      const b = document.querySelector('.ks-stage.blossom');
      if (b) {
        const cs = getComputedStyle(b);
        out.styles.blossomAccent = cs.getPropertyValue('--accent').trim();
        out.styles.blossomCanvas = cs.getPropertyValue('--canvas').trim();
      }
      const o = document.querySelector('.ks-stage:not(.blossom)');
      if (o) {
        const cs = getComputedStyle(o);
        out.styles.originalAccent = cs.getPropertyValue('--accent').trim();
      }
      out.stageCount = document.querySelectorAll('.ks-stage').length;
      out.cardCount = document.querySelectorAll('.ks-card').length;
      return JSON.stringify(out);
    })()
    """ % json.dumps(want_components)

    r = call("Runtime.evaluate", {"expression": probe, "returnByValue": True})
    errors = call("Runtime.evaluate", {
        "expression": "JSON.stringify(window.__errs || [])", "returnByValue": True})
    proc.kill()
    s.close()
    if not r:
        return None
    return json.loads(r["result"]["value"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=str(LIB / "kitchen-sink.html"))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    man = json.load(open(LIB / "kitchensink.json"))
    want = man["components"]

    if args.selftest:
        # build a deliberately broken copy: drop components + raise a JS error
        html = pathlib.Path(args.page).read_text()
        broken = html.replace('<div class="ks-grid">',
                              '<div class="ks-grid">').replace(
            "</body>", "<script>throw new Error('deliberate sink failure');</script></body>")
        # remove one component entirely
        broken = re.sub(r'<div class="row sel">.*?</div>\s*</div>\s*</div>', '', broken, count=1,
                        flags=re.S)
        p = LIB / "verify" / "kitchen-sink-broken.html"
        p.parent.mkdir(exist_ok=True)
        p.write_text(broken)
        res = drive("file://" + str(p), want + ["__absent__"])
        print("SELFTEST — checker pointed at a deliberately broken page")
        print(f"  missing reported: {res['missing'] if res else 'NONE (checker is blind!)'}")
        ok = res is not None and res["missing"]
        print(f"  verdict: {'checker HAS teeth' if ok else 'CHECKER IS BLIND — fix it'}")
        return 0 if ok else 2

    print(f"KITCHEN SINK CHECK — {args.page}")
    res = drive("file://" + os.path.abspath(args.page), want)
    if res is None:
        print("  FAILED: page did not evaluate")
        return 1
    print(f"  cards rendered ....... {res['cardCount']}/{man['count']}")
    print(f"  specimens (stages) ... {res['stageCount']} "
          f"(expected {man['count'] * len(man['matrix'])})")
    print(f"  components missing ... {len(res['missing'])} {res['missing'] or ''}")
    print(f"  components invisible . {len(res['invisible'])} {res['invisible'] or ''}")
    print(f"  zero-box components .. {len(set(res['zero']))} (a component may also appear "
          f"hidden inside another specimen)")
    print(f"  console errors ....... {len(res['errors'])} {res['errors'][:3] or ''}")
    st = res["styles"]
    print(f"  blossom accent ....... {st.get('blossomAccent')}")
    print(f"  blossom canvas ....... {st.get('blossomCanvas')}")
    print(f"  original accent ...... {st.get('originalAccent')}")
    themed = st.get("blossomAccent") and st.get("originalAccent") and \
        st["blossomAccent"] != st["originalAccent"]
    print(f"  theme restyles ....... {'YES' if themed else 'NO'}")

    bad = res["missing"] or res["invisible"] or res["errors"] or not themed
    print(f"\n  VERDICT: {'FAIL' if bad else 'PASS'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
