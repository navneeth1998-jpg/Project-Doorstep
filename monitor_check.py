"""Core check/remember/compare logic for continuous package monitoring.

Takes a photo, runs the fine-tuned detector, compares the detected count to
the last saved count (persisted in a small JSON state file), and reports what
changed using the arrived/arrived-again/picked-up/no-change logic. This is
the reusable unit a future always-on Pi loop will call repeatedly.

No notification sending happens here — that is a separate, future step.
"""

import json
from pathlib import Path

from ultralytics import YOLO

from telegram_notify import send_photo

MODEL_PATH = "training images/models/package_v2_best.pt"
CONFIDENCE_THRESHOLD = 0.5
STATE_FILE = Path("package_state.json")

# Time to wait between checks in a real continuous monitoring loop.
CHECK_INTERVAL_SECONDS = 30


def load_last_count():
    if not STATE_FILE.exists():
        return None
    data = json.loads(STATE_FILE.read_text())
    return data.get("last_count")


def save_last_count(count):
    STATE_FILE.write_text(json.dumps({"last_count": count}))


def reset_state():
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def count_confident_detections(model, image_path):
    results = model(str(image_path), conf=CONFIDENCE_THRESHOLD, verbose=False)
    return len(results[0].boxes), results[0]


def compare_counts(previous_count, current_count):
    if previous_count is None:
        return "no change"  # first-ever check, nothing to compare against yet
    if current_count > previous_count:
        if previous_count == 0:
            return "arrived"
        return "arrived again"
    if current_count < previous_count:
        return "picked up"
    return "no change"


EVENT_MESSAGES = {
    "arrived": "A package has arrived at your doorstep.",
    "arrived again": "Another package has arrived — there are now {current_count} packages at your doorstep.",
    "picked up": "A package was picked up — {current_count} package(s) remaining at your doorstep.",
}


def notify_if_real_event(event, current_count, image_path):
    if event not in EVENT_MESSAGES:
        return  # "no change" (or any unrecognized event) never sends a message
    caption = EVENT_MESSAGES[event].format(current_count=current_count)
    send_photo(image_path, caption)


def check_once(model, image_path):
    """Run one check cycle: detect, compare to saved state, update saved state,
    and send a Telegram notification (photo + caption) if a real event occurred."""
    previous_count = load_last_count()
    current_count, result = count_confident_detections(model, image_path)
    event = compare_counts(previous_count, current_count)
    save_last_count(current_count)
    notify_if_real_event(event, current_count, image_path)
    return previous_count, current_count, event, result
