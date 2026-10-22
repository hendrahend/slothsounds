# Sloth Sounds: I Was Too Lazy to Pick a Playlist, So I Taught My Laptop to Make the Music 🦥

*This is my submission for the Hacktoberfest Open-Source AI Challenge, Week 3: Slow and Steady.*

International Sloth Day was October 20, and sloths have the right idea. They move at their own
pace, conserve their energy, and let the world come to them. So for this week's challenge I
built the most sloth-shaped thing I could think of: a tool for people who want music to wind
down to but cannot be bothered to browse, curate, or pay for another subscription.

You type a lazy vibe — "rainy sunday piano", "slow ambient for sleep", "fireplace while it
snows" — and Sloth Sounds writes the music. One command gets you a seamless loop. One command
before bed gets you a whole multi-minute wind-down set by morning.

Everything runs on my laptop. Open-weight models only. Nothing leaves the machine.

## What I built

Sloth Sounds is a local-first ambient music generator:

```
"rainy sunday piano" ──► vibe expander ──► MusicGen (open weights) ──► seamless loop
  your lazy words        Gemma 3 / Ollama    facebook/musicgen-small    WAV + MP3
                         or keyword map      (swappable)                out/
```

- **`slothsounds gen "rainy sunday piano"`** — generates one click-free loop in about half
  a minute on my GPU (a 4 GB RTX 2050; it also runs on CPU, just slower)
- **`slothsounds night 10 "slow ambient for sleep"`** — composes a 10-segment set, each
  segment a variation on the vibe so the piece evolves instead of repeating, crossfaded
  into one continuous file with a run sheet of timecodes and seeds
- **`slothsounds doctor`** — tells you exactly what your machine has and what it's missing

The stack is entirely open:

| Piece | Role | Why open |
| --- | --- | --- |
| **MusicGen** (`facebook/musicgen-small`) | generates the audio | open weights, runs offline, swappable, fine-tunable, free forever |
| **Gemma 3 via Ollama** | expands lazy vibes into music prompts | runs on a laptop, no API key, no usage meter |
| **numpy + stdlib `wave`** | loops, crossfades, WAV I/O | boring, reliable |
| **ffmpeg** (optional) | MP3 export | already on your machine |

## The Gemma layer: from lazy words to music prompts

MusicGen prompts want concrete audio descriptors. Humans type feelings. Gemma 3 (4B, Q4,
via Ollama) sits in the middle and translates. Real outputs from tonight's run:

| You type | Gemma writes |
| --- | --- |
| `rainy sunday piano` | Ambient piano, melancholic, sustained chords, subtle rain ambience, gentle arpeggios, 60 bpm, seamless loop, no vocals |
| `fireplace while it snows` | Warm synth pads, gentle piano, distant sleigh bells, crackling log, soft strings, 60 bpm, seamless loop, no vocals |
| `midnight train through the countryside` | Synth pads, distant steel drums, mournful cello, driving arpeggio, shimmering reverb, slow tempo, expansive atmosphere, seamless loop, no vocals |

If Ollama isn't running, a keyword-based expander takes over so the tool still works fully
offline. `slothsounds doctor` reports which path is live.

## Hear the Gemma layer work

Same vibe, same seed (777), same model, same GPU. The only variable is who writes the prompt:

