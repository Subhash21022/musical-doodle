"""
Pipeline Step 3: Match Context Extraction & Atmospheric Physics Weather Enrichment
Extracts match metadata from raw Cricsheet JSON and enriches every match with historical
weather (temperature, relative humidity, dew point, pressure, wind, cloud cover)
and derived physics metrics (Air Density rho, Dew Index, Swing Friendliness).
"""

import os
import re
import json
import math
import logging
import urllib.request
import pandas as pd
import sys
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
RAW_IPL = os.path.join(BASE_DIR, "data", "raw", "ipl_json")
RAW_T20S = os.path.join(BASE_DIR, "data", "raw", "t20s_json")

WEATHER_CACHE_FILE = os.path.join(CACHE_DIR, "openmeteo_weather_cache.json")

def calc_air_density(temp_c: float, rh_pct: float, pressure_hpa: float) -> float:
    """
    Calculates moist air density (rho) in kg/m^3 using the ideal gas law:
    rho = (pd / (Rd * T)) + (pv / (Rv * T))
    """
    tk = temp_c + 273.15
    # Magnus-Tetens formula for saturation vapor pressure (hPa)
    es = 6.1078 * (10.0 ** ((7.5 * temp_c) / (temp_c + 237.3)))
    pv = es * (rh_pct / 100.0)
    pd = pressure_hpa - pv
    # Rd = 287.058 J/(kg*K), Rv = 461.495 J/(kg*K)
    rho = (pd * 100.0) / (287.058 * tk) + (pv * 100.0) / (461.495 * tk)
    return round(rho, 4)

def calc_dew_index(temp_c: float, rh_pct: float, dew_point_c: float, is_evening: bool) -> float:
    """
    Calculates Dew Formation Risk Index (0.0 to 1.0).
    Dew requires high RH and a narrow dew point depression (temp - dew_point <= 3C),
    typically in evening/night conditions after radiation cooling.
    """
    if not is_evening:
        return 0.05
    dp_depression = max(0.0, temp_c - dew_point_c)
    # Higher RH and smaller depression increases dew likelihood
    rh_factor = max(0.0, (rh_pct - 55.0) / 35.0)
    depression_factor = max(0.0, (4.0 - dp_depression) / 4.0)
    dew_score = min(1.0, max(0.0, rh_factor * 0.6 + depression_factor * 0.4))
    return round(dew_score, 2)

def calc_swing_score(temp_c: float, rh_pct: float, cloud_cover_pct: float, air_density: float) -> float:
    """
    Calculates Atmospheric Swing Friendliness Index (0.0 to 10.0).
    Conventional swing is favored by:
    - Moderate/cool temperatures (15-26C)
    - Moderate-to-high humidity (50-80% RH creates boundary layer turbulence)
    - Overcast cloud cover (reduces thermal updrafts)
    - Higher air density (> 1.15 kg/m^3)
    """
    score = 5.0
    # Air density impact: denser air = more lateral aerodynamic force
    if air_density > 1.18:
        score += 1.5
    elif air_density < 1.05:
        score -= 1.5
        
    # Humidity impact
    if 55 <= rh_pct <= 85:
        score += 1.5
    elif rh_pct < 35:
        score -= 1.0
        
    # Cloud cover impact
    if cloud_cover_pct > 60:
        score += 1.5
    elif cloud_cover_pct < 20:
        score -= 0.5
        
    # Temperature impact
    if temp_c < 24:
        score += 0.5
    elif temp_c > 36:
        score -= 1.0
        
    return round(min(10.0, max(1.0, score)), 1)

