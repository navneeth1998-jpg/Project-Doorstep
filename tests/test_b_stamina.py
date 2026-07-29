"""Test B: stamina test. Runs the check/remember/compare logic repeatedly
across 100 validation images to confirm the CODE survives running many times
in a row without crashing, leaking, or corrupting the saved state file.

These 100 images are not a real chronological sequence, so the
arrived/picked-up/no-change outputs are NOT meaningful detections of real
events — this test only cares whether the code runs cleanly, cycle after
cycle.
"""

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so monitor_check.py (project root) is importable

import cv2
from ultralytics import YOLO

from monitor_check import MODEL_PATH, CHECK_INTERVAL_SECONDS, check_once, reset_state

# Note: CHECK_INTERVAL_SECONDS now reads monitor_check.py's live production value (30s),
# not the temporary 1.5s used for the original stamina test run — re-running this as-is
# will take ~50 minutes, not ~3 minutes, unless that constant is temporarily lowered again.

VALID_IMAGES_DIR = Path("training images/Combined package images.v1/valid/images")
SELECTION_FILE = Path("stamina_test_selection.txt")
OUTPUT_DIR = Path("test_images/stamina_test_output")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reset_state()

    selected_filenames = SELECTION_FILE.read_text().splitlines()
    model = YOLO(MODEL_PATH)

    cycles_attempted = 0
    cycles_completed = 0
    errors = []
    change_events = 0
    images_saved = 0

    for i, filename in enumerate(selected_filenames, start=1):
        cycles_attempted += 1
        image_path = VALID_IMAGES_DIR / filename

        try:
            previous_count, current_count, event, result = check_once(model, image_path)
            cycles_completed += 1

            print(f"Cycle {i:03d}: {filename} -> previous={previous_count}, current={current_count}, event='{event}'")

            if event != "no change":
                change_events += 1
                annotated = result.plot()
                out_name = f"cycle_{i:03d}_{event.replace(' ', '_')}.jpg"
                cv2.imwrite(str(OUTPUT_DIR / out_name), annotated)
                images_saved += 1

        except Exception as e:
            errors.append((i, filename, str(e)))
            print(f"Cycle {i:03d}: {filename} -> ERROR: {e}")
            traceback.print_exc()

        time.sleep(CHECK_INTERVAL_SECONDS)

    print("\n--- Test B summary ---")
    print(f"Total cycles attempted: {cycles_attempted}")
    print(f"Total cycles completed successfully: {cycles_completed}")
    print(f"Total errors: {len(errors)}")
    for i, filename, err in errors:
        print(f"  Cycle {i}: {filename} -> {err}")
    print(f"Total change events detected: {change_events}")
    print(f"Total images saved to {OUTPUT_DIR}: {images_saved}")


if __name__ == "__main__":
    main()
