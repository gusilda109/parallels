#!/usr/bin/env python3

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
import json
import matplotlib.pyplot as plt


class BenchmarkRunner:
    
    def __init__(self, video_path: str, output_dir: str = "benchmark_results"):
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        if not Path(video_path).exists():
            raise RuntimeError(f"Video file not found: {video_path}")
    
    def run_benchmark(self, num_threads: int) -> Tuple[float, str]:
        
        output_file = self.output_dir / f"output_threads_{num_threads}.mp4"
        
        cmd = [
            sys.executable, "pose_processor.py",
            "-i", self.video_path,
            "-m", "multi",
            "-t", str(num_threads),
            "-o", str(output_file)
        ]
        
        print(f"\n[*] Running benchmark with {num_threads} threads...")
        print(f"    Command: {' '.join(str(x) for x in cmd)}")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            elapsed_time = time.time() - start_time
            
            if result.returncode != 0:
                print(f"[!] Error running benchmark: {result.stderr}")
                return None, str(output_file)
            
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "Time elapsed:" in line:
                    time_str = line.split(':')[-1].strip().split()[0]
                    return float(time_str), str(output_file)
            
            return elapsed_time, str(output_file)
        
        except subprocess.TimeoutExpired:
            print(f"[!] Benchmark timeout after 300 seconds")
            return None, str(output_file)
        except Exception as e:
            print(f"[!] Error: {e}")
            return None, str(output_file)
    
    def run_all_benchmarks(self, thread_counts: List[int]) -> Dict[int, float]:
        results = {}
        
        print("=" * 60)
        print("YOLOv8 Pose Processor - Threading Benchmark")
        print("=" * 60)
        
        for num_threads in thread_counts:
            elapsed_time, output_file = self.run_benchmark(num_threads)
            if elapsed_time is not None:
                results[num_threads] = elapsed_time
                speedup = 1.0
                print(f"[✓] Threads: {num_threads:2d} | Time: {elapsed_time:7.2f}s | Output: {output_file}")
            else:
                print(f"[!] Threads: {num_threads:2d} | Failed")
        
        return results
    
    def analyze_results(self, results: Dict[int, float]) -> Dict:
        if not results:
            print("[!] No results to analyze")
            return {}
        
        sorted_results = sorted(results.items())
        
        min_threads = min(results.keys())
        baseline_time = results[min_threads]
        
        analysis = {}
        print("\n" + "=" * 60)
        print("Benchmark Analysis:")
        print("=" * 60)
        print(f"{'Threads':<10} {'Time (s)':<12} {'Speedup':<12} {'Efficiency':<12}")
        print("-" * 60)
        
        best_threads = None
        best_speedup = 0
        
        for num_threads, elapsed_time in sorted_results:
            speedup = baseline_time / elapsed_time
            efficiency = (speedup / num_threads) * 100
            
            analysis[num_threads] = {
                'time': elapsed_time,
                'speedup': speedup,
                'efficiency': efficiency
            }
            
            if speedup > best_speedup:
                best_speedup = speedup
                best_threads = num_threads
            
            print(f"{num_threads:<10} {elapsed_time:<12.2f} {speedup:<12.2f}x {efficiency:<12.1f}%")
        
        print("=" * 60)
        print(f"\n[✓] Best configuration: {best_threads} threads with {best_speedup:.2f}x speedup")
        print("=" * 60)
        
        return analysis
    
    def plot_results(self, results: Dict[int, float], output_file: str = "benchmark.png"):
        if not results:
            print("[!] No results to plot")
            return
        
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        sorted_items = sorted(results.items())
        threads = [x[0] for x in sorted_items]
        times = [x[1] for x in sorted_items]
        
        baseline_time = min(times)
        speedups = [baseline_time / t for t in times]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        ax1.plot(threads, times, 'b-o', linewidth=2, markersize=8)
        ax1.set_xlabel('Количество потоков', fontsize=12)
        ax1.set_ylabel('Время (секунды)', fontsize=12)
        ax1.set_title('Время обработки vs Количество потоков', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(threads)
        
        ax2.plot(threads, speedups, 'g-s', linewidth=2, markersize=8, label='Реальное ускорение')
        ax2.plot(threads, threads, 'r--', linewidth=1, label='Теоретический максимум')
        ax2.set_xlabel('Количество потоков', fontsize=12)
        ax2.set_ylabel('Ускорение', fontsize=12)
        ax2.set_title('Ускорение vs Количество потоков', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(threads)
        
        plt.tight_layout()
        output_path = self.output_dir / output_file
        plt.savefig(str(output_path), dpi=150)
        print(f"\n[✓] Benchmark plot saved to: {output_path}")
        plt.close()
    
    def save_results(self, results: Dict[int, float], analysis: Dict, 
                    output_file: str = "results.json"):
        data = {
            'results': results,
            'analysis': analysis
        }
        
        output_path = self.output_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[✓] Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark YOLOv8 Pose processor with different thread counts"
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="Path to input video file"
    )
    parser.add_argument(
        "-t", "--threads",
        type=str,
        default="1,2,4,8",
        help="Comma-separated thread counts to test (default: 1,2,4,8)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="benchmark_results",
        help="Output directory for results (default: benchmark_results)"
    )
    
    args = parser.parse_args()
    
    try:
        thread_counts = [int(x.strip()) for x in args.threads.split(',')]
    except ValueError:
        print("[!] Invalid thread counts format. Use comma-separated integers (e.g., 1,2,4,8)")
        return
    
    try:
        runner = BenchmarkRunner(args.input, args.output_dir)
        
        results = runner.run_all_benchmarks(thread_counts)
        
        if results:
            analysis = runner.analyze_results(results)
            runner.plot_results(results)
            runner.save_results(results, analysis)
    
    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    main()