# Cricket Pitch and Weather Performance Benchmark: Codebook & Data Dictionary

This codebook provides variable definitions, units, derivations, and valid ranges for all datasets in the **Cricket Pitch and Weather Performance Benchmark**.

---

## 1. `data/processed/venues_master.csv`
Master registry of international and domestic cricket venues with geographic, atmospheric, structural, and agronomic attributes.

| Column | Data Type | Units / Format | Description |
| :--- | :--- | :--- | :--- |
| `venue_id` | String | Identifier | Unique standardized venue key (e.g., `IND_MUM_WANKHEDE`, `AUS_MEL_MCG`). |
| `canonical_name` | String | Text | Official standard ground name. |
| `city` | String | Text | Host city of the stadium. |
| `country` | String | Text | Host nation. |
| `latitude` | Float | Decimal Degrees | GPS latitude coordinate (-90.0 to 90.0). |
| `longitude` | Float | Decimal Degrees | GPS longitude coordinate (-180.0 to 180.0). |
| `elevation_m` | Float | Meters ($m$) | Ground elevation above mean sea level ($0$ to $1720\text{ m}$). Derived from Open-Meteo elevation models. |
| `boundary_straight_m` | Float | Meters ($m$) | Distance from pitch center to straight boundary along the longitudinal axis. |
| `boundary_square_off_m` | Float | Meters ($m$) | Distance from pitch center to off-side square boundary. |
| `boundary_square_leg_m` | Float | Meters ($m$) | Distance from pitch center to leg-side square boundary. |
| `boundary_fine_leg_m` | Float | Meters ($m$) | Distance from pitch center to fine leg rope. |
| `boundary_third_man_m` | Float | Meters ($m$) | Distance from pitch center to third man rope. |
| `boundary_avg_m` | Float | Meters ($m$) | Mean boundary radius of the playing field. |
| `pitch_soil_type` | Categorical | Text | Soil composition: `Red Soil`, `Black Soil`, `Clay/Loam Mix`, `Bulli Clay`, `Laterite`, `Tropical Clay`, etc. |
| `pitch_behavior` | Categorical | Text | Historical pitch tendency: `Pace & True Bounce`, `Spin & Grip`, `Batting Paradise`, `Two-Paced`, `Seam & Swing`. |
| `grass_coverage` | Categorical | Text | Turf profile: `Shaved / Bare`, `Light Grass`, `Moderate Grass`, `Heavy Grass`. |

---

## 2. `data/processed/matches_enriched.csv`
Match-level records linking contextual outcome data with hourly ambient weather and calculated physics variables.

