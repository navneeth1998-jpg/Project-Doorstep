"""Run the fine-tuned package detector against every validation image and save
the model's raw output (boxes, confidence, label) with no manual overrides."""

from pathlib import Path

from ultralytics import YOLO

MODEL_PATH = Path("runs/detect/training images/runs/package_detector/weights/best.pt")
VALID_IMAGES_DIR = Path("training images/Doormat Detector.v1i.yolov8/valid/images")
OUTPUT_DIR = Path("training images/validation_results")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(MODEL_PATH))

    image_paths = sorted(VALID_IMAGES_DIR.glob("*.jpg")) + sorted(VALID_IMAGES_DIR.glob("*.jpeg"))

    for i, image_path in enumerate(image_paths, start=1):
        results = model(str(image_path))
        annotated_frame = results[0].plot()

        output_filename = f"result_{i:03d}_{image_path.stem}.jpg"
        output_path = OUTPUT_DIR / output_filename

        import cv2
        cv2.imwrite(str(output_path), annotated_frame)

        num_detections = len(results[0].boxes)
        if num_detections == 0:
            print(f"{output_filename}: no detections")
        else:
            details = ", ".join(
                f"{results[0].names[int(box.cls[0])]} ({float(box.conf[0]):.2f})"
                for box in results[0].boxes
            )
            print(f"{output_filename}: {num_detections} detection(s) — {details}")

    print(f"\nSaved {len(image_paths)} annotated validation images to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
