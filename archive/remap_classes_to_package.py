"""Remap every class in the combined package dataset's label files to a single
unified class ID (0 = "package"). Box coordinates are left untouched."""

from pathlib import Path

DATASET_DIR = Path("training images/Combined package images.v1")
UNIFIED_CLASS_ID = "0"


def remap_label_file(label_path):
    lines = label_path.read_text().splitlines()
    new_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        parts[0] = UNIFIED_CLASS_ID
        new_lines.append(" ".join(parts))
    label_path.write_text("\n".join(new_lines) + "\n" if new_lines else "")


def main():
    total_files = 0
    for split in ["train", "valid"]:
        labels_dir = DATASET_DIR / split / "labels"
        label_files = list(labels_dir.glob("*.txt"))
        for label_file in label_files:
            remap_label_file(label_file)
        print(f"{split}: remapped {len(label_files)} label files")
        total_files += len(label_files)

    print(f"\nTotal label files remapped: {total_files}")


if __name__ == "__main__":
    main()
