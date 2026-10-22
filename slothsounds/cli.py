"""Sloth Sounds command line.

  slothsounds gen "rainy sunday piano"      generate one seamless loop
  slothsounds night 30 "slow ambient sleep" generate a 30-minute wind-down set
  slothsounds vibe "rainy sunday piano"     show the expanded prompt only
  slothsounds library                       list what you have generated
  slothsounds doctor                        check the environment
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
from pathlib import Path

from . import __version__
from .audio import duration_seconds, normalize, write_wav
from .config import Settings
from .doctor import print_report, run_checks
from .library import TrackLibrary
from .loops import make_loop
from .musicgen import MusicGenEngine, MusicGenUnavailable
from .night import build_night_set
from .vibe import expand_vibe


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--model", default=None, help="MusicGen model (default: facebook/musicgen-small)")
    p.add_argument("--seed", type=int, default=None, help="seed for reproducible output")
    p.add_argument("--no-llm", action="store_true",
                   help="skip the local LLM and use keyword vibe expansion")
    p.add_argument("--ollama-model", default=None, help="Ollama model for vibe expansion")
    p.add_argument("--out", default=None, help="output directory (default: out/)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slothsounds",
        description="Local-first ambient music generator. Type a lazy vibe, get a seamless loop.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("gen", help="generate one seamless loop")
    gen.add_argument("vibe", help="the lazy vibe, e.g. 'rainy sunday piano'")
    gen.add_argument("--duration", type=int, default=30, help="seconds (max 30 per clip)")
    gen.add_argument("--name", default=None, help="output file name (without extension)")
    gen.add_argument("--mp3", action="store_true", help="also export MP3 (needs ffmpeg)")
    _add_common(gen)

    night = sub.add_parser("night", help="generate a multi-minute wind-down set")
    night.add_argument("minutes", type=int, help="total length in minutes")
    night.add_argument("vibe", help="the lazy vibe for the whole set")
    night.add_argument("--segment", type=int, default=None,
                       help="seconds per generated segment (default 30)")
    _add_common(night)

    vibe = sub.add_parser("vibe", help="show the expanded music prompt")
    vibe.add_argument("vibe", help="the lazy vibe")
    _add_common(vibe)

    lib = sub.add_parser("library", help="list generated tracks")
    lib.add_argument("--dir", default=None, help="library directory (default: out/)")
    lib.add_argument("--all", action="store_true", help="show every entry, not just the latest")

    sub.add_parser("doctor", help="check the environment")
    return parser


def _settings(args) -> Settings:
    settings = Settings()
    if getattr(args, "model", None):
        settings.model = args.model
    if getattr(args, "ollama_model", None):
        settings.ollama_model = args.ollama_model
    if getattr(args, "out", None):
        settings.output_dir = Path(args.out)
    if getattr(args, "segment", None):
        settings.segment_seconds = args.segment
    return settings


def _export_mp3(wav_path: Path) -> Path | None:
    mp3_path = wav_path.with_suffix(".mp3")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-codec:a", "libmp3lame",
             "-qscale:a", "4", str(mp3_path)],
            check=True,
        )
        return mp3_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("mp3 export failed (is ffmpeg on PATH?)", file=sys.stderr)
        return None


def cmd_gen(args) -> int:
    settings = _settings(args)
    vibe_prompt, source = expand_vibe(
        args.vibe,
        use_llm=not args.no_llm,
        ollama_model=settings.ollama_model,
        ollama_url=settings.ollama_url,
    )
    print(f"vibe   : {args.vibe}")
    print(f"prompt : {vibe_prompt}  [{source}]")

    engine = MusicGenEngine(model_name=settings.model)
    try:
        seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)
        print(f"model  : {settings.model}  seed: {seed}")
        print("generating... (this takes a minute on CPU, seconds on GPU)")
        audio = engine.generate(
            vibe_prompt,
            duration=args.duration,
            seed=seed,
            temperature=settings.temperature,
            top_k=settings.top_k,
            cfg_coef=settings.cfg_coef,
        )
    finally:
        engine.unload()

    loop = normalize(make_loop(audio, settings.sample_rate,
                               fade_seconds=settings.crossfade_seconds))
    out_dir = settings.ensure_output_dir()
    name = args.name or f"{args.vibe.strip().lower().replace(' ', '-')[:40]}-{seed}"
    wav_path = write_wav(out_dir / f"{name}.wav", loop, settings.sample_rate)

    library = TrackLibrary(out_dir)
    library.add(kind="loop", vibe=args.vibe, prompt=vibe_prompt, source=source,
                model=settings.model, seed=seed,
                duration=duration_seconds(loop, settings.sample_rate), path=wav_path)

    print(f"saved  : {wav_path} ({duration_seconds(loop, settings.sample_rate):.1f}s, seamless loop)")
    if args.mp3:
        mp3 = _export_mp3(wav_path)
        if mp3:
            print(f"mp3    : {mp3}")
    return 0


def cmd_night(args) -> int:
    settings = _settings(args)
    engine = MusicGenEngine(model_name=settings.model)
    try:
        library = TrackLibrary(settings.output_dir)
        build_night_set(
            engine,
            vibe=args.vibe,
            minutes=args.minutes,
            settings=settings,
            library=library,
            use_llm=not args.no_llm,
            seed=args.seed,
        )
    finally:
        engine.unload()
    return 0


def cmd_vibe(args) -> int:
    settings = _settings(args)
    prompt, source = expand_vibe(
        args.vibe,
        use_llm=not args.no_llm,
        ollama_model=settings.ollama_model,
        ollama_url=settings.ollama_url,
    )
    print(f"vibe   : {args.vibe}")
    print(f"source : {source}")
    print(f"prompt : {prompt}")
    return 0


def cmd_library(args) -> int:
    directory = args.dir or "out"
    library = TrackLibrary(directory)
    entries = library.all() if args.all else library.latest(10)
    if not entries:
        print(f"nothing in {library.path} yet — generate something first")
        return 0
    print(f"{'id':<10}{'kind':<9}{'dur':>7}  vibe")
    for e in entries:
        print(f"{e['id']:<10}{e['kind']:<9}{e['duration']:>6.1f}s  {e['vibe']}")
    return 0


def cmd_doctor(args) -> int:
    return 0 if print_report(run_checks(_settings(args))) else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "gen": cmd_gen,
        "night": cmd_night,
        "vibe": cmd_vibe,
        "library": cmd_library,
        "doctor": cmd_doctor,
    }
    try:
        return handlers[args.command](args)
    except MusicGenUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrupted — the sloth understands", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
