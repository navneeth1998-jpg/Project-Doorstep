"""Run the v2 fine-tuned package detector against every validation image and
save the model's raw output (boxes, confidence, label) with no manual overrides."""

from pathlib import Path

import cv2
from ultralytics import YOLO

MODEL_PATH = Path("training images/models/package_v2_best.pt")
VALID_IMAGES_DIR = Path("training images/Combined package images.v1/valid/images")
OUTPUT_DIR = Path("training images/validation_results_v2")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(MODEL_PATH))

    image_paths = sorted(VALID_IMAGES_DIR.glob("*.jpg")) + sorted(VALID_IMAGES_DIR.glob("*.jpeg")) + sorted(VALID_IMAGES_DIR.glob("*.png"))

    all_confidences = []
    zero_detection_count = 0

    for i, image_path in enumerate(image_paths, start=1):
        results = model(str(image_path), conf=0.001, verbose=False)
        annotated_frame = results[0].plot()

        output_filename = f"result_{i:04d}_{image_path.stem}.jpg"
        output_path = OUTPUT_DIR / output_filename
        cv2.imwrite(str(output_path), annotated_frame)

        num_detections = len(results[0].boxes)
        if num_detections == 0:
            zero_detection_count += 1
        else:
            for box in results[0].boxes:
                all_confidences.append(float(box.conf[0]))

        if i % 200 == 0:
            print(f"Processed {i}/{len(image_paths)}...")

    print(f"\nProcessed {len(image_paths)} validation images")
    print(f"Images with zero detections (even at near-0 confidence threshold): {zero_detection_count}")
    if all_confidences:
        all_confidences.sort()
        n = len(all_confidences)
        print(f"Total detections across all images: {n}")
        print(f"Min confidence: {min(all_confidences):.3f}")
        print(f"Max confidence: {max(all_confidences):.3f}")
        print(f"Median confidence: {all_confidences[n // 2]:.3f}")
        print(f"Mean confidence: {sum(all_confidences) / n:.3f}")
        above_25 = sum(1 for c in all_confidences if c >= 0.25)
        above_50 = sum(1 for c in all_confidences if c >= 0.50)
        print(f"Detections >= 0.25 confidence: {above_25} ({100*above_25/n:.1f}%)")
        print(f"Detections >= 0.50 confidence: {above_50} ({100*above_50/n:.1f}%)")


if __name__ == "__main__":
    main()
