# 🛠️ Litematica to Schematic Converter

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Minecraft Version](https://img.shields.io/badge/minecraft-1.13%2B-orange.svg)
![WorldEdit Format](https://img.shields.io/badge/format-Sponge%20V2%20(.schem)-brightgreen.svg)

> Read this document in another language:  
> 🇹🇷 **[Türkçe (Turkish)](README_TR.md)**

A fast, reliable Python CLI tool and library to convert Minecraft **Litematica** (`.litematic`) schematics directly into **WorldEdit / FastAsyncWorldEdit (FAWE)** compatible **Sponge V2** (`.schem`) format.

---

## 🎯 Purpose

In Minecraft, schematic files created by the Fabric/Quilt-based **Litematica** mod (`.litematic`) cannot be loaded directly by **WorldEdit** or **FAWE** plugins running on Forge, NeoForge, Paper, or Spigot servers.

This tool parses Litematica files directly at the NBT level without launching a Minecraft client and converts them into standard Sponge V2 `.schem` files.

---

## ✨ Features

- 🧩 **Multi-Region Merging & Conflict Policies**: Automatically computes the global bounding box across all regions in a `.litematic` file, aligns relative region offsets, prevents air blocks from erasing solid blocks, and provides configurable conflict resolution (`--on-overlap overwrite|keep-first|error`).
- 📦 **Sponge V2 NBT Structure & Dynamic `DataVersion`**: Preserves the source schematic's `MinecraftDataVersion` (falling back to `2586` only if missing) and builds a Sponge V2 NBT tree (`Version: 2`).
- 🧰 **BlockEntities & Entities Preservation**: Transfers container inventories (chests, barrels, shulker boxes, signs) and entities (armor stands, item frames, paintings, minecarts) with global coordinate alignment, `TileX/Y/Z` recalculation, and `UUID`/`Id` sanitization.
- 🔧 **Modded & Vanilla Namespace Integrity**: Preserves custom mod namespaces (e.g., `create:brass_casing`, `ae2:controller[state=online]`) while automatically prefixing un-namespaced vanilla identifiers with `minecraft:`.
- 🔢 **LEB128 VarInt Byte Encoding**: Encodes block palette indices into signed 8-bit NBT `ByteArray` streams using dynamic LEB128 VarInt encoding, supporting palettes of any size (`> 128` block states).
- 📐 **Negative Coordinate Axis Alignment**: Regions saved with negative selection bounds in Litematica are automatically normalized to WorldEdit's `(Y * Length + Z) * Width + X` index ordering.

---

## 🧱 Minecraft Version Compatibility & Scope

This converter supports **Minecraft 1.13+ schematics** (1.13 through 1.20, 1.21+, etc.).

### Why is 1.13 the Minimum Supported Version?
With Minecraft 1.13 (**"The Flattening"**), blocks transitioned from numeric IDs and metadata values (e.g., `35:14`) to string-based namespaced block states (e.g., `minecraft:red_wool`). Sponge V2 palettes rely strictly on string-based block states and do not support legacy 1.12.2 numeric IDs.

### How Newer Versions & Modded Blocks Work
Block IDs and block state properties (`block.id` and `block.properties`) are parsed dynamically from the input `.litematic` file alongside its `MinecraftDataVersion` tag, without a hardcoded block registry.

### Known Format Limitations
- **No Cross-Version Block ID Remapping**: The converter preserves the source schematic's `DataVersion` and block state strings as-is. Loading a 1.21 schematic on an older 1.16 server will not downgrade blocks that did not exist in 1.16.
- **Pending Ticks**: Litematica's `PendingBlockTicks` and `PendingFluidTicks` have no standard equivalent in WorldEdit's Sponge V2 importer and are skipped with an informational console notice when present.
- **Dimension Bounds**: Sponge V2 stores `Width`, `Height`, and `Length` as signed 16-bit `Short` integers, limiting each axis of the combined bounding box to a maximum of `32,767` blocks.

---

## 📥 Installation

Ensure you have **Python 3.8+** installed on your system.

1. Clone the repository:
   ```bash
   git clone https://github.com/Ohualtex/litematic-to-schematic.git
   cd litematic-to-schematic
   ```

2. Install as a Python package (recommended, installs CLI commands `litematic-to-schematic` and `litematic2schem`):
   ```bash
   pip install .
   ```
   Or install dependencies only for direct script execution:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

### 1. Command-Line Interface (CLI)

Using the installed CLI command (or `python convert.py` / `python -m litematic_to_schematic`):
```bash
litematic-to-schematic sample_structure.litematic
```

Specify a custom output file path and multi-region overlap policy:
```bash
litematic2schem sample_structure.litematic -o my_building.schem --on-overlap keep-first
```

Display help menu:
```bash
litematic-to-schematic --help
```

### 2. Windows Batch Script (`start.bat`)

1. Double-click `start.bat`.
2. Enter the name of your `.litematic` file when prompted (e.g., `house.litematic`).
3. Your `.schem` file will be generated in the same directory.

### 3. Running the Test Suite

```bash
python -m unittest discover -s tests -v
```

---

## 📁 Project Structure

```text
litematic-to-schematic/
├── pyproject.toml                  # PEP 621 package configuration & CLI entry points
├── requirements.txt                # Runtime dependencies (litemapy, nbtlib)
├── convert.py                      # Backward-compatible CLI/API wrapper script
├── start.bat                       # Windows interactive batch launcher
├── README.md                       # English documentation (default)
├── README_TR.md                    # Turkish documentation
├── LICENSE                         # MIT License
├── src/
│   └── litematic_to_schematic/
│       ├── __init__.py             # Package version & public API exports
│       ├── __main__.py             # `python -m litematic_to_schematic` entry point
│       ├── converter.py            # Core Litematica -> Sponge V2 conversion engine
│       └── cli.py                  # Argparse command-line interface
└── tests/
    └── test_converter.py           # Unit & integration test matrix (T01-T14)
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Ohualtex**
- GitHub: [@Ohualtex](https://github.com/Ohualtex)
