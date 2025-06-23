#!/usr/bin/env python3
"""
Local orchestration manager for batch plot generation
Manages parallel execution with resource monitoring and progress tracking
"""

import subprocess
import yaml
import json
import time
import threading
import psutil
import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class LocalOrchestrator:
    def __init__(self, config_file, max_parallel=2, resource_monitoring=True, 
                 r_script_path=None, working_dir=None):
        """
        Initialize the local orchestrator
        
        Args:
            config_file: Path to orchestration config YAML file
            max_parallel: Maximum number of parallel R processes
            resource_monitoring: Enable system resource monitoring
            r_script_path: Path to batch_plot_generator.R script
            working_dir: Working directory for R script execution
        """
        self.config_file = Path(config_file)
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
            
        self.config = yaml.safe_load(self.config_file.read_text())
        self.max_parallel = max_parallel
        self.resource_monitoring = resource_monitoring
        self.results = []
        self._stop_monitoring = False
        
        # Set up paths
        self.r_script_path = Path(r_script_path) if r_script_path else Path("/Users/cristina/wiley/Documents/jheem/code/jheem2_interactive/batch_plot_generator.R")
        self.working_dir = Path(working_dir) if working_dir else Path("/Users/cristina/wiley/Documents/jheem/code/jheem2_interactive")
        
        # Validate paths
        if not self.r_script_path.exists():
            raise FileNotFoundError(f"R script not found: {self.r_script_path}")
        if not self.working_dir.exists():
            raise FileNotFoundError(f"Working directory not found: {self.working_dir}")
            
        print(f"🔧 Orchestrator initialized:")
        print(f"   Config: {self.config_file}")
        print(f"   R Script: {self.r_script_path}")
        print(f"   Working Dir: {self.working_dir}")
        print(f"   Max Parallel: {self.max_parallel}")
        
    def execute_job(self, job):
        """Execute a single batch job"""
        start_time = time.time()
        city = job["city"]
        
        print(f"🏙️  Starting job for city {city}")
        
        # Build command arguments
        cmd = [
            "Rscript", 
            str(self.r_script_path),
            "--city", city,
            "--scenarios", ",".join(job["scenarios"]),
            "--outcomes", ",".join(job["outcomes"]),
            "--statistics", ",".join(job["statistics"]),
            "--facets", ",".join(job["facets"]),
            "--upload-s3",
            "--register-db", 
            "--api-gateway-id", "ogavekpfi5",
            "--skip-existing"
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.working_dir,
                capture_output=True, 
                text=True, 
                timeout=7200  # 2 hour timeout per job
            )
            
            duration = time.time() - start_time
            
            return {
                "job": job,
                "city": city,
                "success": result.returncode == 0,
                "duration": duration,
                "expected_plots": job["expected_plots"],
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "job": job,
                "city": city,
                "success": False,
                "duration": time.time() - start_time,
                "expected_plots": job["expected_plots"],
                "error": "Job timeout (2 hours)",
                "return_code": -1
            }
        except Exception as e:
            return {
                "job": job,
                "city": city,
                "success": False,
                "duration": time.time() - start_time,
                "expected_plots": job["expected_plots"],
                "error": str(e),
                "return_code": -1
            }
    
    def monitor_resources(self):
        """Monitor system resources during execution"""
        print("📊 Starting resource monitoring...")
        
        while not self._stop_monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                if cpu_percent > 90:
                    print(f"⚠️  High CPU usage: {cpu_percent:.1f}%")
                if memory.percent > 85:
                    print(f"⚠️  High memory usage: {memory.percent:.1f}%")
                    
                # Log resource usage every 5 minutes
                if int(time.time()) % 300 == 0:
                    print(f"📊 Resources: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"⚠️  Resource monitoring error: {e}")
                time.sleep(60)  # Back off on errors
    
    def run_orchestration(self):
        """Execute all jobs with parallel processing and monitoring"""
        
        # Get jobs from config
        jobs = self.config.get("jobs", [])
        if not jobs:
            print("❌ No jobs found in configuration")
            return
            
        total_expected_plots = sum(job.get("expected_plots", 0) for job in jobs)
        
        print(f"🚀 Starting orchestration:")
        print(f"   📋 Jobs: {len(jobs)}")
        print(f"   📊 Expected plots: {total_expected_plots:,}")
        print(f"   ⚡ Max parallel: {self.max_parallel}")
        print(f"   ⏱️  Estimated time: {self.config.get('estimated_parallel_hours', 'unknown')} hours")
        print()
        
        # Start resource monitoring
        if self.resource_monitoring:
            monitor_thread = threading.Thread(target=self.monitor_resources, daemon=True)
            monitor_thread.start()
        
        start_time = time.time()
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            # Submit all jobs
            future_to_job = {
                executor.submit(self.execute_job, job): job 
                for job in jobs
            }
            
            # Process completed jobs
            for future in as_completed(future_to_job):
                result = future.result()
                self.results.append(result)
                completed += 1
                
                status = "✅" if result["success"] else "❌"
                duration_min = result["duration"] / 60
                city = result["city"]
                expected = result["expected_plots"]
                
                print(f"{status} [{completed:2d}/{len(jobs)}] {city} "
                      f"({expected:3d} plots, {duration_min:5.1f}m)")
                
                if not result["success"]:
                    error_msg = result.get("error", "Unknown error")
                    print(f"     💥 Error: {error_msg}")
                    if result.get("return_code", 0) != 0:
                        print(f"     📄 Exit code: {result['return_code']}")
                    
                    # Show stderr if available and not too long
                    stderr = result.get("stderr", "")
                    if stderr and len(stderr) < 500:
                        print(f"     📄 stderr: {stderr.strip()}")
                        
                # Show progress estimate
                if completed < len(jobs):
                    elapsed_hours = (time.time() - start_time) / 3600
                    if completed > 0:
                        avg_time_per_job = elapsed_hours / completed
                        remaining_jobs = len(jobs) - completed
                        estimated_remaining = remaining_jobs * avg_time_per_job
                        print(f"     ⏳ Estimated remaining: {estimated_remaining:.1f} hours")
        
        # Stop monitoring
        self._stop_monitoring = True
        
        # Final summary
        total_duration = time.time() - start_time
        successful = sum(1 for r in self.results if r["success"])
        total_expected_plots = sum(r["expected_plots"] for r in self.results)
        successful_plots = sum(r["expected_plots"] for r in self.results if r["success"])
        
        print(f"\n🎯 Orchestration Complete!")
        print(f"   ⏱️  Total time: {total_duration/3600:.2f} hours")
        print(f"   ✅ Successful jobs: {successful}/{len(jobs)}")
        print(f"   ❌ Failed jobs: {len(jobs) - successful}")
        print(f"   📊 Expected plots generated: {successful_plots:,}/{total_expected_plots:,}")
        
        if successful > 0:
            avg_time_per_job = total_duration / len(jobs)
            avg_time_per_plot = total_duration / successful_plots if successful_plots > 0 else 0
            print(f"   ⚡ Average time per job: {avg_time_per_job/60:.1f} minutes")
            print(f"   ⚡ Average time per plot: {avg_time_per_plot:.2f} seconds")
            
            # Extrapolate to full scale
            if avg_time_per_plot > 0:
                estimated_64k_hours = (64512 * avg_time_per_plot) / 3600
                print(f"   🔮 Estimated time for 64K plots: {estimated_64k_hours:.1f} hours")
        
        # Save detailed results
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        results_file = results_dir / f"orchestration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            "orchestration_summary": {
                "config_file": str(self.config_file),
                "config_type": self.config.get("config_type", "unknown"),
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_duration_hours": total_duration/3600,
                "total_jobs": len(jobs),
                "successful_jobs": successful,
                "failed_jobs": len(jobs) - successful,
                "total_expected_plots": total_expected_plots,
                "successful_plots": successful_plots,
                "average_time_per_plot": avg_time_per_plot if successful_plots > 0 else None,
                "max_parallel": self.max_parallel
            },
            "job_results": self.results
        }
        
        with open(results_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)
            
        print(f"   📄 Detailed results: {results_file}")
        
        return successful == len(jobs)

def main():
    parser = argparse.ArgumentParser(description="Local orchestration manager for JHEEM plot generation")
    parser.add_argument("config", help="Path to orchestration config YAML file")
    parser.add_argument("--max-parallel", type=int, default=2, 
                       help="Maximum parallel R processes (default: 2)")
    parser.add_argument("--no-monitoring", action="store_true", 
                       help="Disable resource monitoring")
    parser.add_argument("--r-script", 
                       help="Path to batch_plot_generator.R script")
    parser.add_argument("--working-dir", 
                       help="Working directory for R script execution")
    
    args = parser.parse_args()
    
    try:
        orchestrator = LocalOrchestrator(
            config_file=args.config,
            max_parallel=args.max_parallel,
            resource_monitoring=not args.no_monitoring,
            r_script_path=args.r_script,
            working_dir=args.working_dir
        )
        
        success = orchestrator.run_orchestration()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Orchestration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
