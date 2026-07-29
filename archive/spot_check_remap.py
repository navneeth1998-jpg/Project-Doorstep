"""Draw the remapped 'package' bounding boxes onto a handful of sample images
so the remap can be visually spot-checked."""

from pathlib import Path

import cv2

DATASET_DIR = Path("training images/Combined package images.v1")
OUTPUT_DIR = Path("training images/spot_check")

# same 3 files used for the earlier before/after text comparison, plus 2 more at random
SAMPLE_LABEL_FILES = [
    ("train", "0db4658021970d63_jpg.rf.01464e64cadb75d06194443edbe0787c.txt"),
    ("train", "00d0c7964e5a3ec327fb1826_png_jpg.rf.8456ae9224778fd699a87ae6c5c94ee5.txt"),
    ("train", "-106_jpg.rf.af93641bce2a798f25eba4ee3d675b1d.txt"),
]


def find_image_for_label(split, label_stem):
    images_dir = DATASET_DIR / split / "images"
    for ext in [".jpg", ".jpeg", ".png"]:
        candidate = images_dir / f"{label_stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def draw_boxes(image_path, label_path, output_path):
    image = cv2.imread(str(image_path))
    height, width = image.shape[:2]

    for line in label_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        class_id, cx, cy, w, h = line.split()
        cx, cy, w, h = float(cx) * width, float(cy) * height, float(w) * width, float(h) * height
        x1, y1 = int(cx - w / 2), int(cy - h / 2)
        x2, y2 = int(cx + w / 2), int(cy + h / 2)

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(image, f"package (class {class_id})", (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imwrite(str(output_path), image)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    for split, label_filename in SAMPLE_LABEL_FILES:
        label_path = DATASET_DIR / split / "labels" / label_filename
        label_stem = Path(label_filename).stem
        image_path = find_image_for_label(split, label_stem)

        if image_path is None:
            print(f"Could not find matching image for {label_filename}")
            continue

        output_path = OUTPUT_DIR / f"spotcheck_{label_stem}.jpg"
        draw_boxes(image_path, label_path, output_path)
        print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
