#!/usr/bin/env python3

import cv2
import argparse
import time
from queue import Queue, Empty
from threading import Thread, Lock, Event
from typing import Tuple, Optional
import numpy as np
from ultralytics import YOLO


class CameraCapture:
    
    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480):
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {camera_id}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        return self.cap.read()
    
    def __del__(self):
        if self.cap is not None:
            self.cap.release()


class YOLOModel:
    
    def __init__(self, model_name: str = "yolov8s-pose", device: str = "cpu"):
        self.model = YOLO(model_name)
        self.device = device
    
    def predict(self, frame: np.ndarray) -> np.ndarray:
        results = self.model(frame, device=self.device, verbose=False)
        
        if results[0].keypoints is not None:
            annotated_frame = results[0].plot()
        else:
            annotated_frame = frame.copy()
        
        return annotated_frame
    
    def __del__(self):
        pass


class RealtimeVideoProcessor:
    
    def __init__(self, camera_id: int = 0, num_threads: int = 2):
        self.camera_id = camera_id
        self.num_threads = num_threads
        
        self.input_queue = Queue(maxsize=2)
        self.output_queue = Queue(maxsize=2)
        
        self.stop_event = Event()
        
        self.frame_count = 0
        self.stats_lock = Lock()
        self.last_time = time.time()
        self.fps_counter = 0
    
    def reader_thread(self, camera: CameraCapture):
        while not self.stop_event.is_set():
            ret, frame = camera.read()
            if not ret:
                break
            
            try:
                self.input_queue.put((time.time(), frame), block=False)
            except:
                pass
    
    def worker_thread(self, model: YOLOModel):
        while not self.stop_event.is_set():
            try:
                timestamp, frame = self.input_queue.get(timeout=1)
            except Empty:
                continue
            
            processed_frame = model.predict(frame)
            
            try:
                self.output_queue.put((timestamp, processed_frame), block=False)
            except:
                pass
    
    def display_thread(self):
        while not self.stop_event.is_set():
            try:
                timestamp, frame = self.output_queue.get(timeout=1)
            except Empty:
                continue
            
            with self.stats_lock:
                self.frame_count += 1
                current_time = time.time()
                time_diff = current_time - self.last_time
                
                if time_diff >= 1.0:
                    fps = self.frame_count / time_diff
                    self.fps_counter = fps
                    self.frame_count = 0
                    self.last_time = current_time
            
            fps_text = f"FPS: {self.fps_counter:.1f} | Threads: {self.num_threads}"
            cv2.putText(
                frame,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            
            cv2.imshow("YOLOv8 Pose - Real-time Processing", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                self.stop_event.set()
                break
    
    def run(self):
        print("=" * 60)
        print(f"YOLOv8 Pose - Real-time Camera Processing")
        print(f"Threads: {self.num_threads}")
        print("Press ESC or Q to quit")
        print("=" * 60)
        
        try:
            print("[*] Loading camera...")
            camera = CameraCapture(self.camera_id)
            print(f"[*] Camera info: {camera.width}x{camera.height}, FPS: {camera.fps:.2f}")
            
            print("[*] Loading YOLO model...")
            model = YOLOModel()
            
            print(f"[*] Starting {self.num_threads}-threaded processing...")
            
            reader = Thread(target=self.reader_thread, args=(camera,), daemon=True)
            reader.start()
            
            workers = [
                Thread(target=self.worker_thread, args=(model,), daemon=True)
                for _ in range(self.num_threads)
            ]
            for worker in workers:
                worker.start()
            
            self.display_thread()
            
            self.stop_event.set()
            reader.join(timeout=2)
            for worker in workers:
                worker.join(timeout=2)
        
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")
        
        except Exception as e:
            print(f"[!] Error: {e}")
        
        finally:
            cv2.destroyAllWindows()
            print("[✓] Camera processor stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Real-time pose detection from camera using YOLOv8"
    )
    parser.add_argument(
        "-c", "--camera",
        type=int,
        default=0,
        help="Camera ID (default: 0)"
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=2,
        help="Number of processing threads (default: 2)"
    )
    
    args = parser.parse_args()
    
    processor = RealtimeVideoProcessor(args.camera, args.threads)
    processor.run()


if __name__ == "__main__":
    main()
