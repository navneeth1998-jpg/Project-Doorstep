"""Live continuous monitoring loop on the Pi: capture a photo from the Pi
camera, run the check/remember/compare logic (which sends a Telegram
notification automatically on a real event), then wait and repeat."""

import time
from datetime import datetime
from pathlib import Path

import cv2
from picamera2 import Picamera2
from ultralytics import YOLO

from monitor_check import MODEL_PATH, CHECK_INTERVAL_SECONDS, check_once, reset_state

OUTPUT_DIR = Path("test_images")
TOTAL_CYCLES = 5  # bounded run for this test (~2 minutes at 30s interval), not an infinite loop yet


def capture_photo(picam2):
    frame_rgb = picam2.capture_array()
    return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    reset_state()  # start from a clean baseline for this test run

    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()
    time.sleep(1)  # let auto-exposure/auto-white-balance settle

    model = YOLO(MODEL_PATH)

    print(f"Starting live monitor: {TOTAL_CYCLES} cycles, {CHECK_INTERVAL_SECONDS}s apart.")

    for cycle in range(1, TOTAL_CYCLES + 1):
        frame = capture_photo(picam2)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        photo_path = OUTPUT_DIR / f"live_loop_{timestamp}.jpg"
        cv2.imwrite(str(photo_path), frame)

        previous_count, current_count, event, _ = check_once(model, photo_path)
        print(f"Cycle {cycle}/{TOTAL_CYCLES} [{timestamp}]: previous={previous_count}, current={current_count}, event='{event}'")

        if cycle < TOTAL_CYCLES:
            time.sleep(CHECK_INTERVAL_SECONDS)

    picam2.stop()
    picam2.close()
    print("Live monitor test finished.")


if __name__ == "__main__":
    main()
