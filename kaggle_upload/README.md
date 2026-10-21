# 🏏 Cricket Pitch and Weather Performance Benchmark

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Matches Enriched](https://img.shields.io/badge/Matches-7%2C053-orange.svg)](data/processed/matches_enriched.csv)
[![Deliveries](https://img.shields.io/badge/Deliveries-1.6M+-green.svg)](data/processed/deliveries_enriched.parquet)

A research-grade benchmark dataset combining **pitch characteristics**, **ambient weather**, **venue altitude**, **boundary dimensions**, **tactical innings context**, and **1,607,744 ball-by-ball outcomes** across all Indian Premier League (IPL) seasons and Men's T20 Internationals (T20Is).

---

## 🎯 Motivation & Research Opportunity

Traditional cricket analytics datasets focus purely on match scores or basic delivery tracking (e.g., batsman runs and bowler wickets). However, cricket performance is heavily governed by environmental physics and playing conditions:

1. **Aerodynamics & Six-Hitting**: Venue altitude (e.g., Wanderers at $1,720\text{ m}$ vs. Wankhede at $14\text{ m}$) creates a $15-20\%$ variation in surface **moist air density** ($\rho$). Reduced air density directly lowers aerodynamic drag on struck balls, drastically impacting six-hitting frequency.
2. **Dew & Innings Asymmetry**: Evening humidity and radiation cooling lower the dew point depression ($\Delta T = T - T_{dew}$), saturating grass and cricket balls with dew, which critically alters spin grip, seam control, and 2nd innings bowling economy.
3. **Pitch Agronomy & Soil Mechanics**: Ground-level performance varies dramatically across soil types (**Red Soil** [high bounce, pace] vs. **Black Soil** [clay-swelling, gripping turn] vs. **Bulli/Drop-in turf**).

This dataset links **consistent venue-condition metadata with granular ball-by-ball deliveries**, providing sports science researchers, cricket boards, and performance analysts with an empirical foundation for conditional modeling.

---

## 📊 Dataset Architecture & Files

All processed datasets are available in `data/processed/`:

| File | Format | Rows | Description |
| :--- | :--- | :--- | :--- |
| **`venues_master.csv`** | CSV | 245 | Master catalog of stadiums with verified GPS coordinates, altitude ($m$), boundary dimensions (straight, square, avg in $m$), pitch soil composition, and bounce/pace tendencies. |
| **`matches_enriched.csv`** | CSV | 7,053 | Match-level records across IPL and T20Is enriched with hourly ambient weather (temp, humidity, pressure, dew point, wind, cloud cover), moist air density ($\rho$), dew risk score, and innings summaries. |
| **`deliveries_enriched.parquet`**| Parquet | 1,607,744 | Complete ball-by-ball dataset linked with venue geography, boundary distances, pitch soil, atmospheric variables, and bowler classification (`Pace` vs `Spin`). Compressed with Snappy. |
| **`deliveries_sample.csv`** | CSV | 5,000 | 5,000-row preview sample of the ball-by-ball dataset for quick tabular viewing. |
| **`condition_benchmark_summary.csv`** | CSV | Table | Aggregated benchmark metrics across altitude bands, air density tiers, dew risk categories, and pitch soil profiles. |

---

## 🧪 Scientific Benchmark Highlights

### 1. Air Density ($\rho$) & Altitude vs. Six-Hitting
- **Wanderers (South Africa, $1,720\text{ m}$)**: Air density $\rho \approx 0.975\text{ kg/m}^3$ (thinnest air in major cricket).
- **HPCA Dharamsala (India, $1,457\text{ m}$)**: Air density $\rho \approx 1.018\text{ kg/m}^3$.
- **Wankhede / Chepauk (Coastal, $<15\text{ m}$)**: Air density $\rho \approx 1.135 - 1.180\text{ kg/m}^3$.
- *Insight*: Reduced atmospheric density lowers aerodynamic drag ($F_D = \frac{1}{2}\rho v^2 C_D A$), providing measurable aerial carry advantage on lofted shots.

### 2. Pitch Soil Profile vs. 1st Innings Scoring
Empirical 1st innings scoring and sixes across soil types (min. 30 matches):
- **Dual Red & Black Soil Strips (Narendra Modi Stadium, Motera)**: Avg 1st Innings: **183.4 runs**, 15.5 sixes/match, Run Rate **9.18**.
- **Red Soil (Wankhede / Brabourne)**: Avg 1st Innings: **171.6 runs**, 13.3 sixes/match, Run Rate **8.63**.
- **Clay / Sand Sub-base (M. Chinnaswamy Stadium)**: Avg 1st Innings: **170.1 runs**, 14.6 sixes/match, Run Rate **8.84**.
- **Tropical / Laterite Clay (Bayuemas / Kigali)**: Avg 1st Innings: **114 - 122 runs**, Run Rate **5.96 - 6.38**.

### 3. Bowler Style (Spin vs. Pace) Across Innings
Analyzing 1.6M+ deliveries:
- **Pace Bowlers**: Innings 1 Economy **8.13** vs. Innings 2 Economy **7.97** (Dot %: 36.3% vs. 38.2%).
- **Spin Bowlers**: Innings 1 Economy **7.51** vs. Innings 2 Economy **7.36** (Strike Rate improves from 20.4 to 18.3 balls/wicket).

---

## 🚀 Quickstart & Pipeline Execution

### Prerequisites
```bash
pip install pandas pyarrow scipy matplotlib seaborn requests
```

### Reproduce the End-to-End Pipeline
```bash
# Run all steps end-to-end
python run_pipeline.py --all

# Or run individual steps:
python run_pipeline.py --step 1   # Fetch & extract raw Cricsheet data
python run_pipeline.py --step 2   # Build Venue Master database
python run_pipeline.py --step 3   # Enrich matches with Open-Meteo weather & air density
python run_pipeline.py --step 4   # Extract ball-by-ball deliveries to Parquet
python run_pipeline.py --step 5   # Generate benchmark summary tables
```

### Run Scientific Analysis & Visualizations
```bash
python analysis/benchmark_analysis.py
```
Outputs:
- `analysis/air_density_vs_sixes.png`
- `analysis/pitch_soil_comparison.png`

---

## 📖 Data Dictionary & Documentation
- **[docs/CODEBOOK.md](docs/CODEBOOK.md)**: Full variable definitions, types, valid ranges, and units.
- **[dataset-metadata.json](dataset-metadata.json)**: Kaggle dataset publication metadata.

---

## 📜 Citation & Credits
- **Ball-by-Ball Data**: Open data courtesy of [Cricsheet](https://cricsheet.org/).
- **Atmospheric & Weather Data**: Historical reanalysis courtesy of [Open-Meteo](https://open-meteo.com/).
- **License**: Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
