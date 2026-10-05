#!/usr/bin/env python3
"""
vidæo — agentic video engineering CLI.

The AEE cycle applied to video, made executable:
  SPEC → RTL → SIM → SYNTH → P&R → GDS → FAB → TEST

Every phase has a gate. A phase advances when its gate passes, never on a timer.
This orchestrates the proven pieces:
  render.mjs         (æRTXrender: CDP capture → NVENC)
  cudavideo_spec.py  (CuPy GPU particle render)
  video_supervision  (SupervisorVideo: PASS/FAIL + SHA-256 receipt)

Usage:
  vidæo status                          probe the toolchain
  vidæo verify <mp4>                    supervise one video
  vidæo render <url> <out.mp4>          render an HTML surface (CDP → NVENC)
  vidæo generate <spec.json> <out.mp4>  render a CuPy spec
  vidæo corpus [manifest.json]          regenerate the factory manifest
  vidæo cycle <spec.json> <out.mp4>     run the full AEE cycle with gates
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOME = Path(r"C:\æ")
THREEJS = HOME / "threejs-curriculo"
VISION = HOME / "vision-supervision"
FACTORY = HOME / "mp4-factory"
GPU_PY = r"C:\gpu\Scripts\python.exe"
FFPROBE = r"C:\Users\yaelm\AppData\Local\hermes\tools\ffmpeg-7.1-nvenc\bin\ffprobe.exe"

sys.path.insert(0, str(VISION))
sys.path.insert(0, str(THREEJS))

# ── AEE phases — the cycle the skill describes, now with gates ──
PHASES = ["SPEC", "RTL", "SIM", "SYNTH", "P&R", "GDS", "FAB", "TEST"]


def _ok(msg):   print(f"  \033[92m✓\033[0m {msg}")
def _fail(msg): print(f"  \033[91m✗\033[0m {msg}")
def _info(msg): print(f"    {msg}")
def _head(msg): print(f"\n\033[93m{msg}\033[0m")


# ══════════════════════════════════════════════════════════════
# GATES — each phase has a gate that must pass to advance
# ══════════════════════════════════════════════════════════════

def gate_spec(spec: dict) -> tuple[bool, str]:
    """SPEC gate: is the scene spec valid and bounded?"""
    required = {"particles", "palette", "motion", "duration"}
    missing = required - set(spec)
    if missing:
        return False, f"missing fields: {missing}"
    palettes = {"gold", "cyan", "neon", "amber", "mono"}
    if spec.get("palette") not in palettes:
        return False, f"palette '{spec.get('palette')}' not in {palettes}"
    if not (2000 <= spec.get("particles", 0) <= 20000):
        return False, f"particles {spec.get('particles')} outside 2000-20000"
    if not (0.01 <= spec.get("motion", 0) <= 0.08):
        return False, f"motion {spec.get('motion')} outside 0.01-0.08"
    if not (2 <= spec.get("duration", 0) <= 6):
        return False, f"duration {spec.get('duration')} outside 2-6"
    return True, "spec valid and bounded"


def gate_render(out: Path, min_frames: int = 1) -> tuple[bool, str]:
    """PRODUCTION gate: did the render produce real frames?"""
    frames_dir = Path(str(out).replace(".mp4", "-frames"))
    if not frames_dir.exists():
        return False, f"no frames dir at {frames_dir}"
    n = len(list(frames_dir.glob("frame_*.png")))
    if n < min_frames:
        return False, f"only {n} frames"
    return True, f"{n} frames written"


def gate_verify(out: Path) -> tuple[bool, str, dict]:
    """POST gate: does the supervisor pass the video?"""
    from vision_supervision import supervisar_video
    r = supervisar_video(str(out), muestrear=20)
    if r.get("calidad") == "PASS":
        return True, f"PASS (lum {r['luminancia_media']} con {r['contraste_medio']} mov {r['movimiento_medio']})", r
    return False, f"{r.get('calidad')}: {'; '.join(r.get('razones', []))}", r


# ══════════════════════════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════════════════════════

def cmd_status():
    _head("VIDÆO — toolchain")
    for tool, path in [("ffmpeg", "ffmpeg-7.1-nvenc/bin/ffmpeg.exe"),
                       ("ffprobe", "ffprobe.exe"), ("node", None)]:
        full = Path(r"C:\Users\yaelm\AppData\Local\hermes\tools") / path if path else None
        if full and full.exists():
            _ok(f"{tool:8} {full}")
        elif subprocess.run(["where", tool], capture_output=True).returncode == 0:
            _ok(f"{tool:8} on PATH")
        else:
            _fail(f"{tool:8} NOT FOUND")
    _ok(f"GPU py   {GPU_PY}")
    # GPU probe
    try:
        r = subprocess.run([GPU_PY, "-c",
            "import cupy as cp; p=cp.cuda.runtime.getDeviceProperties(0); "
            "print(p['name'].decode()+' | CC '+str(p['major'])+'.'+str(p['minor']))"],
            capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            _ok(f"CUDA     {r.stdout.strip()}")
        else:
            _fail(f"CUDA     {r.stderr.strip()[:80]}")
    except Exception as e:
        _fail(f"CUDA     {e}")
    _head("Render roots")
    for d in [THREEJS, FACTORY]:
        n = len(list(d.glob("*.mp4"))) if d.exists() else 0
        _info(f"{d}  ({n} mp4s)")


def cmd_verify(mp4: str):
    _head(f"VIDÆO — supervise {Path(mp4).name}")
    ok, msg, r = gate_verify(Path(mp4))
    (_ok if ok else _fail)(msg)
    print(json.dumps(r, indent=2))
    return 0 if ok else 1


def cmd_render(url: str, out: str, frames: int = 450):
    _head(f"VIDÆO — render {url}")
    t0 = time.time()
    r = subprocess.run(["node", "render.mjs", f"--url={url}", f"--out={out}",
                        f"--frames={frames}", "--fps=30", "--w=720", "--h=1280",
                        "--encoder=nvenc"],
                       cwd=str(THREEJS), capture_output=True, text=True, timeout=900)
    print(r.stdout[-600:] if r.stdout else r.stderr[-600:])
    if r.returncode != 0:
        _fail("render failed")
        return 1
    _ok(f"rendered in {time.time()-t0:.0f}s")
    ok, msg, _ = gate_verify(Path(out))
    (_ok if ok else _fail)(f"supervisor: {msg}")
    return 0 if ok else 1


def cmd_generate(spec_file: str, out: str):
    _head("VIDÆO — generate from spec")
    spec = json.load(open(spec_file, encoding="utf-8"))
    ok, msg = gate_spec(spec)
    (_ok if ok else _fail)(f"SPEC gate: {msg}")
    if not ok:
        return 1
    import cudavideo_spec
    gen = cudavideo_spec.generate(spec, out)
    _ok(f"rendered {gen['frames']} frames in {gen['capture_s']}s, encoded {gen['encode_s']}s")
    ok, msg, _ = gate_verify(Path(out))
    (_ok if ok else _fail)(f"supervisor: {msg}")
    return 0 if ok else 1


def cmd_corpus(manifest: str = None):
    _head("VIDÆO — regenerate corpus manifest")
    out = manifest or str(FACTORY / "manifest.json")
    r = subprocess.run([GPU_PY, str(FACTORY / "mp4_manifest.py"), out],
                       capture_output=True, text=True, timeout=900)
    print(r.stdout[-1200:])
    return r.returncode


def cmd_cycle(spec_file: str, out: str):
    """Run the full AEE cycle with gates. A phase advances only when its gate passes."""
    print("\033[93m╔══════════════════════════════════════════════╗")
    print("║  VIDÆO — AEE CYCLE                           ║")
    print("╚══════════════════════════════════════════════╝\033[0m")
    trace = {"out": out, "phases": [], "started": time.time()}

    # SPEC
    _head("[1/8] SPEC — validate the scene spec")
    spec = json.load(open(spec_file, encoding="utf-8"))
    ok, msg = gate_spec(spec)
    trace["phases"].append({"phase": "SPEC", "gate": msg, "pass": ok})
    (_ok if ok else _fail)(msg)
    if not ok:
        trace["verdict"] = "BLOCKED at SPEC"
        return 1, trace

    # RTL — resolve the generation parameters
    _head("[2/8] RTL — resolve generation parameters")
    params = {"particles": spec["particles"], "palette": spec["palette"],
              "motion": spec["motion"], "duration": spec["duration"],
              "frames": int(30 * spec["duration"])}
    ok = params["frames"] > 0
    trace["phases"].append({"phase": "RTL", "gate": f"{params['frames']} frames planned", "pass": ok})
    (_ok if ok else _fail)(f"{params['frames']} frames planned")
    if not ok:
        trace["verdict"] = "BLOCKED at RTL"
        return 1, trace

    # SIM/SYNTH — the render itself (CuPy computes the scene graph directly)
    _head("[3-5/8] SIM · SYNTH · P&R — render, compose, post")
    import cudavideo_spec
    t0 = time.time()
    gen = cudavideo_spec.generate(spec, out)
    trace["phases"].append({"phase": "SIM/SYNTH/P&R",
                            "gate": f"{gen['frames']} frames in {gen['capture_s']}s", "pass": True})
    _ok(f"{gen['frames']} frames rendered in {gen['capture_s']}s")

    # GDS — the frame sequence exists
    _head("[6/8] GDS — verify the frame sequence")
    ok, msg = gate_render(Path(out))
    trace["phases"].append({"phase": "GDS", "gate": msg, "pass": ok})
    (_ok if ok else _fail)(msg)
    if not ok:
        trace["verdict"] = "BLOCKED at GDS"
        return 1, trace

    # FAB — the encode produced a file
    _head("[7/8] FAB — verify the encode")
    size_mb = os.path.getsize(out) / 1048576 if os.path.exists(out) else 0
    ok = size_mb > 0.1
    trace["phases"].append({"phase": "FAB", "gate": f"{size_mb:.1f} MB", "pass": ok})
    (_ok if ok else _fail)(f"{size_mb:.1f} MB")

    # TEST — the supervisor
    _head("[8/8] TEST — supervisor gate")
    ok, msg, r = gate_verify(Path(out))
    trace["phases"].append({"phase": "TEST", "gate": msg, "pass": ok,
                            "receipt": r.get("receipt")})
    (_ok if ok else _fail)(msg)
    if ok:
        _info(f"receipt {r['receipt']}")

    trace["verdict"] = "PASS" if ok else "FAIL"
    trace["elapsed_s"] = round(time.time() - trace["started"], 1)
    trace["receipt"] = r.get("receipt")
    return (0 if ok else 1), trace


# ══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "status":
        cmd_status(); return 0
    if cmd == "verify" and args:
        return cmd_verify(args[0])
    if cmd == "render" and len(args) >= 2:
        return cmd_render(args[0], args[1], int(args[2]) if len(args) > 2 else 450)
    if cmd == "generate" and len(args) >= 2:
        return cmd_generate(args[0], args[1])
    if cmd == "corpus":
        return cmd_corpus(args[0] if args else None)
    if cmd == "cycle" and len(args) >= 2:
        code, trace = cmd_cycle(args[0], args[1])
        print(json.dumps(trace, indent=2))
        return code
    print(f"unknown command: {cmd}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
