import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

# Ensure src is on sys.path for testing without global installation
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from litemapy import Schematic, Region, BlockState, Entity, TileEntity  # noqa: E402
from nbtlib import File, Compound, Int, String, List, Byte  # noqa: E402
from litematic_to_schematic.converter import (  # noqa: E402
    litematic_to_schem_final,
    decode_varint,
    normalize_identifier,
)


def _read_schem_blocks(nbt_root: Compound) -> dict[tuple[int, int, int], str]:
    """Decode a Sponge V2 Schematic NBT root into a {(x, y, z): state_str} dictionary."""
    width = int(nbt_root["Width"])
    height = int(nbt_root["Height"])
    length = int(nbt_root["Length"])
    palette = {int(idx): str(state) for state, idx in nbt_root["Palette"].items()}
    indices = decode_varint(nbt_root["BlockData"])
    assert len(indices) == width * height * length, (
        f"Expected {width * height * length} blocks, got {len(indices)}"
    )
    blocks = {}
    for y in range(height):
        for z in range(length):
            for x in range(width):
                flat_idx = (y * length + z) * width + x
                blocks[(x, y, z)] = palette[indices[flat_idx]]
    return blocks


def _run_quiet(func, *args, **kwargs) -> tuple[bool, str]:
    """Run converter while capturing console stdout."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = func(*args, **kwargs)
    return result, buf.getvalue()


class TestLitematicToSchematicMatrix(unittest.TestCase):
    """Comprehensive test suite covering T01 through T14 from the Code Review Report."""

    def test_t01_single_region_simple_house(self):
        """T01: Single-region simple structure transfers all blocks accurately."""
        reg = Region(0, 0, 0, 4, 3, 4)
        reg[0, 0, 0] = BlockState("minecraft:cobblestone")
        reg[3, 2, 3] = BlockState("minecraft:oak_planks")
        schem = reg.as_schematic(name="SimpleHouse", mc_version=2586)

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t01.litematic")
            out_path = os.path.join(tmpdir, "t01.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            self.assertEqual(int(nbt["Width"]), 4)
            self.assertEqual(int(nbt["Height"]), 3)
            self.assertEqual(int(nbt["Length"]), 4)
            blocks = _read_schem_blocks(nbt)
            self.assertEqual(blocks[(0, 0, 0)], "minecraft:cobblestone")
            self.assertEqual(blocks[(3, 2, 3)], "minecraft:oak_planks")
            self.assertEqual(blocks[(1, 1, 1)], "minecraft:air")

    def test_t02_three_region_castle_merged(self):
        """T02 (BUG-01): Multi-region schematic (3 regions) merges all regions into a global bounding box."""
        r1 = Region(0, 0, 0, 2, 2, 2)
        r1[0, 0, 0] = BlockState("minecraft:stone_bricks")

        r2 = Region(5, 0, 0, 2, 2, 2)
        r2[1, 1, 1] = BlockState("minecraft:gold_block")

        r3 = Region(-3, 2, 4, 2, 2, 2)
        r3[0, 0, 0] = BlockState("minecraft:diamond_block")

        schem = Schematic(
            name="ThreeRegionCastle",
            regions={"TowerA": r1, "TowerB": r2, "Keep": r3},
            mc_version=3465,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t02.litematic")
            out_path = os.path.join(tmpdir, "t02.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            # Global X: -3 .. 6 (width 10), Global Y: 0 .. 3 (height 4), Global Z: 0 .. 5 (length 6)
            self.assertEqual(int(nbt["Width"]), 10)
            self.assertEqual(int(nbt["Height"]), 4)
            self.assertEqual(int(nbt["Length"]), 6)

            blocks = _read_schem_blocks(nbt)
            self.assertEqual(blocks[(3, 0, 0)], "minecraft:stone_bricks")
            self.assertEqual(blocks[(9, 1, 1)], "minecraft:gold_block")
            self.assertEqual(blocks[(0, 2, 4)], "minecraft:diamond_block")

    def test_t03_negative_dimensions_alignment(self):
        """T03: Negative X/Y/Z region dimensions preserve exact spatial order and block orientation."""
        reg = Region(0, 0, 0, -3, -2, -3)
        reg[-2, -1, -2] = BlockState("minecraft:emerald_block")
        reg[0, 0, 0] = BlockState("minecraft:redstone_block")
        schem = reg.as_schematic(name="NegativeBounds")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t03.litematic")
            out_path = os.path.join(tmpdir, "t03.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            blocks = _read_schem_blocks(nbt)
            self.assertEqual(blocks[(0, 0, 0)], "minecraft:emerald_block")
            self.assertEqual(blocks[(2, 1, 2)], "minecraft:redstone_block")

    def test_t04_modded_block_namespace_preservation(self):
        """T04 (BUG-02): Modded block namespaces (e.g., create:brass_casing) are preserved intact."""
        self.assertEqual(normalize_identifier("create:brass_casing"), "create:brass_casing")
        self.assertEqual(normalize_identifier("stone"), "minecraft:stone")
        self.assertEqual(normalize_identifier("minecraft:dirt"), "minecraft:dirt")

        reg = Region(0, 0, 0, 2, 1, 1)
        reg[0, 0, 0] = BlockState("create:brass_casing")
        reg[1, 0, 0] = BlockState("ae2:controller", state="online")
        schem = reg.as_schematic(name="ModdedBlocks")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t04.litematic")
            out_path = os.path.join(tmpdir, "t04.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            blocks = _read_schem_blocks(nbt)
            self.assertEqual(blocks[(0, 0, 0)], "create:brass_casing")
            self.assertEqual(blocks[(1, 0, 0)], "ae2:controller[state=online]")

    def test_t05_stairs_and_slabs_blockstate_properties(self):
        """T05: BlockState properties (stairs, slabs, waterlogged, facing) are sorted and preserved."""
        reg = Region(0, 0, 0, 2, 1, 1)
        reg[0, 0, 0] = BlockState(
            "minecraft:oak_stairs",
            facing="north",
            half="bottom",
            shape="straight",
            waterlogged="false",
        )
        reg[1, 0, 0] = BlockState("minecraft:stone_slab", type="top", waterlogged="true")
        schem = reg.as_schematic(name="BlockStates")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t05.litematic")
            out_path = os.path.join(tmpdir, "t05.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            blocks = _read_schem_blocks(nbt)
            self.assertEqual(
                blocks[(0, 0, 0)],
                "minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]",
            )
            self.assertEqual(
                blocks[(1, 0, 0)],
                "minecraft:stone_slab[type=top,waterlogged=true]",
            )

    def test_t06_chest_and_inventory_block_entity(self):
        """T06 (RISK-01): Chest BlockEntity inventory and coordinates are preserved and legacy x/y/z/id stripped."""
        reg = Region(5, 2, 3, 3, 2, 3)
        reg[1, 0, 2] = BlockState("minecraft:chest", facing="south")
        chest_nbt = Compound({
            "id": String("minecraft:chest"),
            "x": Int(1),
            "y": Int(0),
            "z": Int(2),
            "Items": List[Compound]([
                Compound({"Slot": Byte(0), "id": String("minecraft:diamond"), "Count": Byte(64)})
            ]),
        })
        reg.tile_entities.append(TileEntity(chest_nbt))
        schem = Schematic(name="ChestTest", regions={"Main": reg})

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t06.litematic")
            out_path = os.path.join(tmpdir, "t06.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            self.assertEqual(len(nbt["BlockEntities"]), 1)
            be = nbt["BlockEntities"][0]
            self.assertEqual(str(be["Id"]), "minecraft:chest")
            self.assertEqual(list(be["Pos"]), [1, 0, 2])
            self.assertNotIn("x", be)
            self.assertNotIn("y", be)
            self.assertNotIn("z", be)
            self.assertNotIn("id", be)
            self.assertEqual(len(be["Items"]), 1)
            self.assertEqual(str(be["Items"][0]["id"]), "minecraft:diamond")

    def test_t07_sign_block_entity_in_negative_and_offset_regions(self):
        """T07 (RISK-01): Sign BlockEntity text and position are accurately mapped in negative/multi-region space."""
        r1 = Region(0, 0, 0, 2, 2, 2)
        r1[0, 0, 0] = BlockState("minecraft:stone")

        r2 = Region(4, 0, 0, -2, 2, -2)
        r2[-1, 1, -1] = BlockState("minecraft:oak_sign")
        sign_nbt = Compound({
            "id": String("minecraft:sign"),
            "x": Int(-1),
            "y": Int(1),
            "z": Int(-1),
            "Text1": String('{"text":"Hello WorldEdit"}'),
        })
        r2.tile_entities.append(TileEntity(sign_nbt))
        schem = Schematic(name="SignTest", regions={"Base": r1, "SignRegion": r2})

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t07.litematic")
            out_path = os.path.join(tmpdir, "t07.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            blocks = _read_schem_blocks(nbt)
            self.assertEqual(blocks[(3, 1, 0)], "minecraft:oak_sign")
            self.assertEqual(len(nbt["BlockEntities"]), 1)
            be = nbt["BlockEntities"][0]
            self.assertEqual(list(be["Pos"]), [3, 1, 0])
            self.assertEqual(str(be["Text1"]), '{"text":"Hello WorldEdit"}')

    def test_t08_entities_armor_stand_and_item_frame(self):
        """T08 (BUG-03 & RISK-02): Entities preserve offset coordinates, TileX/Y/Z, strip UUID, and handle String Id."""
        reg = Region(0, 0, 0, -4, 3, -4)
        armor_stand = Entity("minecraft:armor_stand")
        armor_stand.position = (-2.5, 1.0, -1.5)
        armor_stand.data["UUID"] = List[Int]([Int(1), Int(2), Int(3), Int(4)])

        item_frame = Entity("custommod:fancy_frame")
        item_frame.position = (-1.0, 2.0, -3.0)
        item_frame.data["TileX"] = Int(-1)
        item_frame.data["TileY"] = Int(2)
        item_frame.data["TileZ"] = Int(-3)

        reg.entities.append(armor_stand)
        reg.entities.append(item_frame)
        schem = reg.as_schematic(name="EntityTest")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t08.litematic")
            out_path = os.path.join(tmpdir, "t08.schem")
            schem.save(in_path)

            # Explicitly test BUG-03 branch where 'id' is absent from e.data when converter processes the entity
            orig_load = Schematic.load

            def _load_without_nbt_id(path):
                loaded = orig_load(path)
                first_reg = list(loaded.regions.values())[0]
                del first_reg.entities[0].data["id"]
                return loaded

            with patch.object(Schematic, "load", side_effect=_load_without_nbt_id):
                ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            self.assertEqual(len(nbt["Entities"]), 2)
            ent_as = nbt["Entities"][0]
            self.assertEqual(str(ent_as["Id"]), "minecraft:armor_stand")
            self.assertNotIn("id", ent_as)
            self.assertNotIn("UUID", ent_as)
            self.assertAlmostEqual(float(ent_as["Pos"][0]), 0.5)
            self.assertAlmostEqual(float(ent_as["Pos"][1]), 1.0)
            self.assertAlmostEqual(float(ent_as["Pos"][2]), 1.5)

            ent_if = nbt["Entities"][1]
            self.assertEqual(str(ent_if["Id"]), "custommod:fancy_frame")
            self.assertEqual(int(ent_if["TileX"]), 2)
            self.assertEqual(int(ent_if["TileY"]), 2)
            self.assertEqual(int(ent_if["TileZ"]), 0)

    def test_t09_overlapping_regions_policies(self):
        """T09 (BUG-01): Overlapping regions obey overwrite, keep-first, error policies and non-air preservation."""
        r1 = Region(0, 0, 0, 2, 1, 1)
        r1[0, 0, 0] = BlockState("minecraft:chest")
        r1[1, 0, 0] = BlockState("minecraft:gold_block")
        r1.tile_entities.append(
            TileEntity(Compound({"id": String("minecraft:chest"), "x": Int(0), "y": Int(0), "z": Int(0)}))
        )

        r2 = Region(0, 0, 0, 2, 1, 1)
        r2[0, 0, 0] = BlockState("minecraft:stone")

        schem = Schematic(name="OverlapTest", regions={"R1": r1, "R2": r2})

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t09.litematic")
            out_overwrite = os.path.join(tmpdir, "t09_overwrite.schem")
            out_keep = os.path.join(tmpdir, "t09_keep.schem")
            out_err = os.path.join(tmpdir, "t09_err.schem")
            schem.save(in_path)

            ok1, log1 = _run_quiet(litematic_to_schem_final, in_path, out_overwrite, on_overlap="overwrite")
            self.assertTrue(ok1)
            self.assertIn("Detected 1 overlapping non-air block(s)", log1)
            nbt1 = File.load(out_overwrite, gzipped=True)
            blocks1 = _read_schem_blocks(nbt1)
            self.assertEqual(blocks1[(0, 0, 0)], "minecraft:stone")
            self.assertEqual(blocks1[(1, 0, 0)], "minecraft:gold_block")
            self.assertEqual(len(nbt1["BlockEntities"]), 0)

            ok2, _ = _run_quiet(litematic_to_schem_final, in_path, out_keep, on_overlap="keep-first")
            self.assertTrue(ok2)
            nbt2 = File.load(out_keep, gzipped=True)
            blocks2 = _read_schem_blocks(nbt2)
            self.assertEqual(blocks2[(0, 0, 0)], "minecraft:chest")
            self.assertEqual(len(nbt2["BlockEntities"]), 1)

            ok3, _ = _run_quiet(litematic_to_schem_final, in_path, out_err, on_overlap="error")
            self.assertFalse(ok3)
            self.assertFalse(os.path.exists(out_err))

    def test_t10_missing_corrupted_or_empty_files(self):
        """T10 (BUG-05): Missing, corrupted, or region-less files fail gracefully with descriptive errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = os.path.join(tmpdir, "does_not_exist.litematic")
            out_path = os.path.join(tmpdir, "out.schem")
            ok_missing, log_missing = _run_quiet(litematic_to_schem_final, missing_path, out_path)
            self.assertFalse(ok_missing)
            self.assertIn("not found", log_missing)

            corrupt_path = os.path.join(tmpdir, "corrupt.litematic")
            with open(corrupt_path, "wb") as f:
                f.write(b"not a valid gzip or nbt file")
            ok_corrupt, log_corrupt = _run_quiet(litematic_to_schem_final, corrupt_path, out_path)
            self.assertFalse(ok_corrupt)
            self.assertIn("Failed to read valid Litematica data", log_corrupt)

            empty_reg_path = os.path.join(tmpdir, "empty_regions.litematic")
            empty_nbt = Compound({
                "Version": Int(5),
                "SubVersion": Int(1),
                "MinecraftDataVersion": Int(2586),
                "Metadata": Compound({
                    "EnclosingSize": Compound({"x": Int(0), "y": Int(0), "z": Int(0)}),
                    "Author": String("Test"),
                    "Description": String(""),
                    "Name": String("Empty"),
                    "RegionCount": Int(0),
                    "TimeCreated": Int(0),
                    "TimeModified": Int(0),
                    "TotalBlocks": Int(0),
                    "TotalVolume": Int(0),
                }),
                "Regions": Compound({}),
            })
            File(empty_nbt, gzipped=True).save(empty_reg_path)
            ok_empty, log_empty = _run_quiet(litematic_to_schem_final, empty_reg_path, out_path)
            self.assertFalse(ok_empty)
            self.assertIn("does not contain any regions", log_empty)

    def test_t11_large_palette_varint_encoding(self):
        """T11 (RISK-03): Palettes with > 128 states encode multi-byte LEB128 VarInts into signed ByteArray cleanly."""
        reg = Region(0, 0, 0, 200, 1, 1)
        for i in range(200):
            reg[i, 0, 0] = BlockState(f"custommod:block_{i}")
        schem = reg.as_schematic(name="LargePalette")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t11.litematic")
            out_path = os.path.join(tmpdir, "t11.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            self.assertEqual(int(nbt["PaletteMax"]), 200)
            blocks = _read_schem_blocks(nbt)
            for i in range(200):
                self.assertEqual(blocks[(i, 0, 0)], f"custommod:block_{i}")

    def test_t12_minecraft_data_version_preservation(self):
        """T12 (BUG-04): Input MinecraftDataVersion is dynamically preserved in the output Sponge V2 NBT."""
        reg = Region(0, 0, 0, 1, 1, 1)
        reg[0, 0, 0] = BlockState("minecraft:crafter")
        schem = reg.as_schematic(name="ModernVersion", mc_version=3953)

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t12.litematic")
            out_path = os.path.join(tmpdir, "t12.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            self.assertEqual(int(nbt["DataVersion"]), 3953)

    def test_t13_pending_ticks_and_dimension_limits(self):
        """T13 (RISK-04 & RISK-05): Medium volume converts rapidly, pending ticks emit notice, and >32767 is rejected."""
        reg = Region(0, 0, 0, 16, 16, 16)
        reg[0, 0, 0] = BlockState("minecraft:repeater")
        reg.block_ticks.append(Compound({"x": Int(0), "y": Int(0), "z": Int(0), "t": Int(4), "p": Int(0)}))
        reg.fluid_ticks.append(Compound({"x": Int(1), "y": Int(0), "z": Int(0), "t": Int(5), "p": Int(0)}))
        schem = reg.as_schematic(name="TicksAndVolume")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t13.litematic")
            out_path = os.path.join(tmpdir, "t13.schem")
            schem.save(in_path)

            ok, output_log = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)
            self.assertIn("Skipped 1 pending block tick(s) and 1 pending fluid tick(s)", output_log)

            # Verify Short dimension overflow protection (> 32767)
            r_far = Region(40000, 0, 0, 1, 1, 1)
            oversized = Schematic(name="Oversized", regions={"Origin": Region(0, 0, 0, 1, 1, 1), "Far": r_far})
            over_in = os.path.join(tmpdir, "oversized.litematic")
            over_out = os.path.join(tmpdir, "oversized.schem")
            oversized.save(over_in)
            ok_over, log_over = _run_quiet(litematic_to_schem_final, over_in, over_out)
            self.assertFalse(ok_over)
            self.assertIn("exceed Sponge V2 Short limit", log_over)

    def test_t14_air_only_structure(self):
        """T14: Structure containing only minecraft:air produces a valid Sponge V2 schematic."""
        reg = Region(0, 0, 0, 3, 3, 3)
        schem = reg.as_schematic(name="AirOnly")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "t14.litematic")
            out_path = os.path.join(tmpdir, "t14.schem")
            schem.save(in_path)

            ok, _ = _run_quiet(litematic_to_schem_final, in_path, out_path)
            self.assertTrue(ok)

            nbt = File.load(out_path, gzipped=True)
            self.assertEqual(int(nbt["PaletteMax"]), 1)
            self.assertIn("minecraft:air", nbt["Palette"])
            blocks = _read_schem_blocks(nbt)
            self.assertEqual(len(blocks), 27)
            self.assertTrue(all(v == "minecraft:air" for v in blocks.values()))


if __name__ == "__main__":
    unittest.main()
