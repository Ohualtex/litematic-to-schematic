import os
import sys
import argparse
from .converter import litematic_to_schem_final, VALID_OVERLAP_POLICIES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Converts Litematica files (.litematic) directly to WorldEdit Sponge V2 Schematic (.schem) format."
    )
    parser.add_argument("input", help="Path to the input .litematic file")
    parser.add_argument("-o", "--output", help="Optional: Custom output .schem file path", default=None)
    parser.add_argument(
        "--on-overlap",
        choices=VALID_OVERLAP_POLICIES,
        default="overwrite",
        help="Conflict resolution policy when multiple regions overlap with non-air blocks (default: overwrite)",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_file = args.input

    if args.output:
        output_file = args.output
    else:
        # Strip extension and append .schem
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.schem"

    success = litematic_to_schem_final(input_file, output_file, on_overlap=args.on_overlap)
    if not success:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    main()
