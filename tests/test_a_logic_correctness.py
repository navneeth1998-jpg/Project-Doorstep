"""Test A: confirm the check/remember/compare logic still works correctly
in the new persistent-state setup, using the real known-good 3-photo
sequence (zero -> one -> two items, true chronological order)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so monitor_check.py (project root) is importable

from ultralytics import YOLO

from monitor_check import MODEL_PATH, check_once, reset_state

TEST_IMAGES_DIR = Path("test_images")
SEQUENCE = [
    "doorstep_zero items.jpeg",
    "doorstep_one item.jpeg",
    "doorstep_two items.jpeg",
]


def main():
    reset_state()  # start from a clean baseline, no leftover state from prior tests
    model = YOLO(MODEL_PATH)

    for filename in SEQUENCE:
        image_path = TEST_IMAGES_DIR / filename
        previous_count, current_count, event, _ = check_once(model, image_path)
        print(f"{filename}: previous={previous_count}, current={current_count}, event='{event}'")


if __name__ == "__main__":
    main()
