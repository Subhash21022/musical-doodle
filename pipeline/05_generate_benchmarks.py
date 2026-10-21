"""
Pipeline Step 5: Generate Research Performance Benchmarks
Computes aggregated condition benchmarks across altitude tiers, air density brackets,
pitch soil types, dew factor, and weather conditions.
Outputs: data/processed/condition_benchmark_summary.csv and specialized tables.
"""

import os
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def main():
    matches_csv = os.path.join(PROCESSED_DIR, "matches_enriched.csv")
    parquet_path = os.path.join(PROCESSED_DIR, "deliveries_enriched.parquet")
    
    if not os.path.exists(matches_csv):
        raise FileNotFoundError(f"Missing {matches_csv}. Run pipeline first.")
        
    df_matches = pd.read_csv(matches_csv)
    logging.info(f"Loaded {len(df_matches)} matches for benchmark synthesis.")

    # 1. Air Density & Altitude Benchmark
    def air_density_tier(rho):
        if rho < 1.05:
            return "1. Low Air Density (< 1.05 kg/m3 - High Altitude)"
        elif rho < 1.12:
            return "2. Moderate Air Density (1.05 - 1.12 kg/m3)"
        elif rho < 1.18:
            return "3. High Air Density (1.12 - 1.18 kg/m3 - Coastal/Sea Level)"
        else:
            return "4. Extreme Dense Air (> 1.18 kg/m3 - Cold/High Pressure)"

    df_matches["air_density_tier"] = df_matches["air_density_kg_m3"].apply(air_density_tier)

    # 2. Dew Risk Tier
    def dew_tier(d):
        if d < 0.25:
            return "Low Dew Risk (< 0.25)"
        elif d < 0.60:
            return "Moderate Dew Risk (0.25 - 0.60)"
        else:
            return "High Dew Risk (>= 0.60)"

    df_matches["dew_tier"] = df_matches["dew_index"].apply(dew_tier)

    # Chasing Team Won Flag
    df_matches["chasing_won"] = (df_matches["match_winner"] == df_matches["innings2_team"]).astype(int)

    # Groupby Air Density
    density_bench = df_matches.groupby("air_density_tier").agg(
        matches=("match_id", "count"),
        avg_elevation_m=("elevation_m", "mean"),
        avg_first_innings_score=("innings1_runs", "mean"),
        avg_sixes_per_match=("match_total_sixes", "mean"),
        avg_fours_per_match=("match_total_fours", "mean"),
        avg_run_rate=("innings1_run_rate", "mean")
    ).reset_index()

    # Groupby Dew Tier
    dew_bench = df_matches.groupby("dew_tier").agg(
        matches=("match_id", "count"),
        chasing_win_pct=("chasing_won", lambda x: round(x.mean() * 100.0, 1)),
        avg_inn1_runs=("innings1_runs", "mean"),
        avg_inn2_runs=("innings2_runs", "mean"),
        avg_inn1_rr=("innings1_run_rate", "mean"),
        avg_inn2_rr=("innings2_run_rate", "mean")
    ).reset_index()

    # Groupby Pitch Soil Type
    soil_bench = df_matches.groupby("pitch_soil_type").filter(lambda g: len(g) >= 15).groupby("pitch_soil_type").agg(
        matches=("match_id", "count"),
        avg_inn1_score=("innings1_runs", "mean"),
        avg_inn1_wickets=("innings1_wickets", "mean"),
        avg_run_rate=("innings1_run_rate", "mean"),
        avg_sixes_per_match=("match_total_sixes", "mean")
    ).reset_index()

    # Save summary tables
    summary_csv = os.path.join(PROCESSED_DIR, "condition_benchmark_summary.csv")
    density_csv = os.path.join(PROCESSED_DIR, "benchmark_air_density_altitude.csv")
    dew_csv = os.path.join(PROCESSED_DIR, "benchmark_dew_effect.csv")
    soil_csv = os.path.join(PROCESSED_DIR, "benchmark_pitch_soil.csv")

    density_bench.to_csv(density_csv, index=False)
    dew_bench.to_csv(dew_csv, index=False)
    soil_bench.to_csv(soil_csv, index=False)
    
    # Combined summary
    density_bench["benchmark_category"] = "Air Density & Altitude"
    dew_bench["benchmark_category"] = "Dew & Innings Effect"
    soil_bench["benchmark_category"] = "Pitch Soil Composition"
    
    # Write a comprehensive master benchmark report
    with open(summary_csv, "w", encoding="utf-8") as f:
        f.write("# CRICKET PITCH AND WEATHER PERFORMANCE BENCHMARK SUMMARY\n\n")
        f.write("### 1. Air Density & Altitude Benchmark (Six-Hitting & Scoring)\n")
        f.write(density_bench.to_csv(index=False))
        f.write("\n### 2. Dew Effect Benchmark (Chasing Advantage & Innings Run Rates)\n")
        f.write(dew_bench.to_csv(index=False))
        f.write("\n### 3. Pitch Soil Composition Benchmark\n")
        f.write(soil_bench.to_csv(index=False))
        
    logging.info(f"Successfully generated condition benchmarks at: {summary_csv}")
    logging.info(f"Air Density Benchmark:\n{density_bench}")
    logging.info(f"Dew Benchmark:\n{dew_bench}")

if __name__ == "__main__":
    main()
