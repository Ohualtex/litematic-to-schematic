"""Backward-compatible CLI and API entry point for Litematic-to-Schematic."""

import os
import sys

# Ensure the local 'src' directory is importable even without 'pip install -e .'
_SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from litematic_to_schematic.converter import litematic_to_schem_final  # noqa: E402
from litematic_to_schematic.cli import main  # noqa: E402

__all__ = ["litematic_to_schem_final", "main"]

if __name__ == "__main__":
    main()
