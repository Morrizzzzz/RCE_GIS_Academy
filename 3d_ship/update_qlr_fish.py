from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

DEFAULT_TEMPLATE_FISH = "Baars"


def update_qlr_text(text: str, source_fish: str, target_fish: str) -> str:
    """Update the QLR XML so style + labeling point to a different fish field.

    This intentionally only changes the pieces that drive:
    - the grouped layer name
    - rule-based renderer filters
    - label field names

    It does NOT blindly replace every occurrence of the source fish name,
    because fields like `Baars_pos` or `pivot_bun2_Baars` may exist and should
    not be renamed unless the layer schema also changes.
    """

    updated = text

    # 1) Rename the inner grouped layer name, e.g. <layer-tree-group name="Baars" ...>
    updated = re.sub(
        rf'(<layer-tree-group\b[^>]*\bname=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
        count=1,
    )

    # 2) Update rule filters like &quot;Baars&quot; = 0 and &quot;Baars&quot;!= 0.
    updated = re.sub(
        rf'(&quot;){re.escape(source_fish)}(&quot;\s*[!=<>])',
        rf'\1{target_fish}\2',
        updated,
    )

    # Also handle possible spaces before operators or different comparison styles.
    updated = re.sub(
        rf'(&quot;){re.escape(source_fish)}(&quot;\s*=)',
        rf'\1{target_fish}\2',
        updated,
    )

    # 3) Update label field attribute, e.g. fieldName="Baars"
    updated = re.sub(
        rf'(fieldName=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
    )

    # 4) Update any exact field references in XML attributes such as <field name="Baars" ...>
    # Only exact matches are changed; Baars_pos / pivot_bun2_Baars stay untouched.
    updated = re.sub(
        rf'(<field\b[^>]*\bname=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
    )

    updated = re.sub(
        rf'(<alias\b[^>]*\bfield=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
    )

    updated = re.sub(
        rf'(<policy\b[^>]*\bfield=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
    )

    updated = re.sub(
        rf'(<default\b[^>]*\bfield=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
    )

    updated = re.sub(
        rf'(<constraint\b[^>]*\bfield=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
    )

    updated = re.sub(
        rf'(<column\b[^>]*\bname=")({re.escape(source_fish)})(")',
        rf"\1{target_fish}\3",
        updated,
    )

    if updated == text:
        raise ValueError(
            f"No changes were made. Check whether the template fish '{source_fish}' exists in the QLR."
        )

    return updated


def build_output_name(template_path: Path, fish: str) -> str:
    template_stem = template_path.stem
    if DEFAULT_TEMPLATE_FISH.lower() in template_stem.lower():
        return re.sub(
            DEFAULT_TEMPLATE_FISH,
            fish,
            template_stem,
            flags=re.IGNORECASE,
        ) + template_path.suffix
    return f"{template_stem}_{fish}{template_path.suffix}"


def generate_qlrs(
    template_path: Path,
    fishes: Iterable[str],
    output_dir: Path,
    source_fish: str,
) -> list[Path]:
    text = template_path.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for fish in fishes:
        fish = fish.strip()
        if not fish:
            continue
        updated = update_qlr_text(text, source_fish=source_fish, target_fish=fish)
        output_path = output_dir / build_output_name(template_path, fish)
        output_path.write_text(updated, encoding="utf-8")
        written.append(output_path)
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create fish-specific QLR files from a template QLR."
    )
    parser.add_argument(
        "template",
        type=Path,
        help="Path to the template .qlr file, for example Baars.qlr",
    )
    parser.add_argument(
        "--fish",
        nargs="+",
        required=True,
        help='One or more fish names, for example --fish Haring Baars Spiering',
    )
    parser.add_argument(
        "--source-fish",
        default=DEFAULT_TEMPLATE_FISH,
        help=f"Fish field used in the template QLR (default: {DEFAULT_TEMPLATE_FISH})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated_qlr"),
        help="Directory where the new QLR files will be written",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written = generate_qlrs(
        template_path=args.template,
        fishes=args.fish,
        output_dir=args.output_dir,
        source_fish=args.source_fish,
    )
    print("Created:")
    for path in written:
        print(f" - {path}")


if __name__ == "__main__":
    main()
