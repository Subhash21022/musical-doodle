"""
Pipeline Step 4: Ball-by-Ball Linked Dataset Generation (Parquet & CSV Sample)
Extracts every ball-by-ball delivery, tags match phase (Powerplay/Middle/Death),
classifies bowler style (Pace vs Spin), and joins venue altitude, boundary dimensions,
pitch soil characteristics, air density, dew index, and weather metrics.
"""

import os
import re
import json
import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
RAW_IPL = os.path.join(BASE_DIR, "data", "raw", "ipl_json")
RAW_T20S = os.path.join(BASE_DIR, "data", "raw", "t20s_json")

# Bowler Taxonomy: Major Spinners vs Pace Bowlers
KNOWN_SPINNERS = {
    "rashid khan", "sp narine", "sunil narine", "ys chahal", "yuzvendra chahal",
    "r ashwin", "ravichandran ashwin", "ra jadeja", "ravindra jadeja", "kuldeep yadav",
    "a zampa", "adam zampa", "pwa de silva", "wanindu hasaranga", "imran tahir",
    "shakib al hasan", "ar patel", "axar patel", "ravi bishnoi", "cv varun", "varun chakravarthy",
    "mujeeb ur rahman", "harbhajan singh", "pp chawla", "piyush chawla", "a kumble", "anil kumble",
    "amit mishra", "washington sundar", "krunal pandya", "mohammad nabi", "noor ahmad",
    "m theekshana", "maheesh theekshana", "ka maharaj", "keshav maharaj", "is sodhi", "ish sodhi",
    "mj santner", "mitchell santner", "moeen ali", "au rashid", "adil rashid", "t shamsi", "tabraiz shamsi",
    "nm lyon", "nathan lyon", "m muralitharan", "muttiah muralitharan", "shadab khan",
    "usman qadir", "imad wasim", "mohammad nawaz", "afridi", "shahid afridi", "saeed ajmal",
    "saqlain mushtaq", "m santner", "gj maxwell", "glenn maxwell", "sk raina", "suresh raina",
    "deepak hooda", "shahbaz ahmed", "rahul chahar", "rd chahar", "m markande", "mayank markande",
    "s gopal", "shreyas gopal", "karn sharma", "pravin tambe", "p pravin", "m ashwin", "murugan ashwin",
    "sai kishore", "r sai kishore", "s lamichhane", "sandeep lamichhane", "gudakesh motie",
    "akeal hosein", "roston chase", "hayden walsh", "danish kaneria", "graeme swann", "g swann"
}

KNOWN_PACERS = {
    "jj bumrah", "jasprit bumrah", "ma starc", "mitchell starc", "ta boult", "trent boult",
    "mohammed shami", "m shami", "pj cummins", "pat cummins", "jc archer", "jofra archer",
    "k rabada", "kagiso rabada", "mohammed siraj", "m siraj", "b kumar", "bhuvaneshwar kumar",
    "jr hazlewood", "josh hazlewood", "sl malinga", "lasith malinga", "ut yadav", "umesh yadav",
    "i sharma", "ishant sharma", "sn thakur", "shardul thakur", "harshit rana", "mayank yadav",
    "arshdeep singh", "m pathirana", "matheesha pathirana", "dj bravo", "dwayne bravo",
    "ch morris", "chris morris", "l ferguson", "lockie ferguson", "a nehra", "ashish nehra",
    "z khan", "zaheer khan", "rp singh", "ja morkel", "albie morkel", "dw steyn", "dale steyn",
    "m morkel", "morne morkel", "mg johnson", "mitchell johnson", "b lee", "brett lee",
    "p kumar", "praveen kumar", "mm sharma", "mohit sharma", "hv patel", "harshal patel",
    "dl chahar", "deepak chahar", "t natarajan", "avesh khan", "prasidh krishna", "khaleel ahmed",
    "umran malik", "shivam dube", "hardik pandya", "hh pandya", "marcus stoinis", "mp stoinis",
    "andre russell", "ad russell", "anrich nortje", "a nortje", "lungi ngidi", "l ngidi",
    "marco jansen", "m jansen", "jason holder", "jo holder", "alzarri joseph", "as joseph",
    "shaheen shah afridi", "haris rauf", "naseem shah", "mohammad amir", "wahab riaz",
    "hasan ali", "tim southee", "tg southee", "matt henry", "mj henry", "kyle jamieson",
    "shannon gabriel", "kemar roach", "mustafizur rahman", "taskin ahmed", "shoriful islam",
    "chris woakes", "cr woakes", "mark wood", "ma wood", "sam curran", "sm curran", "david willey",
    "re Reece topley", "r topley", "josh tongue", "oliver stone", "o stone", "brydon carse"
}

def classify_bowler(bowler_name: str) -> str:
    """Classifies bowler as 'Spin', 'Pace', or 'Medium / All-Rounder'."""
    clean = bowler_name.lower().strip()
    if clean in KNOWN_SPINNERS:
        return "Spin"
    if clean in KNOWN_PACERS:
        return "Pace"
    for s in KNOWN_SPINNERS:
        if s in clean or clean in s:
            return "Spin"
    for p in KNOWN_PACERS:
        if p in clean or clean in p:
            return "Pace"
    # Fallback heuristic
    return "Pace / Seam"

