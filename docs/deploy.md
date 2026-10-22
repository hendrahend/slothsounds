# Deploy runbook — Sloth Sounds demo

## 1. Render (Best Use of Render)

The repo includes a `render.yaml` blueprint: a static site serving the demo
player from `site/`.

1. Go to https://dashboard.render.com → **New +** → **Blueprint**
2. Connect the `hendrahend/slothsounds` repo — Render reads `render.yaml`
3. The static site `slothsounds-site` deploys on every push to `main`
4. After generating new loops locally:
   ```bash
   slothsounds site        # rebuilds site/ from out/library.json
   git add site && git commit -m "site: new loops" && git push
   ```
   Render auto-deploys the commit.

The HF26 Render credit (from hacktoberfest.com/my/promos) covers any instance
costs; the static site itself is free.

## 2. .tech domain (Best Use of a .tech Domain)

1. Claim the free domain at hacktoberfest.com/my/promos (follow the .tech link)
2. In the .tech dashboard, set a CNAME for your chosen name
   (e.g. `slothsounds.tech`) → `<your-site>.onrender.com`
3. In Render: **slothsounds-site** → **Settings** → **Custom Domains** →
   add the domain, wait for TLS

## 3. Backboard taste memory (Best Use of Backboard)

1. Get an API key at https://app.backboard.io → Settings → API Keys
2. `setx SLOTHSOUNDS_BACKBOARD_KEY <key>` (new terminal after)
3. `slothsounds night 30 "slow ambient for sleep" --memory`

The assistant remembers every generated vibe and suggests variations shaped
by your taste.

## 4. Tinker fine-tuned vibe translator (Best Use of Tinker)

1. `pip install tinker tinker-cookbook` (in the project venv)
2. `tinker auth login` with the HF26 Tinker credit
3. `python scripts/build_vibe_dataset.py` (add `--no-ollama` to skip Gemma)
4. `python scripts/train_vibe_translator.py` (~30 steps, LoRA on Qwen3.5-4B)

The fine-tuned model replaces the heuristic/Gemma vibe expander with a
specialist trained on lazy-vibe → MusicGen-prompt pairs.
