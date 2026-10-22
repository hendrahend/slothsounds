"""Install the Windows xformers shim into the active venv.

xformers has no Windows wheels, but audiocraft imports it unconditionally.
audiocraft's default attention backend is 'torch' (native SDPA), so the
shim only satisfies the import surface. Run once after creating the venv:

    python scripts/install_windows_shims.py

On Linux/macOS this is unnecessary — install real xformers instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

INIT = '''"""Minimal Windows shim for the `xformers` package.

xformers publishes Linux-only wheels, but audiocraft imports it
unconditionally (`from xformers import ops`). audiocraft's default
attention backend is 'torch' (F.scaled_dot_product_attention), so this
shim only needs to satisfy the import and provide the few symbols the
torch code path touches. The xformers backend is never selected.

Recreate with:  python scripts/install_windows_shims.py
"""

__version__ = "0.0.23.windows-shim"
'''

OPS = '''"""Shim for `xformers.ops` on Windows (no official wheels exist).

Provides the three symbols audiocraft touches:
- `unbind`            — splits packed qkv [B, H, 3, D] -> (q, k, v)
- `LowerTriangularMask` — placeholder; the torch backend only checks
                        `attn_mask is not None`
- `memory_efficient_attention` — falls back to torch SDPA (only used if
                        someone explicitly selects the xformers backend)
"""

import torch
import torch.nn.functional as F


def unbind(x: torch.Tensor, dim: int = 2):
    """Split a packed qkv tensor into (q, k, v). Same as torch.unbind."""
    return x.unbind(dim)


class LowerTriangularMask:
    """Placeholder mask; the torch SDPA path only checks for None."""

    def __init__(self, *args, **kwargs):
        pass


def memory_efficient_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attn_bias=None,
    p: float = 0.0,
    scale: float | None = None,
    **kwargs,
) -> torch.Tensor:
    """Fallback to torch SDPA for the (unused) xformers backend."""
    if attn_bias is not None and not isinstance(attn_bias, torch.Tensor):
        # LowerTriangularMask or similar object -> approximate with causal.
        return F.scaled_dot_product_attention(
            query, key, value, dropout_p=p, is_causal=True, scale=scale
        )
    return F.scaled_dot_product_attention(
        query, key, value, attn_mask=attn_bias, dropout_p=p, scale=scale
    )
'''

PROFILER = '''"""Shim for `xformers.profiler` on Windows (no official wheels exist).

audiocraft's `_is_profiled()` does:
    from xformers.profiler import profiler
    return profiler._Profiler._CURRENT_PROFILER is not None

In real xformers, `profiler` is the module and `_Profiler` is a class in
it. With no profiler ever activated, `_CURRENT_PROFILER` must be None.
"""


class _Profiler:
    _CURRENT_PROFILER = None


class _ProfilerModule:
    """Stand-in for the module object, exposing the _Profiler class."""

    _Profiler = _Profiler


profiler = _ProfilerModule()
'''


def site_packages() -> Path:
    for entry in sys.path:
        if entry.endswith("site-packages"):
            return Path(entry)
    raise SystemExit("no site-packages directory found on sys.path")


def main() -> None:
    target = site_packages() / "xformers"
    target.mkdir(exist_ok=True)
    (target / "__init__.py").write_text(INIT, encoding="utf-8")
    (target / "ops.py").write_text(OPS, encoding="utf-8")
    (target / "profiler.py").write_text(PROFILER, encoding="utf-8")
    print(f"xformers shim installed at {target}")


if __name__ == "__main__":
    main()
