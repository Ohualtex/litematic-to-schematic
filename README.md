# 🛠️ Litematica to Schematic Converter

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Minecraft Version](https://img.shields.io/badge/minecraft-1.13%2B-orange.svg)
![WorldEdit Format](https://img.shields.io/badge/format-Sponge%20V2%20(.schem)-brightgreen.svg)

> Read this document in another language:  
> 🇹🇷 **[Türkçe (Turkish)](README_TR.md)**

A fast, reliable, and fully compliant Python CLI tool to convert Minecraft **Litematica** (`.litematic`) schematics directly into modern **WorldEdit / FastAsyncWorldEdit (FAWE)** compatible **Sponge V2** (`.schem`) format.

---

## 🎯 Purpose

In Minecraft, schematic files created by the Fabric/Quilt-based **Litematica** mod (`.litematic`) cannot be loaded directly by **WorldEdit** or **FAWE** plugins running on Forge, Paper, or Spigot servers.

This tool parses Litematica files directly at the NBT level without launching any Minecraft client and converts them into fully compliant `.schem` files.

---

## 🧱 Minecraft Version Compatibility

This converter supports **Minecraft 1.13 and all modern versions** (1.16, 1.20, 26.2+, etc.).

### Why is 1.13 the Minimum Supported Version?
With Minecraft 1.13, Mojang introduced **"The Flattening"**, a major overhaul of the internal world data structure. Before 1.13, blocks used numeric IDs and metadata values (e.g., Red Wool was `35:14`). Starting with 1.13, all blocks transitioned to string-based namespaced states (e.g., `minecraft:red_wool`). This converter generates **Sponge V2** NBT palettes which rely strictly on string-based block states and therefore does not support numeric ID formats from Minecraft 1.12.2 and older.

### Why is there No Upper Version Limit (Future-Proof)?
Block IDs and properties are **dynamically parsed** at runtime directly from the Litematica file (`block.id` and `block.properties`). No block names or properties are hardcoded into the Python script. When new blocks are added in future Minecraft updates (e.g., 1.20, 26.2, or beyond), the converter dynamically reads their exact namespaced IDs and attributes, writing them into the NBT tree for seamless WorldEdit recognition.

---

## ✨ Features

- 📦 **Full Sponge V2 NBT Standard Support**: NBT data tree structure fully compliant with WorldEdit v7+ and FAWE standards (`Version: 2`, `DataVersion: 2586`).
- 🔢 **LEB128 VarInt Byte Encoding**: Block indices are encoded into a byte array using dynamic VarInt (LEB128) format as required by Sponge V2 specifications.
- 📐 **Automatic Negative Coordinate Axis Alignment**: Regions saved with negative axis selection in Litematica are automatically sorted and aligned to the WorldEdit index order (`(Y * Length + Z) * Width + X`).
- 🎨 **Advanced BlockState & Palette Management**: `minecraft:` namespace prefixes, stair states, orientation, waterlogging, glass properties, and all block state key-values are fully preserved.
- ⚡ **Fast & Dual Interface Support**: Offers both a command-line interface (CLI) for advanced users and a single-click Windows batch script (`start.bat`).

---

## 📥 Installation

Ensure you have **Python 3.8+** installed on your system.

1. Clone or download this repository:
   ```bash
   git clone https://github.com/Ohualtex/Litematic-to-Schematic.git
   cd Litematic-to-Schematic
   ```

2. Install required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

You can use the converter in two different ways:

### 1. Command-Line Interface (CLI)

Basic conversion (creates output `.schem` with the same name as the input file):
```bash
python convert.py sample_structure.litematic
```

Specify a custom output file name:
```bash
python convert.py sample_structure.litematic -o my_building.schem
```

Display help menu:
```bash
python convert.py --help
```

---

### 2. Windows Batch Script (`start.bat`)

If you prefer a graphical interactive terminal prompt on Windows without typing CLI flags:

1. Double-click `start.bat`.
2. Type the name of your `.litematic` file when prompted (e.g., `house.litematic`).
3. Your `.schem` file will be generated in the same directory.

---

## 📁 Project Structure

```text
Litematic-to-Schematic/
├── .gitignore          # Git ignore file for Python, OS, IDE & schematic files
├── LICENSE             # MIT License file
├── README.md           # English documentation (default)
├── README_TR.md        # Turkish documentation
├── requirements.txt    # Python dependencies (litemapy, nbtlib)
├── convert.py          # Core converter script
└── start.bat           # Windows single-click launcher
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute it.

---

## 👤 Author

**Ohualtex**
- GitHub: [@Ohualtex](https://github.com/Ohualtex)
