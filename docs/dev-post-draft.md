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
 your lazy words         Gemma 3 / Ollama     facebook/musicgen-small    WAV + MP3
                         or keyword map       (swappable)                out/
```

- **`slothsounds gen "rainy sunday piano"`** — generates one click-free loop in about a minute
  on my GPU (a 4 GB RTX 2050; it also runs on CPU, just slower)
- **`slothsounds night 30 "slow ambient for sleep"`** — composes a 30-minute set overnight,
  each segment a variation on the vibe so the piece evolves instead of repeating, crossfaded
  into one continuous file with a run sheet of timecodes and seeds
- **`slothsounds doctor`** — tells you exactly what your machine has and what it's missing

The stack is entirely open:

| Piece | Role | Why open |
| --- | --- | --- |
| **MusicGen** (`facebook/musicgen-small`) | generates the audio | open weights, runs offline, swappable, fine-tunable, free forever |
| **Gemma 3 via Ollama** | expands lazy vibes into music prompts | runs on a laptop, no API key, no usage meter |
| **numpy + stdlib `wave`** | loops, crossfades, WAV I/O | boring, reliable |
| **ffmpeg** (optional) | MP3 export | already on your machine |

## Demo

TODO: terminal recording + audio samples + demo site link

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

The challenge asked how much time or effort the project actually saves. Here's the honest math
for my own evenings:

TODO: real numbers — messages/minutes of playlist browsing replaced, generation time, etc.

One command replaces the whole ritual: no app to open, no albums to scroll past, no "what
should I put on". And with night mode, the decision happens before you're even tired — you
kick it off, sleep, and the music is just there.

## Prize categories

- **Overall prize**
- **Best Use of Gemma** — Gemma 3 (via Ollama) expands lazy vibes into MusicGen-optimized prompts
- **Best Use of Tinker** — TODO if the fine-tuned vibe translator lands in time
- **Best Use of Render** — the public demo site
- **Best Use of Backboard** — taste memory that shapes future night sets
- **Best Use of a .tech Domain** — the demo domain

## Show your work

TODO: DevRelay session embed + repo link

---

*Built during the Week 3 window (Oct 19–25). Repo: github.com/hendrahend/slothsounds*
