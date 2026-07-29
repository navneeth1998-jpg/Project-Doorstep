"""Take one photo from the webcam, run YOLOv8 nano detection, save the result,
and log the test to session-log.md."""

from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

OUTPUT_DIR = Path("test_images")
SESSION_LOG_PATH = Path("session-log.md")


def capture_photo():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open the webcam. Check that it's connected and not in use by another app.")

    success, frame = camera.read()
    camera.release()

    if not success:
        raise RuntimeError("Webcam opened but failed to capture a frame.")

    return frame


def format_detections(result):
    if len(result.boxes) == 0:
        return "no objects detected"

    lines = []
    for box in result.boxes:
        label = result.names[int(box.cls[0])]
        confidence = float(box.conf[0])
        lines.append(f"{label} ({confidence:.2f})")
    return ", ".join(lines)


def log_test(timestamp, filename, scene_description, detections_summary):
    entry = (
        f"\n### {timestamp} — Test capture\n"
        f"- File: `test_images/{filename}`\n"
        f"- Scene: {scene_description}\n"
        f"- Detections: {detections_summary}\n"
    )
    with SESSION_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    frame = capture_photo()

    model = YOLO("yolov8n.pt")
    results = model(frame)

    annotated_frame = results[0].plot()

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
    filename = f"detection_{timestamp}.jpg"
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        raise RuntimeError(
            f"Refusing to overwrite existing file: {output_path}. "
            "This shouldn't happen with second-level timestamps — wait a second and try again."
        )

    cv2.imwrite(str(output_path), annotated_frame)

    print(f"Saved detection result to {output_path}")

    detections_summary = format_detections(results[0])
    scene_description = input("Briefly describe what was in the test scene: ").strip()
    if not scene_description:
        scene_description = "(not provided)"

    log_test(now.strftime("%Y-%m-%d %H:%M"), filename, scene_description, detections_summary)
    print("Logged this test run to session-log.md")


if __name__ == "__main__":
    main()
