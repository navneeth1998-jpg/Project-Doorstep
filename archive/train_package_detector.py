"""Fine-tune YOLOv8 nano on the doormat package dataset."""

from pathlib import Path

from ultralytics import YOLO

DATA_YAML = Path("training images/Doormat Detector.v1i.yolov8/data.yaml").resolve()


def main():
    model = YOLO("yolov8n.pt")
    model.train(
        data=str(DATA_YAML),
        epochs=100,
        patience=20,
        imgsz=640,
        project="training images/runs",
        name="package_detector",
    )


if __name__ == "__main__":
    main()
