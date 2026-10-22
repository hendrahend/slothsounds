# Sloth Sounds 🦥

**Type a lazy vibe, get a seamless wind-down loop — on your own laptop, with no cloud in the loop.**

Sloth Sounds is a local-first ambient music generator for people who want music to
relax to but cannot be bothered to browse, curate, or pay for another subscription.
Point it at a vibe ("rainy sunday piano", "slow ambient for sleep", "fireplace while
it snows"); it writes the prompt for you, generates a click-free loop with an
open-weight music model, and — if you ask nicely — composes a whole multi-minute
wind-down set overnight while you sleep.

Nothing leaves your machine. No upload, no account, no per-minute bill, no one
profiling what you listen to at 2 AM.

```
  "rainy sunday piano" ──► vibe expander ──► MusicGen (open weights) ──► seamless loop
   your lazy words         Gemma 3 / Ollama     facebook/musicgen-small    WAV + MP3
                           or keyword map       (swappable)                out/
```

## Why local, and why open

Streaming wind-down music means scrolling past albums you do not want, on a
subscription, over a connection, while a company logs your midnight habits.
Sloth Sounds runs everything on open pieces:

| Piece | Role | Why open |
| --- | --- | --- |
| **MusicGen** (`facebook/musicgen-small`) | generates the audio | open weights, runs offline, swappable, fine-tunable, free forever |
| **Gemma 3 via Ollama** | expands lazy vibes into music prompts | runs on a laptop, no API key, no usage meter |
| **numpy + stdlib `wave`** | loops, crossfades, WAV I/O | boring, reliable, already installed |
| **ffmpeg** (optional) | MP3 export | already on your machine |

The marginal cost of the thousandth loop is zero, which is the whole point.
And because the music model is swappable, you can trade quality for speed
(`musicgen-small` on a 4 GB laptop GPU, `musicgen-medium` on a desktop)
without touching the rest of the pipeline.

## Install

```bash
git clone https://github.com/hendrahend/slothsounds.git
cd slothsounds
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[music]"
```

`pip install -e ".[music]"` pulls torch + audiocraft (~2.5 GB). On Windows:

```powershell
# CUDA torch for NVIDIA GPUs (the default pip torch is CPU-only on Windows)
pip install torch --index-url https://download.pytorch.org/whl/cu121
# audiocraft needs --no-deps on Windows (xformers has no Windows wheels)
pip install audiocraft --no-deps
pip install einops protobuf sentencepiece scipy timm transformers av
```

Optional upgrades:

```bash
ollama pull gemma3:4b    # LLM vibe expansion (keyword fallback works without it)
# ffmpeg on PATH          # MP3 export
```

Or run the bootstrap script: `bash scripts/bootstrap_models.sh`

First run downloads the MusicGen weights (~1.5 GB for `small`).

## Use

```bash
# check what your machine has
slothsounds doctor

# see how a vibe gets expanded (no generation, instant)
slothsounds vibe "rainy sunday piano"

# generate one seamless loop
slothsounds gen "rainy sunday piano" --duration 30

# generate a 30-minute wind-down set overnight
slothsounds night 30 "slow ambient for sleep"

# reproducible output + MP3 export
slothsounds gen "fireplace while it snows" --seed 1234 --mp3

# what have you made?
slothsounds library
```

Output:

```
out/
  rainy-sunday-piano-1234.wav   the loop (click-free, ready to repeat)
  library.json                  metadata: vibe, prompt, model, seed
  night-slow-ambient-for-sleep-20261022-234500/
    segment-01.wav ...          individual 30s loops
    full-set.wav                the whole set, crossfaded
    RUN-SHEET.md                timecodes, seeds, variations
```

## The lazy payoff

- **One command** replaces browsing: no app, no scroll, no "what should I put on".
- **Night mode**: `slothsounds night 30` before bed → a fresh 30-minute set by morning.
- **Works offline**: plane, cabin, cabin-in-the-woods. Zero data, zero subscription.
- **Your listening stays yours**: nothing is uploaded, nothing is logged.

## Roadmap

- [x] MusicGen pipeline, seamless loops, night mode, local library
- [ ] Fine-tuned vibe translator (Tinker) — a specialist model that turns lazy
      human vibes into MusicGen-optimized prompts
- [ ] Hosted demo + nightly radio (Render)
- [ ] Taste memory: remember which vibes you keep coming back to (Backboard)
- [ ] `slothsounds.tech` demo domain

## Development

```bash
pip install -e ".[dev]"
pytest                # runs without torch installed
```

## License

MIT — see [LICENSE](LICENSE).
