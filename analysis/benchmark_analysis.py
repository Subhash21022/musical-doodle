"""
Research Analysis & Scientific Benchmark Study
Performs statistical hypothesis testing, econometric regressions, and visualizations on:
1. Aerodynamic Air Density & Boundary Dimensions vs. Six-Hitting
2. Dew Factor & Pitch Moisture vs. 2nd Innings Spin Bowling Degradation
3. Pitch Soil Composition vs. Scoring Efficiency & Wickets
"""

import os
import logging
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")

def main():
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    matches_csv = os.path.join(PROCESSED_DIR, "matches_enriched.csv")
    parquet_path = os.path.join(PROCESSED_DIR, "deliveries_enriched.parquet")
    
    df_matches = pd.read_csv(matches_csv)
    logging.info(f"Loaded {len(df_matches)} matches for statistical modeling.")

    # -------------------------------------------------------------
    # 1. REGRESSION: Six-Hitting vs Air Density & Boundary Dimensions
    # -------------------------------------------------------------
    # Filter for full matches with at least 15 overs per innings
    clean_m = df_matches[(df_matches["innings1_overs"] >= 15) & (df_matches["innings2_overs"] >= 10)].copy()
    
    # Compute Sixes Per Over
    clean_m["total_overs"] = clean_m["innings1_overs"] + clean_m["innings2_overs"]
    clean_m["sixes_per_over"] = clean_m["match_total_sixes"] / clean_m["total_overs"]
    
    # Correlation analysis
    corr_density, p_density = stats.pearsonr(clean_m["air_density_kg_m3"], clean_m["sixes_per_over"])
    corr_bound, p_bound = stats.pearsonr(clean_m["boundary_avg_m"], clean_m["sixes_per_over"])
    
    print("\n" + "="*70)
    print("HYPOTHESIS 1: AERODYNAMIC AIR DENSITY & BOUNDARY SIZE VS SIX-HITTING")
    print("="*70)
    print(f"Sample size: {len(clean_m)} matches")
    print(f"Correlation between Air Density (kg/m3) and Sixes/Over: r = {corr_density:.4f} (p = {p_density:.4e})")
    print(f"Correlation between Average Boundary Distance (m) and Sixes/Over: r = {corr_bound:.4f} (p = {p_bound:.4e})")

    # -------------------------------------------------------------
    # 2. DEW FACTOR & INNINGS ASYMMETRY BENCHMARK
    # -------------------------------------------------------------
    print("\n" + "="*70)
    print("HYPOTHESIS 2: DEW FORMATION RISK VS INNINGS ASYMMETRY")
    print("="*70)
    
    high_dew = clean_m[clean_m["dew_index"] >= 0.50]
    low_dew = clean_m[clean_m["dew_index"] < 0.20]
    
    chase_win_high = (high_dew["match_winner"] == high_dew["innings2_team"]).mean() * 100.0
    chase_win_low = (low_dew["match_winner"] == low_dew["innings2_team"]).mean() * 100.0
    
    # Run rate gap (Inn 2 RR - Inn 1 RR)
    rr_gap_high = (high_dew["innings2_run_rate"] - high_dew["innings1_run_rate"]).mean()
    rr_gap_low = (low_dew["innings2_run_rate"] - low_dew["innings1_run_rate"]).mean()
    
    t_stat_dew, p_val_dew = stats.ttest_ind(
        high_dew["innings2_run_rate"] - high_dew["innings1_run_rate"],
        low_dew["innings2_run_rate"] - low_dew["innings1_run_rate"],
        equal_var=False
    )
    
    print(f"High Dew (index >= 0.50, N={len(high_dew)}):")
    print(f"  Chasing Team Win %: {chase_win_high:.1f}%")
    print(f"  Avg Innings 2 vs 1 Run Rate Delta: {rr_gap_high:+.2f} RPO")
    print(f"Low Dew (index < 0.20, N={len(low_dew)}):")
    print(f"  Chasing Team Win %: {chase_win_low:.1f}%")
    print(f"  Avg Innings 2 vs 1 Run Rate Delta: {rr_gap_low:+.2f} RPO")
    print(f"Two-sample t-test on Run Rate Delta: t = {t_stat_dew:.3f}, p = {p_val_dew:.4e}")

    # -------------------------------------------------------------
    # 3. BALL-BY-BALL: SPIN VS PACE UNDER DEW & SOIL
    # -------------------------------------------------------------
    print("\n" + "="*70)
    print("HYPOTHESIS 3: BOWLER STYLE (SPIN VS PACE) UNDER DEW & SOIL")
    print("="*70)
    
    # Read sample or chunk of parquet
    import pyarrow.parquet as pq
    table = pq.read_table(parquet_path, columns=[
        "match_id", "innings", "phase", "bowler_type", "runs_total", "is_dot", "is_wicket",
        "dew_index", "pitch_soil_type", "elevation_m", "air_density_kg_m3"
    ])
    df_deliv = table.to_pandas()
    
    # Calculate bowler economy and dot % by bowling type and innings
    bowler_perf = df_deliv.groupby(["bowler_type", "innings"]).agg(
        deliveries=("runs_total", "count"),
        total_runs=("runs_total", "sum"),
        wickets=("is_wicket", "sum"),
        dots=("is_dot", "sum")
    ).reset_index()
    
    bowler_perf["overs"] = bowler_perf["deliveries"] / 6.0
    bowler_perf["economy_rate"] = round(bowler_perf["total_runs"] / bowler_perf["overs"], 2)
    bowler_perf["strike_rate"] = round(bowler_perf["deliveries"] / bowler_perf["wickets"], 1)
    bowler_perf["dot_pct"] = round((bowler_perf["dots"] / bowler_perf["deliveries"]) * 100.0, 1)
    
    print(bowler_perf[["bowler_type", "innings", "deliveries", "economy_rate", "strike_rate", "dot_pct"]].to_string(index=False))

    # -------------------------------------------------------------
    # 4. GENERATE RESEARCH VISUALIZATIONS
    # -------------------------------------------------------------
    sns.set_theme(style="whitegrid")
    
    # Plot 1: Air Density vs Six-Hitting
    plt.figure(figsize=(9, 5))
    top_venues = df_matches.groupby("venue_name").filter(lambda g: len(g) >= 20)
    venue_summary = top_venues.groupby(["venue_name", "elevation_m", "air_density_kg_m3", "boundary_avg_m"]).agg(
        avg_sixes=("match_total_sixes", "mean"),
        matches=("match_id", "count")
    ).reset_index()
    
    scatter = plt.scatter(
        venue_summary["air_density_kg_m3"],
        venue_summary["avg_sixes"],
        s=venue_summary["matches"] * 1.5,
        c=venue_summary["elevation_m"],
        cmap="viridis",
        alpha=0.8,
        edgecolors="black"
    )
    cbar = plt.colorbar(scatter)
    cbar.set_label("Venue Elevation (m above sea level)", fontsize=10)
    
    # Fit trendline
    z = np.polyfit(venue_summary["air_density_kg_m3"], venue_summary["avg_sixes"], 1)
    p = np.poly1d(z)
    x_vals = np.linspace(venue_summary["air_density_kg_m3"].min(), venue_summary["air_density_kg_m3"].max(), 50)
    plt.plot(x_vals, p(x_vals), "r--", linewidth=2, label="Trendline")
    
    plt.title("Air Density (Moist rho) vs. Six-Hitting Rate across Cricket Grounds", fontsize=12, fontweight="bold")
    plt.xlabel("Air Density (kg/m3) [Lower = Thinner Air at Altitude]", fontsize=10)
    plt.ylabel("Average Sixes per Match", fontsize=10)
    plt.legend()
    plt.tight_layout()
    fig1_path = os.path.join(ANALYSIS_DIR, "air_density_vs_sixes.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    
    # Plot 2: Pitch Soil Comparison
    plt.figure(figsize=(10, 6))
    soil_counts = df_matches["pitch_soil_type"].value_counts()
    valid_soils = soil_counts[soil_counts >= 30].index
    soil_data = df_matches[df_matches["pitch_soil_type"].isin(valid_soils)].copy()
    
    order = soil_data.groupby("pitch_soil_type")["innings1_runs"].median().sort_values(ascending=False).index
    sns.boxplot(data=soil_data, x="innings1_runs", y="pitch_soil_type", order=order, palette="Spectral")
    plt.title("Innings 1 Score Distribution by Pitch Soil Profile (min. 30 matches)", fontsize=12, fontweight="bold")
    plt.xlabel("1st Innings Total Runs", fontsize=10)
    plt.ylabel("Pitch Soil Composition", fontsize=10)
    plt.tight_layout()
    fig2_path = os.path.join(ANALYSIS_DIR, "pitch_soil_comparison.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()

    logging.info(f"Generated research visual artifacts:\n  - {fig1_path}\n  - {fig2_path}")

if __name__ == "__main__":
    main()
