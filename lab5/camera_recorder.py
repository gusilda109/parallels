#!/usr/bin/env python3

import cv2
import argparse
import time
from pathlib import Path


class CameraRecorder:
    
    def __init__(self, output_path: str, width: int = 640, height: int = 480, fps: int = 30):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        print(f"[*] Camera resolution: {actual_width}x{actual_height}")
        print(f"[*] Camera FPS: {actual_fps:.2f}")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(output_path, fourcc, actual_fps, (actual_width, actual_height))
        
        if not self.writer.isOpened():
            raise RuntimeError(f"Cannot create video writer for {output_path}")
        
        print(f"[*] Recording to: {output_path}")
    
    def record(self, duration: int = 10):
        print(f"[*] Recording for {duration} seconds...")
        print("[*] Press SPACE to stop early, or wait for auto-stop")
        
        frame_count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            
            text = f"Recording... {elapsed}/{duration}s"
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (0, 255, 0), 2)
            
            self.writer.write(frame)
            
            cv2.imshow("Recording Preview (Press SPACE to stop)", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                print("\n[*] Recording stopped by user")
                break
            
            frame_count += 1
        
        print(f"[✓] Recorded {frame_count} frames")
        return frame_count
    
    def __del__(self):
        if self.cap is not None:
            self.cap.release()
        if self.writer is not None:
            self.writer.release()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Record video from webcam for YOLOv8 testing"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="test_video.mp4",
        help="Output video filename (default: test_video.mp4)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=10,
        help="Recording duration in seconds (default: 10)"
    )
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=640,
        help="Video width (default: 640)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Video height (default: 480)"
    )
    parser.add_argument(
        "-f", "--fps",
        type=int,
        default=30,
        help="Video FPS (default: 30)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Camera Recorder for YOLOv8 Testing")
    print("=" * 60)
    
    try:
        if Path(args.output).exists():
            response = input(f"\nFile {args.output} already exists. Overwrite? (y/n): ")
            if response.lower() != 'y':
                print("[!] Cancelled")
                return
        
        recorder = CameraRecorder(args.output, args.width, args.height, args.fps)
        frame_count = recorder.record(args.duration)
        
        print("\n" + "=" * 60)
        print(f"[✓] Video saved: {args.output}")
        print(f"[✓] Total frames: {frame_count}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n[!] Recording cancelled by user")
    
    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    main()
