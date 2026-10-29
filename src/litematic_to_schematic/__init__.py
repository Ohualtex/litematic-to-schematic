"""Litematica (.litematic) to WorldEdit Sponge V2 (.schem) converter package."""

from .converter import (
    litematic_to_schem_final,
    normalize_identifier,
    format_block_state,
    encode_varint,
    decode_varint,
)

__version__ = "1.0.1"
__all__ = [
    "litematic_to_schem_final",
    "normalize_identifier",
    "format_block_state",
    "encode_varint",
    "decode_varint",
    "__version__",
]
