"""Run YOLOv8 nano on a sequence of doormat photos, count confident detections
in each, and compare consecutive photos to report arrival events."""

from pathlib import Path

from ultralytics import YOLO

MODEL_PATH = "training images/models/package_v2_best.pt"
CONFIDENCE_THRESHOLD = 0.5

TEST_IMAGES_DIR = Path("test_images")
PHOTO_SEQUENCE = [
    "doorstep_zero items.jpeg",
    "doorstep_one item.jpeg",
    "doorstep_two items.jpeg",
]


def count_confident_detections(model, image_path):
    results = model(str(image_path), conf=CONFIDENCE_THRESHOLD, verbose=False)
    return len(results[0].boxes)


def compare_counts(previous_count, current_count):
    if current_count > previous_count:
        if previous_count == 0:
            return "arrived"
        return "arrived again"
    if current_count < previous_count:
        return "picked up"
    return "no change"


def main():
    model = YOLO(MODEL_PATH)

    counts = []
    for filename in PHOTO_SEQUENCE:
        image_path = TEST_IMAGES_DIR / filename
        count = count_confident_detections(model, image_path)
        counts.append(count)
        print(f"{filename}: {count} object(s) above {CONFIDENCE_THRESHOLD} confidence")

    print()
    for i in range(1, len(counts)):
        result = compare_counts(counts[i - 1], counts[i])
        print(f"{PHOTO_SEQUENCE[i-1]} -> {PHOTO_SEQUENCE[i]}: {result}")


if __name__ == "__main__":
    main()
