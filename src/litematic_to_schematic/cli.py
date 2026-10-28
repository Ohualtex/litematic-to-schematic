import os
import argparse
from .converter import litematic_to_schem_final


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Converts Litematica files (.litematic) directly to WorldEdit Sponge V2 Schematic (.schem) format."
    )
    parser.add_argument("input", help="Path to the input .litematic file")
    parser.add_argument("-o", "--output", help="Optional: Custom output .schem file path", default=None)
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_file = args.input

    if args.output:
        output_file = args.output
    else:
        # Strip extension and append .schem
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.schem"

    litematic_to_schem_final(input_file, output_file)


if __name__ == "__main__":
    main()

