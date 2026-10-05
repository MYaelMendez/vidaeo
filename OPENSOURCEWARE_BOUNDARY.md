# OpenSourceWare Boundary — vidæo

This file marks the **#opensourceware** release boundary for `vidæo/`.

> *We embody #opensourceware and equip new business owners with care.*
> Open Source Ware (evolution of OCW) — democratizes **agency**, not just knowledge.

## What vidæo is

Agentic video engineering. The AEE cycle (SPEC → RTL → SIM → SYNTH → P&R → GDS →
FAB → TEST) applied to video, with **gates**: a phase advances when its gate
passes, never on a timer. It orchestrates the render toolchain and refuses to
declare success it has not measured.

`vidæo.py` is stdlib-only Python 3.10+ — it orchestrates external tools
(ffmpeg, node, a GPU python) by subprocess; it never imports a network library.

## Included (shipped)

- `vidæo.py` — the AEE cycle CLI: `status | cycle | verify | render | generate | corpus`
- `README.md` — the cycle, the gates, and how to run it
- `LICENSE` — MIT
- `release-manifest.json` — artifact hashes for this release

## Excluded (never shipped)

- **Rendered output** (`*.mp4`, `*-frames/`) — a render is a product, not source
- **Operator-specific absolute paths** as *hard requirements* — the CLI resolves
  its toolchain from `C:\æ\...` conventions today, but every path is a module
  constant, overridable without touching the cycle logic
- **Any secret, token, or credential** — vidæo touches no secret and no network
- Private Hermes runtime assumptions — the cycle runs standalone wherever
  ffmpeg + node + a python exist

## Generalization rules (what makes it OSW, not a personal script)

1. **No network.** vidæo never makes a request. It cannot exfiltrate by design.
2. **Gates, not timers.** A stage advances on a measured condition; elapsed time
   never marks a stage complete.
3. **Refuse over pretend.** A gate that fails blocks the cycle and reports why —
   it does not emit a plausible-looking result.
4. **Degrade gracefully.** A missing tool is reported by `vidæo status`; the
   cycle fails at the phase whose tool is absent, naming it.

## The gate contract (the load-bearing rule)

```
SPEC   → valid + bounded (palette, particles, motion, duration)
RTL    → frames planned > 0
GDS    → frame files exist
FAB    → encoded file > 0.1 MB
TEST   → SupervisorVideo PASS + SHA-256 receipt
```

If TEST fails, the cycle returns a non-zero verdict and the trace of which gate
blocked. There is no path where a failed render is reported as success.

## Boundary in one line

**The cycle is open. The claim it makes is proven.**

---

*vidæo pairs with [supervisionvidæo](https://github.com/MYaelMendez/supervisionvidaeo):
the produce-and-verify contract that refuses to emit a render it has not measured.*
