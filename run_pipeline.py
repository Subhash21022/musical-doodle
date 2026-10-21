"""
Master Pipeline Orchestrator: Cricket Pitch and Weather Performance Benchmark
Executes data extraction, venue cataloging, weather physics enrichment,
ball-by-ball processing, and benchmark generation.
"""

import os
import sys
import argparse
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

STEPS = [
    ("Step 1: Download & Extract Raw Match Data", "pipeline/01_fetch_raw_data.py"),
    ("Step 2: Build Venue & Ground Master Catalog", "pipeline/02_build_venues_catalog.py"),
    ("Step 3: Atmospheric Physics & Weather Enrichment", "pipeline/03_enrich_weather.py"),
    ("Step 4: Generate Ball-by-Ball Linked Dataset", "pipeline/04_build_deliveries.py"),
    ("Step 5: Generate Performance Benchmarks", "pipeline/05_generate_benchmarks.py"),
]

def run_step(desc: str, script_path: str, extra_args: list = None):
    full_path = os.path.join(BASE_DIR, script_path)
    cmd = [sys.executable, full_path]
    if extra_args:
        cmd.extend(extra_args)
        
    logging.info(f"\n{'='*70}\nSTARTING: {desc}\nCommand: {' '.join(cmd)}\n{'='*70}")
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        logging.error(f"FAILURE in {desc} (Exit code {res.returncode})")
        sys.exit(res.returncode)
    logging.info(f"COMPLETED: {desc}\n")

def main():
    parser = argparse.ArgumentParser(description="Cricket Pitch & Weather Performance Benchmark Pipeline")
    parser.add_argument("--all", action="store_true", help="Run entire pipeline end-to-end")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4, 5], help="Run a specific step (1-5)")
    parser.add_argument("--max-matches", type=int, default=None, help="Limit number of matches for deliveries step")
    args = parser.parse_args()

    if args.step:
        step_idx = args.step - 1
        desc, script = STEPS[step_idx]
        extra = []
        if args.step == 4 and args.max_matches:
            extra = ["--max-matches", str(args.max_matches)]
        run_step(desc, script, extra)
    else:
        # Default or --all: run all steps
        for idx, (desc, script) in enumerate(STEPS):
            extra = []
            if idx == 3 and args.max_matches:
                extra = ["--max-matches", str(args.max_matches)]
            run_step(desc, script, extra)

    logging.info("All pipeline processes completed successfully!")

if __name__ == "__main__":
    main()
