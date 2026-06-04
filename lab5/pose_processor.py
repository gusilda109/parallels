#!/usr/bin/env python3

import cv2
import argparse
import time
from collections import OrderedDict
from queue import Queue, Empty
from threading import Thread, Lock
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from ultralytics import YOLO


class VideoCapture:
    
    def __init__(self, source: str):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {source}")
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        return self.cap.read()
    
    def __del__(self):
        if self.cap is not None:
            self.cap.release()


class VideoWriter:
    
    def __init__(self, output_path: str, width: int, height: int, fps: float):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not self.writer.isOpened():
            raise RuntimeError(f"Cannot create video writer for: {output_path}")
    
    def write(self, frame: np.ndarray):
        self.writer.write(frame)
    
    def __del__(self):
        if self.writer is not None:
            self.writer.release()


class YOLOProcessor:
    
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


class FrameBuffer:
    
    def __init__(self, max_size: int = 30):
        self.queue = Queue(maxsize=max_size)
        self.lock = Lock()
    
    def put(self, item, block=True, timeout=None):
        self.queue.put(item, block=block, timeout=timeout)
    
    def get(self, block=True, timeout=None):
        return self.queue.get(block=block, timeout=timeout)
    
    def empty(self):
        return self.queue.empty()
    
    def qsize(self):
        return self.queue.qsize()


class SingleThreadProcessor:
    
    def __init__(self, video_path: str, output_path: str):
        self.video_path = video_path
        self.output_path = output_path
    
    def process(self) -> float:
        
        print("[*] Loading video...")
        video_reader = VideoCapture(self.video_path)
        
        print(f"[*] Video info: {video_reader.width}x{video_reader.height}, "
              f"FPS: {video_reader.fps:.2f}, Frames: {video_reader.total_frames}")
        
        print("[*] Loading YOLO model...")
        processor = YOLOProcessor()
        
        print("[*] Creating output video...")
        video_writer = VideoWriter(
            self.output_path,
            video_reader.width,
            video_reader.height,
            video_reader.fps
        )
        
        print("[*] Starting single-threaded processing...")
        start_time = time.time()
        
        frame_count = 0
        while True:
            ret, frame = video_reader.read()
            if not ret:
                break
            
            processed_frame = processor.predict(frame)
            video_writer.write(processed_frame)
            
            frame_count += 1
            if frame_count % 10 == 0:
                print(f"  Processed {frame_count} frames...")
        
        elapsed_time = time.time() - start_time
        
        print(f"\n[✓] Single-threaded processing completed!")
        print(f"[✓] Total frames: {frame_count}")
        print(f"[✓] Time elapsed: {elapsed_time:.2f} seconds")
        print(f"[✓] FPS: {frame_count / elapsed_time:.2f}")
        
        return elapsed_time


class MultiThreadProcessor:
    
    def __init__(self, video_path: str, output_path: str, num_threads: int = 4):
        self.video_path = video_path
        self.output_path = output_path
        self.num_threads = num_threads
        self.input_buffer = FrameBuffer(max_size=30)
        self.output_buffer = OrderedDict()
        self.output_lock = Lock()
    
    def reader_thread(self, video_reader: VideoCapture):
        frame_idx = 0
        while True:
            ret, frame = video_reader.read()
            if not ret:
                for _ in range(self.num_threads):
                    self.input_buffer.put((None, None))
                break
            
            self.input_buffer.put((frame_idx, frame))
            frame_idx += 1
    
    def worker_thread(self, processor: YOLOProcessor):
        while True:
            try:
                frame_idx, frame = self.input_buffer.get(timeout=1)
            except Empty:
                continue
            
            if frame is None:
                break
            
            processed_frame = processor.predict(frame)
            
            with self.output_lock:
                self.output_buffer[frame_idx] = processed_frame
    
    def process(self) -> float:
        
        print("[*] Loading video...")
        video_reader = VideoCapture(self.video_path)
        
        print(f"[*] Video info: {video_reader.width}x{video_reader.height}, "
              f"FPS: {video_reader.fps:.2f}, Frames: {video_reader.total_frames}")
        
        print(f"[*] Loading YOLO model (num_threads={self.num_threads})...")
        processors = [YOLOProcessor() for _ in range(self.num_threads)]
        
        print("[*] Creating output video...")
        video_writer = VideoWriter(
            self.output_path,
            video_reader.width,
            video_reader.height,
            video_reader.fps
        )
        
        print(f"[*] Starting {self.num_threads}-threaded processing...")
        start_time = time.time()
        
        reader = Thread(target=self.reader_thread, args=(video_reader,), daemon=True)
        reader.start()
        
        workers = [
            Thread(target=self.worker_thread, args=(processors[i],), daemon=True)
            for i in range(self.num_threads)
        ]
        for worker in workers:
            worker.start()
        
        written_frames = 0
        next_frame_to_write = 0
        
        while written_frames < video_reader.total_frames:
            with self.output_lock:
                while next_frame_to_write in self.output_buffer:
                    frame = self.output_buffer.pop(next_frame_to_write)
                    video_writer.write(frame)
                    written_frames += 1
                    next_frame_to_write += 1
                    
                    if written_frames % 10 == 0:
                        print(f"  Written {written_frames} frames...")
            
            time.sleep(0.001)
        
        reader.join(timeout=5)
        for worker in workers:
            worker.join(timeout=5)
        
        elapsed_time = time.time() - start_time
        
        print(f"\n[✓] Multi-threaded processing completed!")
        print(f"[✓] Total frames: {written_frames}")
        print(f"[✓] Time elapsed: {elapsed_time:.2f} seconds")
        print(f"[✓] FPS: {written_frames / elapsed_time:.2f}")
        
        return elapsed_time


def main():
    parser = argparse.ArgumentParser(
        description="Process video with YOLOv8 Pose (single/multi-threaded)"
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="Path to input video file (640x480 recommended)"
    )
    parser.add_argument(
        "-m", "--mode",
        type=str,
        default="multi",
        choices=["single", "multi"],
        help="Processing mode: single-threaded or multi-threaded (default: multi)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output.mp4",
        help="Output video filename (default: output.mp4)"
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=4,
        help="Number of threads for multi-threaded mode (default: 4)"
    )
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"[!] Error: Input file not found: {args.input}")
        return
    
    print("=" * 60)
    print(f"YOLOv8 Pose Video Processor - {args.mode.upper()} mode")
    print("=" * 60)
    
    if args.mode == "single":
        processor = SingleThreadProcessor(args.input, args.output)
        elapsed_time = processor.process()
    else:
        processor = MultiThreadProcessor(args.input, args.output, args.threads)
        elapsed_time = processor.process()
    
    print("=" * 60)
    print(f"Output saved to: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