def get_match_phase(over: int) -> str:
    """Classifies T20 over (0-indexed) into standard tactical phase."""
    if over < 6:
        return "Powerplay"
    elif over < 15:
        return "Middle Overs"
    else:
        return "Death Overs"

def main(max_matches: int = None):
    matches_csv = os.path.join(PROCESSED_DIR, "matches_enriched.csv")
    venues_csv = os.path.join(PROCESSED_DIR, "venues_master.csv")
    
    if not os.path.exists(matches_csv):
        raise FileNotFoundError(f"Missing {matches_csv}. Run 03_enrich_weather.py first.")
        
    df_matches = pd.read_csv(matches_csv)
    df_venues = pd.read_csv(venues_csv)
    venue_dict = {row["venue_id"]: row.to_dict() for _, row in df_venues.iterrows()}
    
    # Fast map: match_id -> match condition metadata
    match_conditions = {str(row["match_id"]): row.to_dict() for _, row in df_matches.iterrows()}
    
    logging.info(f"Loaded {len(match_conditions)} enriched matches for delivery extraction.")
    
    # Target files to process
    all_json_files = []
    if os.path.exists(RAW_IPL):
        all_json_files.extend([(os.path.join(RAW_IPL, f), "IPL") for f in os.listdir(RAW_IPL) if f.endswith(".json")])
    if os.path.exists(RAW_T20S):
        all_json_files.extend([(os.path.join(RAW_T20S, f), "T20I") for f in os.listdir(RAW_T20S) if f.endswith(".json")])
        
    if max_matches:
        all_json_files = all_json_files[:max_matches]
        logging.info(f"Limiting to first {max_matches} matches as requested.")

    logging.info(f"Extracting deliveries across {len(all_json_files)} match files...")

    deliveries_list = []
    batch_records = []
    parquet_writer = None
    output_parquet = os.path.join(PROCESSED_DIR, "deliveries_enriched.parquet")
    sample_csv = os.path.join(PROCESSED_DIR, "deliveries_sample.csv")

    schema = pa.schema([
        ("match_id", pa.string()),
        ("delivery_id", pa.string()),
        ("competition", pa.string()),
        ("season", pa.string()),
        ("date", pa.string()),
        ("innings", pa.int32()),
        ("over", pa.int32()),
        ("ball_in_over", pa.int32()),
        ("phase", pa.string()),
        ("batting_team", pa.string()),
        ("bowling_team", pa.string()),
        ("batter", pa.string()),
        ("bowler", pa.string()),
        ("bowler_type", pa.string()),
        ("non_striker", pa.string()),
        ("runs_batter", pa.int32()),
        ("runs_extras", pa.int32()),
        ("runs_total", pa.int32()),
        ("is_dot", pa.int32()),
        ("is_boundary_four", pa.int32()),
        ("is_boundary_six", pa.int32()),
        ("is_wicket", pa.int32()),
        ("dismissal_kind", pa.string()),
        ("dismissed_player", pa.string()),
        ("venue_id", pa.string()),
        ("venue_name", pa.string()),
        ("elevation_m", pa.float64()),
        ("boundary_avg_m", pa.float64()),
        ("boundary_straight_m", pa.float64()),
        ("boundary_square_off_m", pa.float64()),
        ("pitch_soil_type", pa.string()),
        ("pitch_behavior", pa.string()),
        ("temperature_c", pa.float64()),
        ("relative_humidity_pct", pa.float64()),
        ("dew_point_c", pa.float64()),
        ("surface_pressure_hpa", pa.float64()),
        ("air_density_kg_m3", pa.float64()),
        ("wind_speed_kmh", pa.float64()),
        ("cloud_cover_pct", pa.float64()),
        ("dew_index", pa.float64()),
        ("swing_condition_score", pa.float64())
    ])

    processed_match_count = 0
    total_deliveries = 0
    
    for fpath, comp in all_json_files:
        match_id = os.path.basename(fpath).replace(".json", "")
        m_cond = match_conditions.get(match_id)
        if not m_cond:
            continue
            
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
            
        vid = m_cond["venue_id"]
        v_meta = venue_dict.get(vid, {})
        straight_m = float(v_meta.get("boundary_straight_m", 70.0))
        square_m = float(v_meta.get("boundary_square_off_m", 65.0))
        
        for inn_idx, inn in enumerate(data.get("innings", [])[:2]):
            inn_num = inn_idx + 1
            bat_team = str(inn.get("team", ""))
            
            # Determine bowling team
            all_teams = data.get("info", {}).get("teams", [])
            bowl_team = ""
            for t in all_teams:
                if t != bat_team:
                    bowl_team = t
                    break

            for ov in inn.get("overs", []):
                over_num = int(ov.get("over", 0))
                phase = get_match_phase(over_num)
                
                for b_idx, deliv in enumerate(ov.get("deliveries", [])):
                    ball_in_over = b_idx + 1
                    deliv_id = f"{match_id}_{inn_num}_{over_num}_{ball_in_over}"
                    
                    batter = str(deliv.get("batter", ""))
                    bowler = str(deliv.get("bowler", ""))
                    non_striker = str(deliv.get("non_striker", ""))
                    bowler_type = classify_bowler(bowler)
                    
                    runs_bat = int(deliv.get("runs", {}).get("batter", 0))
                    runs_ext = int(deliv.get("runs", {}).get("extras", 0))
                    runs_tot = int(deliv.get("runs", {}).get("total", 0))
                    
                    is_dot = 1 if runs_tot == 0 else 0
                    is_four = 1 if runs_bat == 4 else 0
                    is_six = 1 if runs_bat == 6 else 0
                    
                    is_wkt = 0
                    d_kind = ""
                    d_player = ""
                    if "wickets" in deliv and deliv["wickets"]:
                        is_wkt = 1
                        wkt_info = deliv["wickets"][0]
                        d_kind = str(wkt_info.get("kind", ""))
                        d_player = str(wkt_info.get("player_out", ""))
                        
                    rec = {
                        "match_id": str(match_id),
                        "delivery_id": str(deliv_id),
                        "competition": str(comp),
                        "season": str(m_cond.get("season", "")),
                        "date": str(m_cond.get("date", "")),
                        "innings": int(inn_num),
                        "over": int(over_num),
                        "ball_in_over": int(ball_in_over),
                        "phase": str(phase),
                        "batting_team": str(bat_team),
                        "bowling_team": str(bowl_team),
                        "batter": str(batter),
                        "bowler": str(bowler),
                        "bowler_type": str(bowler_type),
                        "non_striker": str(non_striker),
                        "runs_batter": int(runs_bat),
                        "runs_extras": int(runs_ext),
                        "runs_total": int(runs_tot),
                        "is_dot": int(is_dot),
                        "is_boundary_four": int(is_four),
                        "is_boundary_six": int(is_six),
                        "is_wicket": int(is_wkt),
                        "dismissal_kind": str(d_kind),
                        "dismissed_player": str(d_player),
                        "venue_id": str(vid),
                        "venue_name": str(m_cond.get("venue_name", "")),
                        "elevation_m": float(m_cond.get("elevation_m", 50.0)),
                        "boundary_avg_m": float(m_cond.get("boundary_avg_m", 65.0)),
                        "boundary_straight_m": float(straight_m),
                        "boundary_square_off_m": float(square_m),
                        "pitch_soil_type": str(m_cond.get("pitch_soil_type", "Standard Clay Loam")),
                        "pitch_behavior": str(m_cond.get("pitch_behavior", "Balanced")),
                        "temperature_c": float(m_cond.get("temperature_c", 28.0)),
                        "relative_humidity_pct": float(m_cond.get("relative_humidity_pct", 60.0)),
                        "dew_point_c": float(m_cond.get("dew_point_c", 20.0)),
                        "surface_pressure_hpa": float(m_cond.get("surface_pressure_hpa", 1005.0)),
                        "air_density_kg_m3": float(m_cond.get("air_density_kg_m3", 1.15)),
                        "wind_speed_kmh": float(m_cond.get("wind_speed_kmh", 10.0)),
                        "cloud_cover_pct": float(m_cond.get("cloud_cover_pct", 30.0)),
                        "dew_index": float(m_cond.get("dew_index", 0.1)),
                        "swing_condition_score": float(m_cond.get("swing_condition_score", 5.0))
                    }
                    batch_records.append(rec)
                    total_deliveries += 1
                    
        processed_match_count += 1
        
        # Flush batch to Parquet writer every 200 matches
        if len(batch_records) >= 50000:
            df_batch = pd.DataFrame(batch_records)
            table = pa.Table.from_pandas(df_batch, schema=schema)
            if parquet_writer is None:
                parquet_writer = pq.ParquetWriter(output_parquet, schema, compression="snappy")
            parquet_writer.write_table(table)
            logging.info(f"Flushed {len(batch_records)} deliveries to parquet. Matches processed: {processed_match_count} / {len(all_json_files)}")
            
            # Save sample CSV if not saved
            if not os.path.exists(sample_csv):
                df_batch.head(5000).to_csv(sample_csv, index=False)
                logging.info(f"Saved sample CSV preview: {sample_csv}")
                
            batch_records.clear()

    # Flush any remaining records
    if batch_records:
        df_batch = pd.DataFrame(batch_records)
        table = pa.Table.from_pandas(df_batch, schema=schema)
        if parquet_writer is None:
            parquet_writer = pq.ParquetWriter(output_parquet, schema, compression="snappy")
        parquet_writer.write_table(table)
        
        if not os.path.exists(sample_csv):
            df_batch.head(5000).to_csv(sample_csv, index=False)

    if parquet_writer is not None:
        parquet_writer.close()

    logging.info(f"Done! Successfully generated enriched deliveries Parquet dataset: {output_parquet}")
    logging.info(f"Total deliveries written: {total_deliveries} across {processed_match_count} matches.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build enriched deliveries dataset")
    parser.add_argument("--max-matches", type=int, default=None, help="Max matches to process")
    args = parser.parse_args()
    main(max_matches=args.max_matches)
