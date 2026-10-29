import os
import numpy as np
from litemapy import Schematic
from nbtlib import File, Compound, Int, Short, ByteArray, IntArray, List, Double, String

DEFAULT_DATA_VERSION = 2586
MAX_SPONGE_DIMENSION = 32767
AIR_BLOCKS = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
VALID_OVERLAP_POLICIES = ("overwrite", "keep-first", "error")


def normalize_identifier(identifier: str) -> str:
    """Ensure a Minecraft resource identifier has a namespace without corrupting custom namespaces."""
    ident = str(identifier).strip()
    if not ident:
        return "minecraft:air"
    if ":" not in ident:
        return f"minecraft:{ident}"
    return ident


def format_block_state(block) -> str:
    """Convert a litemapy BlockState into a canonical Sponge V2 block state string."""
    block_name = normalize_identifier(block.id)
    props_raw = block.properties() if callable(block.properties) else block.properties

    if props_raw:
        props_dict = dict(props_raw.items()) if hasattr(props_raw, "items") else dict(props_raw)
        if props_dict:
            props_str = ",".join(f"{k}={v}" for k, v in sorted(props_dict.items()))
            return f"{block_name}[{props_str}]"
    return block_name


def encode_varint(values) -> bytearray:
    """Encode a sequence of non-negative palette indices into a LEB128 VarInt bytearray."""
    block_data = bytearray()
    for val in values:
        if val < 0:
            raise ValueError(f"Palette index cannot be negative: {val}")
        while True:
            byte = val & 0x7F
            val >>= 7
            if val != 0:
                block_data.append(byte | 0x80)
            else:
                block_data.append(byte)
                break
    return block_data


def decode_varint(data) -> list[int]:
    """Decode a LEB128 VarInt byte sequence (signed int8 or unsigned uint8) into integer indices."""
    result = []
    current = 0
    shift = 0
    for raw_byte in data:
        unsigned_byte = int(raw_byte) & 0xFF
        current |= (unsigned_byte & 0x7F) << shift
        if (unsigned_byte & 0x80) == 0:
            result.append(current)
            current = 0
            shift = 0
        else:
            shift += 7
            if shift >= 35:
                raise ValueError("Malformed VarInt in BlockData: value exceeds 32-bit integer")
    if shift != 0:
        raise ValueError("Malformed VarInt in BlockData: truncated sequence")
    return result


def _resolve_tile_entity_local_pos(reg, te) -> tuple[int, int, int]:
    """Resolve a TileEntity position to 0-based region-local coordinates (0..abs(dim)-1)."""
    tx, ty, tz = int(te.position[0]), int(te.position[1]), int(te.position[2])
    min_x, min_y, min_z = reg.min_x(), reg.min_y(), reg.min_z()

    if min_x == 0 and min_y == 0 and min_z == 0:
        return tx, ty, tz

    cand_reg = (tx - min_x, ty - min_y, tz - min_z)
    cand_store = (tx, ty, tz)

    w, h, length = abs(reg.width), abs(reg.height), abs(reg.length)
    reg_valid = (0 <= cand_reg[0] < w) and (0 <= cand_reg[1] < h) and (0 <= cand_reg[2] < length)
    store_valid = (0 <= cand_store[0] < w) and (0 <= cand_store[1] < h) and (0 <= cand_store[2] < length)

    if reg_valid and not store_valid:
        return cand_reg
    if store_valid and not reg_valid:
        return cand_store
    if reg_valid and store_valid:
        raw_te_id = te.data.get("id", te.data.get("Id", ""))
        te_id = normalize_identifier(raw_te_id) if raw_te_id else ""
        blk_at_reg = normalize_identifier(reg[tx, ty, tz].id)
        blk_at_store = normalize_identifier(reg[tx + min_x, ty + min_y, tz + min_z].id)
        if te_id:
            if blk_at_reg == te_id and blk_at_store != te_id:
                return cand_reg
            if blk_at_store == te_id and blk_at_reg != te_id:
                return cand_store
        if blk_at_reg not in AIR_BLOCKS and blk_at_store in AIR_BLOCKS:
            return cand_reg
        if blk_at_store not in AIR_BLOCKS and blk_at_reg in AIR_BLOCKS:
            return cand_store

    return cand_reg if reg_valid else cand_store