def load_weather_cache():
    if os.path.exists(WEATHER_CACHE_FILE):
        try:
            with open(WEATHER_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_weather_cache(cache):
    with open(WEATHER_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

def fetch_weather_batch(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """
    Fetches hourly weather from Open-Meteo for a given lat/lon and date range.
    Returns dictionary mapping date 'YYYY-MM-DD' -> weather averages.
    """
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat:.4f}&longitude={lon:.4f}&start_date={start_date}&end_date={end_date}&"
        f"hourly=temperature_2m,relative_humidity_2m,dew_point_2m,surface_pressure,wind_speed_10m,cloud_cover,precipitation"
    )
    headers = {"User-Agent": "CricketResearchBenchmark/1.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
        
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rhs = hourly.get("relative_humidity_2m", [])
    dps = hourly.get("dew_point_2m", [])
    pressures = hourly.get("surface_pressure", [])
    winds = hourly.get("wind_speed_10m", [])
    clouds = hourly.get("cloud_cover", [])
    precips = hourly.get("precipitation", [])
    
    # Aggregate by date (specifically focused on match hours 14:00 to 23:00)
    date_records = {}
    for i, t_str in enumerate(times):
        dt_date, dt_hour = t_str.split("T")
        hour_int = int(dt_hour.split(":")[0])
        
        # Consider primary playing hours 14:00 - 23:00
        if 14 <= hour_int <= 23:
            if dt_date not in date_records:
                date_records[dt_date] = []
            date_records[dt_date].append({
                "temp": temps[i] if i < len(temps) and temps[i] is not None else 28.0,
                "rh": rhs[i] if i < len(rhs) and rhs[i] is not None else 60.0,
                "dew_point": dps[i] if i < len(dps) and dps[i] is not None else 20.0,
                "pressure": pressures[i] if i < len(pressures) and pressures[i] is not None else 1005.0,
                "wind": winds[i] if i < len(winds) and winds[i] is not None else 10.0,
                "cloud": clouds[i] if i < len(clouds) and clouds[i] is not None else 30.0,
                "precip": precips[i] if i < len(precips) and precips[i] is not None else 0.0
            })
            
    summary_by_date = {}
    for d, recs in date_records.items():
        if not recs:
            continue
        avg_temp = round(sum(r["temp"] for r in recs) / len(recs), 1)
        avg_rh = round(sum(r["rh"] for r in recs) / len(recs), 1)
        avg_dp = round(sum(r["dew_point"] for r in recs) / len(recs), 1)
        avg_press = round(sum(r["pressure"] for r in recs) / len(recs), 1)
        avg_wind = round(sum(r["wind"] for r in recs) / len(recs), 1)
        avg_cloud = round(sum(r["cloud"] for r in recs) / len(recs), 1)
        tot_precip = round(sum(r["precip"] for r in recs), 2)
        
        summary_by_date[d] = {
            "temperature_c": avg_temp,
            "relative_humidity_pct": avg_rh,
            "dew_point_c": avg_dp,
            "surface_pressure_hpa": avg_press,
            "wind_speed_kmh": avg_wind,
            "cloud_cover_pct": avg_cloud,
            "precipitation_mm": tot_precip
        }
    return summary_by_date

def get_climate_normal(elevation_m: float, lat: float, month: int) -> dict:
    """Fallback climate normal model based on venue altitude, latitude, and month."""
    # Standard barometric lapse rate
    base_pressure = 1013.25 * math.pow(1 - (0.0065 * elevation_m) / 288.15, 5.255)
    
    # Tropical vs Temperate baseline
    is_subcontinent_summer = (10 <= lat <= 35) and (3 <= month <= 6)
    if is_subcontinent_summer:
        temp = 32.0 - (elevation_m * 0.0065)
        rh = 55.0
        dp = temp - 10.0
        cloud = 25.0
    else:
        temp = 25.0 - (elevation_m * 0.0065)
        rh = 65.0
        dp = temp - 6.0
        cloud = 40.0
        
    return {
        "temperature_c": round(temp, 1),
        "relative_humidity_pct": round(rh, 1),
        "dew_point_c": round(dp, 1),
        "surface_pressure_hpa": round(base_pressure, 1),
        "wind_speed_kmh": 12.0,
        "cloud_cover_pct": round(cloud, 1),
        "precipitation_mm": 0.0
    }

def parse_match_deliveries_summary(innings_data: list) -> dict:
    """Summarizes runs, wickets, boundaries, and sixes across both innings."""
    summary = {
        "innings1_team": None,
        "innings1_runs": 0,
        "innings1_wickets": 0,
        "innings1_legal_balls": 0,
        "innings2_team": None,
        "innings2_runs": 0,
        "innings2_wickets": 0,
        "innings2_legal_balls": 0,
        "match_fours": 0,
        "match_sixes": 0
    }
    
    if not innings_data:
        return summary

    for idx, inn in enumerate(innings_data[:2]):
        prefix = f"innings{idx+1}"
        summary[f"{prefix}_team"] = inn.get("team")
        runs = 0
        wickets = 0
        legal_balls = 0
        
        for ov in inn.get("overs", []):
            for deliv in ov.get("deliveries", []):
                bat_runs = deliv.get("runs", {}).get("batter", 0)
                tot_runs = deliv.get("runs", {}).get("total", 0)
                runs += tot_runs
                
                # Check legal ball (not wide, not noball)
                extras = deliv.get("extras", {})
                if "wides" not in extras and "noballs" not in extras:
                    legal_balls += 1
                    
                if "wickets" in deliv:
                    wickets += len(deliv["wickets"])
                    
                if bat_runs == 4:
                    summary["match_fours"] += 1
                elif bat_runs == 6:
                    summary["match_sixes"] += 1
                    
        summary[f"{prefix}_runs"] = runs
        summary[f"{prefix}_wickets"] = wickets
        summary[f"{prefix}_legal_balls"] = legal_balls

    return summary

def main():
    venues_path = os.path.join(PROCESSED_DIR, "venues_master.csv")
    if not os.path.exists(venues_path):
        raise FileNotFoundError(f"Missing {venues_path}. Run 02_build_venues_catalog.py first.")
        
    df_venues = pd.read_csv(venues_path)
    venue_map = {row["venue_id"]: row.to_dict() for _, row in df_venues.iterrows()}
    
    # Load venues lookup
    sys.path.insert(0, os.path.join(BASE_DIR, "pipeline"))
    import importlib
    venues_builder = importlib.import_module("02_build_venues_catalog")
    lookup = venues_builder.build_venue_lookup()
    normalize_text = venues_builder.normalize_text

    cache_path = os.path.join(CACHE_DIR, "dynamic_venues_cache.json")
    dynamic_cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            dynamic_cache = json.load(f)

    # Collect match files (all IPL + top international T20s)
    ipl_files = [os.path.join(RAW_IPL, f) for f in os.listdir(RAW_IPL) if f.endswith(".json")]
    t20_files = [os.path.join(RAW_T20S, f) for f in os.listdir(RAW_T20S) if f.endswith(".json")]
    
    logging.info(f"Loaded {len(ipl_files)} IPL match files and {len(t20_files)} T20 match files.")
    
    # Prioritize: All IPL matches + high-profile T20I matches (or all if desired)
    # Let's index all IPL and all international T20s
    match_targets = [(f, "IPL") for f in ipl_files] + [(f, "T20I") for f in t20_files]
    
    weather_cache = load_weather_cache()
    logging.info(f"Loaded {len(weather_cache)} cached weather date-venue entries.")

    # Pass 1: Parse match infos and group required weather queries by (venue_id, year)
    parsed_matches = []
    needed_weather_queries = {}  # (venue_id, year) -> list of dates
    
    logging.info("Extracting match metadata and identifying weather query windows...")
    for fpath, comp in match_targets:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            info = data.get("info", {})
            match_id = os.path.basename(fpath).replace(".json", "")
            raw_venue = info.get("venue", "Unknown Venue")
            raw_city = info.get("city", "")
            dates = info.get("dates", [])
            if not dates:
                continue
            match_date = dates[0]
            
            # Resolve venue_id
            norm_v = normalize_text(raw_venue)
            matched = lookup.get(norm_v)
            if not matched:
                for k, v in lookup.items():
                    if k in norm_v or norm_v in k:
                        matched = v
                        break
            if not matched:
                cache_key = f"{raw_venue}___{raw_city}"
                matched = dynamic_cache.get(cache_key)
                
            venue_id = matched["venue_id"] if matched else "INT_DEFAULT"
            v_meta = venue_map.get(venue_id, {
                "canonical_name": raw_venue,
                "city": raw_city,
                "country": "International",
                "latitude": 20.0,
                "longitude": 75.0,
                "elevation_m": 50.0,
                "boundary_avg_m": 65.0,
                "pitch_soil_type": "Standard Clay Loam",
                "pitch_behavior": "Balanced"
            })
            
            # Check if weather already in cache
            cache_key = f"{venue_id}_{match_date}"
            if cache_key not in weather_cache:
                year = match_date.split("-")[0]
                q_key = (venue_id, year)
                if q_key not in needed_weather_queries:
                    needed_weather_queries[q_key] = []
                needed_weather_queries[q_key].append(match_date)
                
            innings_summary = parse_match_deliveries_summary(data.get("innings", []))
            
            parsed_matches.append({
                "match_id": match_id,
                "competition": comp,
                "season": str(info.get("season", "")),
                "date": match_date,
                "match_type": info.get("match_type", "T20"),
                "venue_id": venue_id,
                "raw_venue": raw_venue,
                "v_meta": v_meta,
                "toss_winner": info.get("toss", {}).get("winner"),
                "toss_decision": info.get("toss", {}).get("decision"),
                "winner": info.get("outcome", {}).get("winner"),
                "margin_runs": info.get("outcome", {}).get("by", {}).get("runs", 0),
                "margin_wickets": info.get("outcome", {}).get("by", {}).get("wickets", 0),
                "player_of_match": info.get("player_of_match", [None])[0] if info.get("player_of_match") else None,
                "innings_summary": innings_summary
            })
        except Exception:
            continue
            
    logging.info(f"Parsed {len(parsed_matches)} matches. Missing weather cache for {len(needed_weather_queries)} venue-year batches.")
    
    # Pass 2: Fetch missing weather in efficient date-range batches
    # Sort venue-years and fetch
    fetched_count = 0
    for (vid, year), d_list in needed_weather_queries.items():
        v_meta = venue_map.get(vid)
        if not v_meta or vid == "INT_DEFAULT":
            continue
            
        min_date = min(d_list)
        max_date = max(d_list)
        lat = v_meta["latitude"]
        lon = v_meta["longitude"]
        
        # Don't query future dates
        current_year = datetime.now().year
        if int(year) > current_year:
            continue
            
        try:
            # Query Open-Meteo for the date range
            batch_data = fetch_weather_batch(lat, lon, min_date, max_date)
            for d, w in batch_data.items():
                ckey = f"{vid}_{d}"
                weather_cache[ckey] = w
            fetched_count += 1
            import time
            time.sleep(0.2)
            if fetched_count % 10 == 0:
                logging.info(f"Fetched weather for {fetched_count} / {len(needed_weather_queries)} batches... saving cache.")
                save_weather_cache(weather_cache)
        except Exception as e:
            # If rate limited or network failure, use climate normal model
            for d in d_list:
                ckey = f"{vid}_{d}"
                m = int(d.split("-")[1])
                weather_cache[ckey] = get_climate_normal(v_meta["elevation_m"], lat, m)
                
    save_weather_cache(weather_cache)
    logging.info(f"Weather cache complete. Total cached date-venue entries: {len(weather_cache)}")
    
    # Pass 3: Assemble Enriched Matches Table
    enriched_rows = []
    for m in parsed_matches:
        vid = m["venue_id"]
        m_date = m["date"]
        v_meta = m["v_meta"]
        ckey = f"{vid}_{m_date}"
        
        w = weather_cache.get(ckey)
        if not w:
            m_month = int(m_date.split("-")[1])
            w = get_climate_normal(v_meta.get("elevation_m", 50.0), v_meta.get("latitude", 20.0), m_month)
            
        temp_c = w["temperature_c"]
        rh = w["relative_humidity_pct"]
        dp = w["dew_point_c"]
        press = w["surface_pressure_hpa"]
        wind = w["wind_speed_kmh"]
        cloud = w["cloud_cover_pct"]
        
        # Physics computations
        rho = calc_air_density(temp_c, rh, press)
        is_evening = True  # Standard T20 night match assumption
        dew_idx = calc_dew_index(temp_c, rh, dp, is_evening)
        swing_score = calc_swing_score(temp_c, rh, cloud, rho)
        
        inn = m["innings_summary"]
        inn1_overs = round(inn["innings1_legal_balls"] / 6.0, 1)
        inn2_overs = round(inn["innings2_legal_balls"] / 6.0, 1)
        inn1_rr = round(inn["innings1_runs"] / inn1_overs, 2) if inn1_overs > 0 else 0.0
        inn2_rr = round(inn["innings2_runs"] / inn2_overs, 2) if inn2_overs > 0 else 0.0
        
        row = {
            "match_id": m["match_id"],
            "competition": m["competition"],
            "season": m["season"],
            "date": m_date,
            "venue_id": vid,
            "venue_name": v_meta.get("canonical_name", m["raw_venue"]),
            "city": v_meta.get("city", ""),
            "country": v_meta.get("country", ""),
            "elevation_m": v_meta.get("elevation_m", 50.0),
            "boundary_avg_m": v_meta.get("boundary_avg_m", 65.0),
            "pitch_soil_type": v_meta.get("pitch_soil_type", "Standard Clay Loam"),
            "pitch_behavior": v_meta.get("pitch_behavior", "Balanced"),
            "toss_winner": m["toss_winner"],
            "toss_decision": m["toss_decision"],
            "match_winner": m["winner"],
            "margin_runs": m["margin_runs"],
            "margin_wickets": m["margin_wickets"],
            "player_of_match": m["player_of_match"],
            
            # Innings Summaries
            "innings1_team": inn["innings1_team"],
            "innings1_runs": inn["innings1_runs"],
            "innings1_wickets": inn["innings1_wickets"],
            "innings1_overs": inn1_overs,
            "innings1_run_rate": inn1_rr,
            
            "innings2_team": inn["innings2_team"],
            "innings2_runs": inn["innings2_runs"],
            "innings2_wickets": inn["innings2_wickets"],
            "innings2_overs": inn2_overs,
            "innings2_run_rate": inn2_rr,
            
            "match_total_fours": inn["match_fours"],
            "match_total_sixes": inn["match_sixes"],
            
            # Atmospheric & Physics Variables
            "temperature_c": temp_c,
            "relative_humidity_pct": rh,
            "dew_point_c": dp,
            "dew_point_depression_c": round(max(0.0, temp_c - dp), 1),
            "surface_pressure_hpa": press,
            "air_density_kg_m3": rho,
            "wind_speed_kmh": wind,
            "cloud_cover_pct": cloud,
            "dew_index": dew_idx,
            "swing_condition_score": swing_score
        }
        enriched_rows.append(row)
        
    df_out = pd.DataFrame(enriched_rows)
    # Sort chronologically
    df_out = df_out.sort_values(by=["date", "match_id"]).reset_index(drop=True)
    
    out_csv = os.path.join(PROCESSED_DIR, "matches_enriched.csv")
    df_out.to_csv(out_csv, index=False)
    logging.info(f"Successfully created matches enriched dataset: {out_csv}")
    logging.info(f"Total matches enriched: {len(df_out)}")
    logging.info(f"Summary stats:\n{df_out[['elevation_m', 'air_density_kg_m3', 'dew_index', 'match_total_sixes']].describe()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enrich matches with historical weather and physics")
    parser.add_argument("--limit-batches", type=int, default=None, help="Limit number of weather API batches to fetch")
    args = parser.parse_args()
    main()

