#!/usr/bin/env bash
# Sloth Sounds bootstrap: install the heavy extras and pull local models.
# Run once after cloning. Works in Git Bash / WSL / macOS / Linux.
set -euo pipefail

echo "==> Installing slothsounds with music extras"
pip install -e ".[music]"

echo
echo "==> Windows + NVIDIA GPU? Install CUDA torch explicitly:"
echo "    pip install torch --index-url https://download.pytorch.org/whl/cu121"
echo "    (audiocraft pulls CPU torch by default on Windows)"
echo
echo "==> Windows note: xformers has no Windows wheels. If 'pip install"
echo "    audiocraft' fails, use:"
echo "      pip install audiocraft --no-deps"
echo "      pip install einops protobuf sentencepiece scipy timm transformers av"
echo
echo "==> Optional: Ollama + Gemma for LLM vibe expansion"
echo "    install Ollama from https://ollama.com, then:"
echo "      ollama pull gemma3:4b"
echo "    (without Ollama, keyword vibe expansion is used automatically)"
echo
echo "==> Optional: ffmpeg for MP3 export"
echo
echo "==> First run downloads the MusicGen weights (~1.5 GB for small)."
echo "    Then try:"
echo "      slothsounds doctor"
echo "      slothsounds gen \"rainy sunday piano\""
echo "      slothsounds night 30 \"slow ambient for sleep\""
