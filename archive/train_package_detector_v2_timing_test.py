"""Quick 1-epoch timing test with optimized settings, to measure real
per-epoch speed before committing to the full training run."""

from pathlib import Path

from ultralytics import YOLO

DATA_YAML = Path("training images/Combined package images.v1/data.yaml").resolve()


def main():
    model = YOLO("yolov8n.pt")
    model.train(
        data=str(DATA_YAML),
        epochs=1,
        imgsz=512,
        batch=32,
        workers=8,
        device="cpu",
        project="training images/runs",
        name="timing_test",
    )


if __name__ == "__main__":
    main()
