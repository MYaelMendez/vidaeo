# vidæo

**Agentic video engineering.** The AEE cycle applied to video — with gates.

```bash
python vidæo.py status                 # probe the toolchain
python vidæo.py cycle spec.json out.mp4   # run the full cycle, gated
python vidæo.py verify out.mp4         # supervise any video
python vidæo.py render <url> out.mp4   # render an HTML surface
python vidæo.py generate spec.json out.mp4  # render a CuPy scene
python vidæo.py corpus                 # regenerate the factory manifest
```

`vidæo.py` is stdlib-only Python 3.10+. It orchestrates external tools
(ffmpeg, node, a GPU python) by subprocess; it never imports a network library.

---

## The cycle

```
SPEC → RTL → SIM → SYNTH → P&R → GDS → FAB → TEST
```

**A phase advances when its gate passes — never on a timer.**

| Phase | Gate |
|---|---|
| SPEC | fields present, palette valid, particles 2000–20000, motion 0.01–0.08, duration 2–6 |
| RTL | frames planned > 0 |
| SIM/SYNTH/P&R | frames rendered |
| GDS | frame files exist |
| FAB | encoded file > 0.1 MB |
| TEST | SupervisorVideo PASS + SHA-256 receipt |

A bad spec **blocks at SPEC** — zero frames render. The cycle returns a JSON
trace naming the gate that blocked.

```bash
$ python vidæo.py cycle bad-spec.json out.mp4
[1/8] SPEC — validate the scene spec
  ✗ palette 'chartreuse' not in {mono, gold, amber, neon, cyan}
{"verdict": "BLOCKED at SPEC", ...}
```

---

## Why gates, not timers

A timer says *"eight seconds passed, so this must be done."* A gate says
*"measure it, and if it fails, refuse."*

Timers desync at scene transitions and produce black frames that look like a
finished render. Gates catch that at the frame where it happens. The TEST phase
runs a deterministic computer-vision supervisor: black (luminance < 12), blown
out (> 235), flat (contrast < 8), static (motion < 0.5). A failing render is
never reported as success.

---

## The render toolchain

vidæo orchestrates, it does not render. The default producers:

- **CuPy particle render** — `cudavideo_spec.py` computes frames on the GPU
- **HTML surface render** — `render.mjs` drives `__renderFrame(i)` per frame
  through Chrome CDP, then encodes with NVENC

Both are module constants in `vidæo.py` — swap them without touching the cycle.

---

## Pairs with supervisionvidæo

[`supervisionvidæo`](https://github.com/MYaelMendez/supervisionvidaeo) is the
produce-and-verify contract built on the same idea: `produce()` returns a receipt
or raises `SupervisionRefused`. vidæo is the cycle that calls it; supervisionvidæo
is the contract that refuses.

---

## License

MIT. See `OPENSOURCEWARE_BOUNDARY.md` for what ships and what never does.

**The cycle is open. The claim it makes is proven.**