| Expander | What MusicGen received | Listen |
| --- | --- | --- |
| Keyword heuristic | rainy sunday piano, gentle rainfall, distant rolling thunder, soft felt-piano melody, intimate close-miked piano, ambient instrumental, seamless loop, high quality recording, no vocals | [heuristic](https://github.com/hendrahend/slothsounds/blob/main/site/audio/rainy-sunday-piano-777-heuristic.wav) |
| Gemma 3 | Ambient piano, melancholic, subtle strings, gentle rain ambience, slow tempo, shimmering textures, seamless loop, no vocals | [gemma](https://github.com/hendrahend/slothsounds/blob/main/site/audio/rainy-sunday-piano-777-gemma.wav) |

The heuristic path staples stock descriptors onto your words. Gemma makes decisions — it
picks the instrumentation, sets a tempo, shapes an arc. Same seed means any difference you
hear comes from the prompt alone.

## Demo

Three loops and one night set, all generated on my RTX 2050 tonight, committed as WAVs in
the repo so you can listen without running anything:

- [`rainy-sunday-piano-42.wav`](https://github.com/hendrahend/slothsounds/blob/main/site/audio/rainy-sunday-piano-42.wav) — 30s loop
- [`fireplace-while-it-snows-101.wav`](https://github.com/hendrahend/slothsounds/blob/main/site/audio/fireplace-while-it-snows-101.wav) — 30s loop
- [`midnight-train-through-the-countryside-202.wav`](https://github.com/hendrahend/slothsounds/blob/main/site/audio/midnight-train-through-the-countryside-202.wav) — 30s loop
- [`full-set.wav`](https://github.com/hendrahend/slothsounds/blob/main/site/audio/full-set.wav) — 4.7-minute night set (10 segments, crossfaded)

**Live demo: [slothsounds-site.onrender.com](https://slothsounds-site.onrender.com/)** — a
player page with all four tracks, deployed on Render from the `render.yaml` blueprint in
the repo. Generation stays local; the site is just the shop window.

`slothsounds doctor` on my machine, verbatim:

```
[OK  ] Python >= 3.10  3.12.10
[OK  ] numpy           2.5.4
[OK  ] torch           2.5.1+cu121 (NVIDIA GeForce RTX 2050)
[OK  ] audiocraft      1.3.0
[--  ] ffmpeg          not found (optional, MP3 export only)
[OK  ] ollama          reachable, models: gemma3:4b
[--  ] backboard       SLOTHSOUNDS_BACKBOARD_KEY not set (optional, taste memory)
```

## Why open innovation matters for what I built

The closed-API version of this project would be a wrapper: send your vibe to someone else's
GPU, pay per generation, hope the service still exists next year, and hand a company a log of
everything you listen to at 2 AM. That's not a tool, that's a subscription with extra steps.

Running open-weight models locally means:

- **It works offline.** Plane, cabin, cabin-in-the-woods. The music is generated where you are.
- **It costs nothing to run.** The thousandth loop costs exactly as much as the first: zero.
- **The model is swappable.** `musicgen-small` on a 4 GB laptop GPU today, `musicgen-medium`
  on a desktop tomorrow, a fine-tuned specialist the day after — the pipeline doesn't change.
- **Nothing is logged.** Your 2 AM listening habits stay between you and your laptop.

The open pieces aren't decoration here — they're the whole product. Strip them out and there
is no project left.

## The lazy payoff

The challenge asked how much time or effort the project actually saves. Here's the honest
math from my own evenings, measured on the runs above:

- **The old ritual:** open the streaming app, scroll, skip, second-guess, land on something
  you've already played. Five to ten minutes of decisions, every evening, forever.
- **The new ritual:** one command, about ten seconds of typing. The music exists half a
  minute later.
- **Night mode:** the decision happens before you're even tired. Ten segments — 4.7 minutes
  of evolving music — composed in about five and a half minutes of wall time. You kick it
  off, and the set is just there.

Measured on the RTX 2050: each 30-second segment takes roughly 32 seconds to generate, and
the full 10-segment set (282 seconds of audio after crossfades) finished in about five and a
half minutes. Gemma's vibe expansion adds a few seconds when the model is warm.

I won't pretend this saves anyone hours. What it actually removes is the deciding — the
scrolling, the skipping, the standing in the kitchen at 11 PM arguing with yourself about
what to play. The sloth doesn't optimize the walk. The sloth skips it.

## Prize categories

Entering two categories, where the integration is strongest:

- **Best Use of Gemma** — Gemma 3 (via Ollama) expands lazy vibes into MusicGen-optimized
  prompts, with an offline keyword fallback; it also teachers the fine-tuning dataset in
  the repo
- **Best Use of Render** — the public demo site at
  [slothsounds-site.onrender.com](https://slothsounds-site.onrender.com/), deployed from
  the `render.yaml` blueprint in the repo, serving the actual generated audio

Tinker and Backboard integrations are wired in the repo (a Gemma-distilled training
dataset plus LoRA SFT script; taste memory with a local fallback), but they are not the
headline entries for this challenge.

## Show your work

Repo: **github.com/hendrahend/slothsounds** (MIT). 21 tests, `slothsounds doctor` for
setup checks, and a Windows shim script because audiocraft's xformers wheels don't exist
for Windows — the kind of detail you only find by actually running the thing.

---

*Built during the Week 3 window (Oct 19–25). Repo: github.com/hendrahend/slothsounds*
