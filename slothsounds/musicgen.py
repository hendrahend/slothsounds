"""MusicGen engine wrapper.

Loads an open-weight MusicGen model through audiocraft and turns prompts
into raw mono float32 audio at 32 kHz. torch/audiocraft are imported
lazily so the rest of the package (and the test suite) runs without them.
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 32000
MAX_SEGMENT_SECONDS = 30  # MusicGen generates up to 30 s per call.


class MusicGenUnavailable(RuntimeError):
    """Raised when torch/audiocraft are missing. Carries install hints."""


class MusicGenEngine:
    """Thin wrapper around audiocraft's MusicGen."""

    def __init__(self, model_name: str = "facebook/musicgen-small", device: str | None = None):
        try:
            import torch  # noqa: F401
            from audiocraft.models import MusicGen
        except ImportError as exc:
            raise MusicGenUnavailable(
                "torch/audiocraft not installed.\n"
                "  Windows:  pip install torch --index-url https://download.pytorch.org/whl/cu121\n"
                "            pip install audiocraft --no-deps\n"
                "            pip install einops protobuf sentencepiece scipy timm transformers av xformers\n"
                "  (xformers is Linux-only; on Windows the model still runs without it)\n"
                "  or simply:  pip install -e '.[music]'"
            ) from exc

        import torch

        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._torch = torch
        self.model = MusicGen.get_pretrained(model_name, device=self.device)

    def generate(
        self,
        prompt: str,
        duration: int = 30,
        seed: int | None = None,
        temperature: float = 0.9,
        top_k: int = 250,
        cfg_coef: float = 3.0,
    ) -> np.ndarray:
        """Generate one clip. Returns mono float32 in [-1, 1] at 32 kHz."""
        duration = max(1, min(int(duration), MAX_SEGMENT_SECONDS))
        if seed is not None:
            self._torch.manual_seed(seed)

        self.model.set_generation_params(
            duration=duration,
            temperature=temperature,
            top_k=top_k,
            cfg_coef=cfg_coef,
        )
        wav = self.model.generate(
            [prompt],
            progress=False,
        )  # tensor [1, 1, samples] on CPU
        audio = wav[0, 0].detach().cpu().numpy().astype(np.float32)
        return audio

    def unload(self) -> None:
        """Free GPU memory."""
        model = getattr(self, "model", None)
        if model is not None:
            del model
            self.model = None
        if self._torch is not None and self._torch.cuda.is_available():
            self._torch.cuda.empty_cache()
