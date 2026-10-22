"""Sloth Sounds — local-first ambient music generator.

Type a lazy vibe, get a seamless wind-down loop. Open-weight models only;
nothing leaves your laptop.
"""

__version__ = "0.1.0"

from .config import Settings
from .vibe import expand_vibe
from .library import TrackLibrary

__all__ = ["Settings", "expand_vibe", "TrackLibrary", "__version__"]