def litematic_to_schem_final(
    input_file: str,
    output_file: str,
    on_overlap: str = "overwrite",
) -> bool:
    """Convert a Litematica (.litematic) file to a WorldEdit Sponge V2 (.schem) file.

    :param input_file:  Path to the source .litematic file.
    :param output_file: Path to the destination .schem file.
    :param on_overlap:  Conflict resolution policy when multiple regions overlap with non-air blocks
                        ('overwrite', 'keep-first', or 'error').
    :returns:           True if conversion succeeded, False otherwise.
    """
    if on_overlap not in VALID_OVERLAP_POLICIES:
        raise ValueError(f"Invalid on_overlap policy '{on_overlap}'. Must be one of {VALID_OVERLAP_POLICIES}.")

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        return False

    print(f"Reading '{input_file}' and analyzing dimensions...")
    try:
        schem = Schematic.load(input_file)
    except Exception as exc:
        print(f"Error: Failed to read valid Litematica data from '{input_file}': {exc}")
        return False

    if not schem.regions or len(schem.regions) == 0:
        print(f"Error: '{input_file}' does not contain any regions!")
        return False

    regions = list(schem.regions.values())
    region_count = len(regions)

    global_min_x = min(r.min_schem_x() for r in regions)
    global_max_x = max(r.max_schem_x() for r in regions)
    global_min_y = min(r.min_schem_y() for r in regions)
    global_max_y = max(r.max_schem_y() for r in regions)
    global_min_z = min(r.min_schem_z() for r in regions)
    global_max_z = max(r.max_schem_z() for r in regions)

    width = global_max_x - global_min_x + 1
    height = global_max_y - global_min_y + 1
    length = global_max_z - global_min_z + 1

    if width <= 0 or height <= 0 or length <= 0:
        print(f"Error: Invalid schematic dimensions ({width}x{height}x{length})!")
        return False

    if width > MAX_SPONGE_DIMENSION or height > MAX_SPONGE_DIMENSION or length > MAX_SPONGE_DIMENSION:
        print(
            f"Error: Schematic dimensions ({width}x{height}x{length}) exceed "
            f"Sponge V2 Short limit ({MAX_SPONGE_DIMENSION})!"
        )
        return False

    raw_mc_version = getattr(schem, "mc_version", None)
    try:
        data_version = int(raw_mc_version) if raw_mc_version is not None and int(raw_mc_version) > 0 else DEFAULT_DATA_VERSION
        if raw_mc_version is None or int(raw_mc_version) <= 0:
            print(f"Warning: Missing or invalid MinecraftDataVersion; defaulting to {DEFAULT_DATA_VERSION}.")
    except (ValueError, TypeError):
        data_version = DEFAULT_DATA_VERSION
        print(f"Warning: Unparseable MinecraftDataVersion '{raw_mc_version}'; defaulting to {DEFAULT_DATA_VERSION}.")

    print(f"Dimensions: {width}x{height}x{length} (W x H x L) across {region_count} region(s) (DataVersion: {data_version})")

    palette: dict[str, int] = {}
    index_to_state: dict[int, str] = {}
    palette_max = 0

    def get_or_create_palette_index(state_str: str) -> int:
        nonlocal palette_max
        if state_str not in palette:
            palette[state_str] = palette_max
            index_to_state[palette_max] = state_str
            palette_max += 1
        return palette[state_str]

    # -1 indicates an unwritten cell (will become minecraft:air if left unwritten)
    block_indices = [-1] * (width * height * length)
    overlap_count = 0

    block_entities_by_pos: dict[tuple[int, int, int], Compound] = {}
    entities = List[Compound]()
    total_block_ticks = 0
    total_fluid_ticks = 0

    print("Indexing block states and building palette...")
    for reg_name, reg in schem.regions.items():
        offset_x = reg.min_schem_x() - global_min_x
        offset_y = reg.min_schem_y() - global_min_y
        offset_z = reg.min_schem_z() - global_min_z

        x_coords = sorted(list(reg.range_x()))
        y_coords = sorted(list(reg.range_y()))
        z_coords = sorted(list(reg.range_z()))

        min_x = x_coords[0]
        min_y = y_coords[0]
        min_z = z_coords[0]

        skipped_positions: set[tuple[int, int, int]] = set()

        for y_idx, y in enumerate(y_coords):
            gy = offset_y + y_idx
            for z_idx, z in enumerate(z_coords):
                gz = offset_z + z_idx
                row_base = (gy * length + gz) * width
                for x_idx, x in enumerate(x_coords):
                    gx = offset_x + x_idx
                    index = row_base + gx

                    full_name = format_block_state(reg[x, y, z])
                    existing_idx = block_indices[index]

                    if existing_idx == -1:
                        block_indices[index] = get_or_create_palette_index(full_name)
                    else:
                        existing_name = index_to_state[existing_idx]
                        is_existing_air = existing_name in AIR_BLOCKS
                        is_new_air = full_name in AIR_BLOCKS

                        if not is_existing_air and is_new_air:
                            # Do not let air from an overlapping bounding box erase an existing solid block
                            skipped_positions.add((gx, gy, gz))
                            continue
                        elif is_existing_air and not is_new_air:
                            block_indices[index] = get_or_create_palette_index(full_name)
                        elif is_existing_air and is_new_air:
                            continue
                        else:
                            # Both existing and new blocks are non-air
                            overlap_count += 1
                            if on_overlap == "error":
                                print(
                                    f"Error: Region '{reg_name}' overlaps existing non-air block "
                                    f"at global position ({gx}, {gy}, {gz})!"
                                )
                                return False
                            elif on_overlap == "keep-first":
                                skipped_positions.add((gx, gy, gz))
                                continue
                            else:
                                # overwrite
                                block_indices[index] = get_or_create_palette_index(full_name)
                                block_entities_by_pos.pop((gx, gy, gz), None)

        # Process BlockEntities for this region
        for te in reg.tile_entities:
            lx, ly, lz = _resolve_tile_entity_local_pos(reg, te)
            gx = offset_x + lx
            gy = offset_y + ly
            gz = offset_z + lz

            if (gx, gy, gz) in skipped_positions:
                continue

            te_tag = Compound()
            for k, v in te.data.items():
                if k not in ("x", "y", "z", "id"):
                    te_tag[k] = v

            te_tag["Pos"] = IntArray([Int(gx), Int(gy), Int(gz)])

            if "id" in te.data:
                te_tag["Id"] = String(normalize_identifier(str(te.data["id"])))
            elif "Id" in te_tag:
                te_tag["Id"] = String(normalize_identifier(str(te_tag["Id"])))
            else:
                # Infer block entity ID from the block at that coordinate
                blk_idx = block_indices[(gy * length + gz) * width + gx]
                if blk_idx != -1:
                    blk_state = index_to_state[blk_idx].split("[")[0]
                    te_tag["Id"] = String(normalize_identifier(blk_state))

            block_entities_by_pos[(gx, gy, gz)] = te_tag

        # Process Entities for this region
        for e in reg.entities:
            e_tag = Compound()
            for k, v in e.data.items():
                if k not in ("id", "UUID"):
                    e_tag[k] = v

            ex, ey, ez = e.position
            rx = (ex - min_x) + offset_x
            ry = (ey - min_y) + offset_y
            rz = (ez - min_z) + offset_z
            e_tag["Pos"] = List[Double]([Double(rx), Double(ry), Double(rz)])

            if "id" in e.data:
                e_tag["Id"] = String(normalize_identifier(str(e.data["id"])))
            elif "Id" in e_tag:
                e_tag["Id"] = String(normalize_identifier(str(e_tag["Id"])))
            else:
                e_tag["Id"] = String(normalize_identifier(e.id))

            if "TileX" in e_tag:
                e_tag["TileX"] = Int(int(e_tag["TileX"]) - min_x + offset_x)
            if "TileY" in e_tag:
                e_tag["TileY"] = Int(int(e_tag["TileY"]) - min_y + offset_y)
            if "TileZ" in e_tag:
                e_tag["TileZ"] = Int(int(e_tag["TileZ"]) - min_z + offset_z)

            entities.append(e_tag)

        total_block_ticks += len(getattr(reg, "block_ticks", []))
        total_fluid_ticks += len(getattr(reg, "fluid_ticks", []))

    # Fill any remaining unwritten space between regions with minecraft:air
    if any(idx == -1 for idx in block_indices):
        air_idx = get_or_create_palette_index("minecraft:air")
        for i, idx in enumerate(block_indices):
            if idx == -1:
                block_indices[i] = air_idx

    if overlap_count > 0:
        print(
            f"Warning: Detected {overlap_count} overlapping non-air block(s) across regions "
            f"(resolved using '{on_overlap}' policy)."
        )

    if total_block_ticks > 0 or total_fluid_ticks > 0:
        print(
            f"Notice: Skipped {total_block_ticks} pending block tick(s) and "
            f"{total_fluid_ticks} pending fluid tick(s) (not supported by Sponge V2 format)."
        )

    print("Converting block data to VarInt (LEB128) format...")
    block_data = encode_varint(block_indices)
    signed_block_data = np.frombuffer(block_data, dtype=np.int8)

    print("Processing BlockEntities (container inventories, signs, etc.)...")
    block_entities = List[Compound](list(block_entities_by_pos.values()))
    print(f"Processed {len(block_entities)} block entities.")

    print("Processing Entities (minecarts, armor stands, item frames, etc.)...")
    print(f"Processed {len(entities)} entities.")

    print("Building Sponge V2 NBT tree structure...")
    palette_nbt = Compound({k: Int(v) for k, v in palette.items()})

    schematic_nbt = Compound({
        "Version": Int(2),
        "DataVersion": Int(data_version),
        "Width": Short(width),
        "Height": Short(height),
        "Length": Short(length),
        "PaletteMax": Int(palette_max),
        "Palette": palette_nbt,
        "BlockData": ByteArray(signed_block_data),
        "BlockEntities": block_entities,
        "Entities": entities,
        "Metadata": Compound({
            "WEOffsetX": Int(0),
            "WEOffsetY": Int(0),
            "WEOffsetZ": Int(0),
        }),
        "Offset": IntArray([0, 0, 0]),
    })

    # Save NBT file with root tag "Schematic" and gzipped compression
    nbt_file = File(schematic_nbt, gzipped=True)
    nbt_file.root_name = "Schematic"
    nbt_file.save(output_file)

    print(f"Success! '{output_file}' has been created successfully.")
    return True