| Column | Data Type | Units / Format | Description |
| :--- | :--- | :--- | :--- |
| `match_id` | String | ID | Unique identifier from Cricsheet. |
| `competition` | Categorical | String | `IPL` (Indian Premier League) or `T20I` (Men's T20 Internationals). |
| `season` | String | YYYY or Season | Season identifier (e.g. `2023`, `2020/21`). |
| `date` | Date | `YYYY-MM-DD` | Date the match commenced. |
| `venue_id` | String | Foreign Key | References `venues_master.csv`. |
| `venue_name` | String | Text | Venue name. |
| `city` | String | Text | Host city. |
| `country` | String | Text | Host country. |
| `elevation_m` | Float | Meters ($m$) | Stadium elevation. |
| `boundary_avg_m` | Float | Meters ($m$) | Mean boundary distance. |
| `pitch_soil_type` | Categorical | Text | Pitch soil profile. |
| `pitch_behavior` | Categorical | Text | General pitch pace/spin behavior. |
| `toss_winner` | String | Team Name | Team winning the coin toss. |
| `toss_decision` | Categorical | `bat` / `field` | Tactical decision chosen by toss winner. |
| `match_winner` | String | Team Name | Official match winner. |
| `margin_runs` | Integer | Runs | Margin of victory if team batting 1st won (0 otherwise). |
| `margin_wickets` | Integer | Wickets | Margin of victory if team batting 2nd won (0 otherwise). |
| `player_of_match` | String | Player Name | Designated Man/Player of the Match. |
| `innings1_team` | String | Team Name | Team batting in 1st innings. |
| `innings1_runs` | Integer | Runs | Total score in 1st innings. |
| `innings1_wickets` | Integer | Wickets ($0-10$) | Total wickets lost in 1st innings. |
| `innings1_overs` | Float | Overs | Overs completed in 1st innings. |
| `innings1_run_rate` | Float | Runs / Over | 1st innings run rate ($RPO$). |
| `innings2_team` | String | Team Name | Team batting in 2nd innings. |
| `innings2_runs` | Integer | Runs | Total score in 2nd innings. |
| `innings2_wickets` | Integer | Wickets ($0-10$) | Total wickets lost in 2nd innings. |
| `innings2_overs` | Float | Overs | Overs completed in 2nd innings. |
| `innings2_run_rate` | Float | Runs / Over | 2nd innings run rate ($RPO$). |
| `match_total_fours` | Integer | Count | Total 4s hit in the match. |
| `match_total_sixes` | Integer | Count | Total 6s hit in the match. |
| `temperature_c` | Float | Celsius ($^\circ\text{C}$) | Average ambient temperature during playing hours. |
| `relative_humidity_pct` | Float | Percentage ($\%$) | Mean relative humidity ($0-100\%$). |
| `dew_point_c` | Float | Celsius ($^\circ\text{C}$) | Dew point temperature. |
| `dew_point_depression_c`| Float | Celsius ($^\circ\text{C}$) | Difference between temperature and dew point ($T - T_{dew}$). |
| `surface_pressure_hpa` | Float | $hPa$ / $mbar$ | Local atmospheric pressure at ground level ($800 - 1030\text{ hPa}$). |
| `air_density_kg_m3` | Float | $kg/m^3$ | Moist air density ($\rho$) calculated using the ideal gas law: $\rho = \frac{p_d}{R_d T} + \frac{p_v}{R_v T}$. |
| `wind_speed_kmh` | Float | $km/h$ | Wind velocity at 10m altitude. |
| `cloud_cover_pct` | Float | Percentage ($\%$) | Sky coverage ($0-100\%$). |
| `dew_index` | Float | Scaled ($0.0 - 1.0$) | Estimated dew formation risk score. |
| `swing_condition_score`| Float | Index ($1.0 - 10.0$) | Atmospheric suitability score for lateral aerodynamic ball swing. |

---

## 3. `data/processed/deliveries_enriched.parquet`
Ball-by-ball delivery-level dataset (1.6+ million rows) linked with match conditions, tactical phases, and bowling styles.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `match_id` | String | Match ID foreign key. |
| `delivery_id` | String | Unique delivery key (`{match_id}_{innings}_{over}_{ball}`). |
| `competition` | String | Tournament name (`IPL` or `T20I`). |
| `season` | String | Season. |
| `date` | String | Date of match (`YYYY-MM-DD`). |
| `innings` | Integer | Innings number (1 or 2). |
| `over` | Integer | 0-indexed over number (0 to 19). |
| `ball_in_over` | Integer | Delivery number in the over. |
| `phase` | Categorical | `Powerplay` (overs 0-5), `Middle Overs` (overs 6-14), `Death Overs` (overs 15-19). |
| `batting_team` | String | Team batting. |
| `bowling_team` | String | Team fielding. |
| `batter` | String | Striking batter name. |
| `bowler` | String | Bowler name. |
| `bowler_type` | Categorical | Classified style: `Pace` (Fast, Fast-Medium) or `Spin` (Off-spin, Leg-spin, Slow Left Arm). |
| `non_striker` | String | Non-striker name. |
| `runs_batter` | Integer | Runs scored off the bat ($0-6$). |
| `runs_extras` | Integer | Extra runs on delivery (wides, noballs, byes, legbyes). |
| `runs_total` | Integer | Total runs conceded on delivery. |
| `is_dot` | Integer (0/1) | 1 if total runs = 0, else 0. |
| `is_boundary_four` | Integer (0/1) | 1 if 4 runs scored off bat. |
| `is_boundary_six` | Integer (0/1) | 1 if 6 runs scored off bat. |
| `is_wicket` | Integer (0/1) | 1 if dismissal occurred on delivery. |
| `dismissal_kind` | String | Mode of dismissal (`caught`, `bowled`, `lbw`, `run out`, `stumped`, etc.). |
| `dismissed_player` | String | Player out. |
| `venue_id` | String | Venue identifier. |
| `venue_name` | String | Venue name. |
| `elevation_m` | Float | Altitude above sea level ($m$). |
| `boundary_avg_m` | Float | Mean boundary distance ($m$). |
| `boundary_straight_m` | Float | Straight boundary distance ($m$). |
| `boundary_square_off_m` | Float | Off-side square boundary distance ($m$). |
| `pitch_soil_type` | String | Pitch soil composition. |
| `pitch_behavior` | String | Pitch behavior profile. |
| `temperature_c` | Float | Temperature ($^\circ\text{C}$). |
| `relative_humidity_pct` | Float | Relative humidity ($\%$). |
| `dew_point_c` | Float | Dew point ($^\circ\text{C}$). |
| `surface_pressure_hpa` | Float | Atmospheric surface pressure ($hPa$). |
| `air_density_kg_m3` | Float | Moist air density ($\rho$, $kg/m^3$). |
| `wind_speed_kmh` | Float | Wind speed ($km/h$). |
| `cloud_cover_pct` | Float | Cloud cover ($\%$). |
| `dew_index` | Float | Dew risk score ($0.0 - 1.0$). |
| `swing_condition_score` | Float | Swing friendliness rating ($1.0 - 10.0$). |

---

## 4. Derived Physics Formulas

### Moist Air Density ($\rho$)
$$\rho = \frac{p_d}{R_d \cdot T_K} + \frac{p_v}{R_v \cdot T_K}$$
Where:
- $T_K = T_{celsius} + 273.15$ (Kelvin)
- $e_s = 6.1078 \times 10^{\left(\frac{7.5 \cdot T}{T + 237.3}\right)}$ (Saturation vapor pressure, hPa)
- $p_v = e_s \times \frac{RH}{100}$ (Actual vapor pressure, hPa)
- $p_d = p_{surface} - p_v$ (Dry air partial pressure, hPa)
- $R_d = 287.058\text{ J/(kg}\cdot\text{K)}$ (Specific gas constant for dry air)
- $R_v = 461.495\text{ J/(kg}\cdot\text{K)}$ (Specific gas constant for water vapor)
