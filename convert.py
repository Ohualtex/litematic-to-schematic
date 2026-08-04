import os
import argparse
from litemapy import Schematic
from nbtlib import File, Compound, Int, Short, ByteArray, IntArray, List, Double

def litematic_to_schem_final(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        return

    print(f"Reading '{input_file}' and analyzing dimensions...")
    schem = Schematic.load(input_file)
    reg = list(schem.regions.values())[0]

    width = abs(reg.width)
    height = abs(reg.height)
    length = abs(reg.length)

    print(f"Dimensions: {width}x{height}x{length} (W x H x L)")

    palette = {}
    palette_max = 0
    
    # Sort coordinates to handle potential negative selection bounds in Litematica
    x_coords = sorted(list(reg.xrange()))
    y_coords = sorted(list(reg.yrange()))
    z_coords = sorted(list(reg.zrange()))

    min_x = min(x_coords)
    min_y = min(y_coords)
    min_z = min(z_coords)

    # WorldEdit index ordering: (Y * Length + Z) * Width + X
    block_indices = [0] * (width * height * length)

    print("Indexing block states and building palette...")
    for y_idx, y in enumerate(y_coords):
        for z_idx, z in enumerate(z_coords):
            for x_idx, x in enumerate(x_coords):
                block = reg[x, y, z]
                
                block_name = block.id
                if not block_name.startswith("minecraft:"):
                    block_name = f"minecraft:{block_name}"
                
                props_raw = block.properties() if callable(block.properties) else block.properties
                
                if props_raw:
                    props_dict = dict(props_raw.items()) if hasattr(props_raw, 'items') else dict(props_raw)
                    if props_dict:
                        props_str = ",".join(f"{k}={v}" for k, v in sorted(props_dict.items()))
                        full_name = f"{block_name}[{props_str}]"
                    else:
                        full_name = block_name
                else:
                    full_name = block_name

                if full_name not in palette:
                    palette[full_name] = palette_max
                    palette_max += 1

                index = (y_idx * length + z_idx) * width + x_idx
                block_indices[index] = palette[full_name]

    print("Converting block data to VarInt (LEB128) format...")
    block_data = bytearray()
    for val in block_indices:
        while True:
            byte = val & 0x7F
            val >>= 7
            if val != 0:
                byte |= 0x80
                block_data.append(byte)
            else:
                block_data.append(byte)
                break

    print("Processing BlockEntities (container inventories, signs, etc.)...")
    block_entities = List[Compound]()
    for te in reg.tile_entities:
        te_tag = Compound()
        for k, v in te.data.items():
            te_tag[k] = v
        x_idx, y_idx, z_idx = te.position
        te_tag['Pos'] = IntArray([Int(x_idx), Int(y_idx), Int(z_idx)])
        if 'id' in te_tag:
            te_tag['Id'] = te_tag['id']
        block_entities.append(te_tag)
    print(f"Processed {len(block_entities)} block entities.")

    print("Processing Entities (minecarts, armor stands, item frames, etc.)...")
    entities = List[Compound]()
    for e in reg.entities:
        e_tag = Compound()
        for k, v in e.data.items():
            e_tag[k] = v
        ex, ey, ez = e.position
        rx = ex - min_x
        ry = ey - min_y
        rz = ez - min_z
        e_tag['Pos'] = List[Double]([Double(rx), Double(ry), Double(rz)])
        
        # Sponge V2 format: 'Id' tag required, remove 'id' and hardcoded 'UUID' so WorldEdit generates fresh UUIDs
        if 'id' in e_tag:
            e_tag['Id'] = e_tag['id']
            del e_tag['id']
        elif 'Id' not in e_tag:
            e_tag['Id'] = String(f"minecraft:{e.id}")
            
        if 'UUID' in e_tag:
            del e_tag['UUID']

        if 'TileX' in e_tag:
            e_tag['TileX'] = Int(int(e_tag['TileX']) - min_x)
            e_tag['TileY'] = Int(int(e_tag['TileY']) - min_y)
            e_tag['TileZ'] = Int(int(e_tag['TileZ']) - min_z)
        entities.append(e_tag)
    print(f"Processed {len(entities)} entities.")

    print("Building Sponge V2 NBT tree structure...")
    palette_nbt = Compound({k: Int(v) for k, v in palette.items()})

    schematic_nbt = Compound({
        'Version': Int(2),
        'DataVersion': Int(2586), 
        'Width': Short(width),
        'Height': Short(height),
        'Length': Short(length),
        'PaletteMax': Int(palette_max),
        'Palette': palette_nbt,
        'BlockData': ByteArray(block_data),
        'BlockEntities': block_entities,
        'Entities': entities,
        'Metadata': Compound({
            'WEOffsetX': Int(0),
            'WEOffsetY': Int(0),
            'WEOffsetZ': Int(0)
        }),
        'Offset': IntArray([0, 0, 0])
    })

    # Save NBT file with root tag "Schematic" and gzipped compression
    nbt_file = File(schematic_nbt, gzipped=True)
    nbt_file.root_name = "Schematic"  
    nbt_file.save(output_file)
    
    print(f"Success! '{output_file}' has been created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converts Litematica files (.litematic) directly to WorldEdit Sponge V2 Schematic (.schem) format.")
    parser.add_argument("input", help="Path to the input .litematic file")
    parser.add_argument("-o", "--output", help="Optional: Custom output .schem file path", default=None)
    
    args = parser.parse_args()
    
    input_file = args.input
    
    if args.output:
        output_file = args.output
    else:
        # Strip extension and append .schem
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.schem"
        
    litematic_to_schem_final(input_file, output_file)