"""Quick test script to validate Detection service with sample videos.

Usage:
    python scripts/test_detection.py --dir "video samples" --endpoint http://localhost:8001/detect

It will:
1. Iterate over each video file in the directory.
2. Grab one frame every `--stride` frames (default 30).
3. Send the frame to the /detect endpoint.
4. Print detection summary.

Requires: requests, opencv-python.
"""

import argparse
import base64
import json
import os
from pathlib import Path

import cv2
import requests


def parse_args():
    p = argparse.ArgumentParser(description="Test Detection service with sample videos")
    p.add_argument("--dir", default="video samples", help="Directory containing sample videos")
    p.add_argument("--endpoint", default="http://localhost:8001/detect", help="Detection endpoint URL")
    p.add_argument("--stride", type=int, default=30, help="Send every N-th frame")
    return p.parse_args()


def main():
    args = parse_args()
    sample_dir = Path(args.dir)
    if not sample_dir.exists():
        raise SystemExit(f"Directory {sample_dir} not found")

    video_files = list(sample_dir.glob("*.mp4")) + list(sample_dir.glob("*.avi"))
    if not video_files:
        raise SystemExit("No video files found in sample directory")

    print(f"Found {len(video_files)} videos to test")

    for vf in video_files:
        cap = cv2.VideoCapture(str(vf))
        if not cap.isOpened():
            print(f"Cannot open {vf}")
            continue
        frame_idx = 0
        print(f"\nProcessing {vf.name}")
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % args.stride == 0:
                _, buf = cv2.imencode(".jpg", frame)
                resp = requests.post(
                    args.endpoint,
                    files={"file": ("frame.jpg", buf.tobytes(), "image/jpeg")},
                    timeout=60,
                )
                if resp.status_code == 200:
                    detections = resp.json().get("detections", [])
                    print(f"Frame {frame_idx}: {len(detections)} objects detected")
                else:
                    print(f"Frame {frame_idx}: request failed {resp.status_code} - {resp.text}")
            frame_idx += 1
        cap.release()
    print("Testing complete.")


if __name__ == "__main__":
    main()
