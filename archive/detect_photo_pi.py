"""Take one photo from the Raspberry Pi camera (CSI), run YOLOv8 nano detection,
save the result, and log the test to session-log.md. Pi-specific version of
detect_photo.py — same detection/logging logic, different camera capture method."""

import time
from datetime import datetime
from pathlib import Path

import cv2
from picamera2 import Picamera2
from ultralytics import YOLO

OUTPUT_DIR = Path("test_images")
SESSION_LOG_PATH = Path("session-log.md")
MODEL_PATH = "training images/models/package_v2_best.pt"

# Starting confidence threshold, based on the v2 model's validation-set confidence
# distribution (median 93.3%, 94.5% of images above 0.5). Not yet confirmed against
# real Pi camera photos — may need adjustment once tested with actual doorstep images.
CONFIDENCE_THRESHOLD = 0.5


def capture_photo():
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()
    time.sleep(1)  # let auto-exposure/auto-white-balance settle before capturing

    frame_rgb = picam2.capture_array()
    picam2.stop()
    picam2.close()

    # picamera2 gives RGB frames; OpenCV/YOLO expect BGR
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    return frame_bgr


def format_detections(result):
    if len(result.boxes) == 0:
        return "no objects detected"

    lines = []
    for box in result.boxes:
        label = result.names[int(box.cls[0])]
        confidence = float(box.conf[0])
        lines.append(f"{label} ({confidence:.2f})")
    return ", ".join(lines)


def log_test(timestamp, filename, scene_description, detections_summary, inference_seconds):
    entry = (
        f"\n### {timestamp} — Test capture (Pi camera)\n"
        f"- File: `test_images/{filename}`\n"
        f"- Scene: {scene_description}\n"
        f"- Detections: {detections_summary}\n"
        f"- Inference time: {inference_seconds:.2f}s\n"
    )
    with SESSION_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    frame = capture_photo()

    model = YOLO(MODEL_PATH)

    start_time = time.time()
    results = model(frame, conf=CONFIDENCE_THRESHOLD)
    inference_seconds = time.time() - start_time

    annotated_frame = results[0].plot()

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
    filename = f"detection_pi_{timestamp}.jpg"
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        raise RuntimeError(
            f"Refusing to overwrite existing file: {output_path}. "
            "This shouldn't happen with second-level timestamps — wait a second and try again."
        )

    cv2.imwrite(str(output_path), annotated_frame)

    print(f"Saved detection result to {output_path}")
    print(f"Inference time: {inference_seconds:.2f} seconds")

    detections_summary = format_detections(results[0])
    scene_description = input("Briefly describe what was in the test scene: ").strip()
    if not scene_description:
        scene_description = "(not provided)"

    log_test(now.strftime("%Y-%m-%d %H:%M"), filename, scene_description, detections_summary, inference_seconds)
    print("Logged this test run to session-log.md")


if __name__ == "__main__":
    main()
