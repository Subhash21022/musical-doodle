"""
Pipeline Step 2: Build Canonical Venue & Ground Master Catalog
Compiles precise venue metadata including GPS coordinates, elevation/altitude,
boundary dimensions (straight, square, avg), soil composition, and pitch behavior.
"""

import os
import re
import json
import logging
import urllib.request
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
RAW_IPL = os.path.join(BASE_DIR, "data", "raw", "ipl_json")
RAW_T20S = os.path.join(BASE_DIR, "data", "raw", "t20s_json")

# Curated Stadium Database with Ground Truth Dimensions, Elevation, and Pitch Soil
CURATED_VENUES = [
    # --- INDIAN PREMIER LEAGUE & TOP INDIAN VENUES ---
    {
        "venue_id": "IND_MUM_WANKHEDE",
        "canonical_name": "Wankhede Stadium",
        "city": "Mumbai",
        "country": "India",
        "latitude": 18.9389,
        "longitude": 72.8258,
        "elevation_m": 14.0,
        "boundary_straight_m": 72.0,
        "boundary_square_off_m": 65.0,
        "boundary_square_leg_m": 64.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 63.0,
        "boundary_avg_m": 65.2,
        "pitch_soil_type": "Red Soil",
        "pitch_behavior": "Pace & True Bounce",
        "grass_coverage": "Light Grass",
        "aliases": ["wankhede stadium", "wankhede stadium, mumbai"]
    },
    {
        "venue_id": "IND_BLR_CHINNASWAMY",
        "canonical_name": "M. Chinnaswamy Stadium",
        "city": "Bengaluru",
        "country": "India",
        "latitude": 12.9788,
        "longitude": 77.5996,
        "elevation_m": 920.0,
        "boundary_straight_m": 68.0,
        "boundary_square_off_m": 58.0,
        "boundary_square_leg_m": 58.0,
        "boundary_fine_leg_m": 56.0,
        "boundary_third_man_m": 56.0,
        "boundary_avg_m": 59.2,
        "pitch_soil_type": "Clay / Sand Sub-base",
        "pitch_behavior": "Batting Paradise",
        "grass_coverage": "Moderate Grass",
        "aliases": ["m chinnaswamy stadium", "m. chinnaswamy stadium", "m.chinnaswamy stadium", "m chinnaswamy stadium, bengaluru"]
    },
    {
        "venue_id": "IND_KOL_EDEN_GARDENS",
        "canonical_name": "Eden Gardens",
        "city": "Kolkata",
        "country": "India",
        "latitude": 22.5646,
        "longitude": 88.3433,
        "elevation_m": 11.0,
        "boundary_straight_m": 74.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 65.0,
        "boundary_third_man_m": 65.0,
        "boundary_avg_m": 68.0,
        "pitch_soil_type": "Black Soil / Gangetic Silt",
        "pitch_behavior": "Balanced / True Pace",
        "grass_coverage": "Moderate Grass",
        "aliases": ["eden gardens", "eden gardens, kolkata"]
    },
    {
        "venue_id": "IND_CHE_CHEPAUK",
        "canonical_name": "MA Chidambaram Stadium, Chepauk",
        "city": "Chennai",
        "country": "India",
        "latitude": 13.0628,
        "longitude": 80.2793,
        "elevation_m": 9.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 64.0,
        "boundary_third_man_m": 64.0,
        "boundary_avg_m": 66.8,
        "pitch_soil_type": "Black Soil / Clay",
        "pitch_behavior": "Spin & Grip",
        "grass_coverage": "Shaved / Bare",
        "aliases": ["ma chidambaram stadium", "ma chidambaram stadium, chepauk", "ma chidambaram stadium, chepauk, chennai"]
    },
    {
        "venue_id": "IND_DEL_ARUN_JAITLEY",
        "canonical_name": "Arun Jaitley Stadium",
        "city": "Delhi",
        "country": "India",
        "latitude": 28.6378,
        "longitude": 77.2431,
        "elevation_m": 215.0,
        "boundary_straight_m": 66.0,
        "boundary_square_off_m": 62.0,
        "boundary_square_leg_m": 62.0,
        "boundary_fine_leg_m": 58.0,
        "boundary_third_man_m": 58.0,
        "boundary_avg_m": 61.2,
        "pitch_soil_type": "Black Soil",
        "pitch_behavior": "Batting Paradise / Two-Paced",
        "grass_coverage": "Light Grass",
        "aliases": ["feroz shah kotla", "arun jaitley stadium", "arun jaitley stadium, delhi"]
    },
    {
        "venue_id": "IND_HYD_UPPAL",
        "canonical_name": "Rajiv Gandhi International Stadium, Uppal",
        "city": "Hyderabad",
        "country": "India",
        "latitude": 17.4065,
        "longitude": 78.5505,
        "elevation_m": 505.0,
        "boundary_straight_m": 71.0,
        "boundary_square_off_m": 66.0,
        "boundary_square_leg_m": 66.0,
        "boundary_fine_leg_m": 63.0,
        "boundary_third_man_m": 63.0,
        "boundary_avg_m": 65.8,
        "pitch_soil_type": "Black / Red Mixed Soil",
        "pitch_behavior": "True Bounce / High Scoring",
        "grass_coverage": "Light Grass",
        "aliases": ["rajiv gandhi international stadium", "rajiv gandhi international stadium, uppal", "rajiv gandhi international stadium, uppal, hyderabad"]
    },
    {
        "venue_id": "IND_AHM_MOTERA",
        "canonical_name": "Narendra Modi Stadium",
        "city": "Ahmedabad",
        "country": "India",
        "latitude": 23.0917,
        "longitude": 72.5972,
        "elevation_m": 55.0,
        "boundary_straight_m": 75.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 65.0,
        "boundary_third_man_m": 65.0,
        "boundary_avg_m": 68.2,
        "pitch_soil_type": "Dual (Red Soil & Black Soil Strips)",
        "pitch_behavior": "Variable (Red: Bounce / Black: Turn)",
        "grass_coverage": "Moderate Grass",
        "aliases": ["narendra modi stadium, ahmedabad", "sardar patel stadium, motera"]
    },
    {
        "venue_id": "IND_JAI_SMS",
        "canonical_name": "Sawai Mansingh Stadium",
        "city": "Jaipur",
        "country": "India",
        "latitude": 26.8940,
        "longitude": 75.8032,
        "elevation_m": 431.0,
        "boundary_straight_m": 75.0,
        "boundary_square_off_m": 70.0,
        "boundary_square_leg_m": 70.0,
        "boundary_fine_leg_m": 66.0,
        "boundary_third_man_m": 66.0,
        "boundary_avg_m": 69.4,
        "pitch_soil_type": "Clay / Sandy Loam",
        "pitch_behavior": "Balanced / True Bounce",
        "grass_coverage": "Light Grass",
        "aliases": ["sawai mansingh stadium", "sawai mansingh stadium, jaipur"]
    },
    {
        "venue_id": "IND_MOH_BINDRA",
        "canonical_name": "Punjab Cricket Association IS Bindra Stadium",
        "city": "Mohali",
        "country": "India",
        "latitude": 30.6908,
        "longitude": 76.7374,
        "elevation_m": 316.0,
        "boundary_straight_m": 74.0,
        "boundary_square_off_m": 72.0,
        "boundary_square_leg_m": 71.0,
        "boundary_fine_leg_m": 66.0,
        "boundary_third_man_m": 66.0,
        "boundary_avg_m": 69.8,
        "pitch_soil_type": "Clay Loam",
        "pitch_behavior": "Pace & Seam Movement",
        "grass_coverage": "Moderate Grass",
        "aliases": ["punjab cricket association stadium, mohali", "punjab cricket association is bindra stadium, mohali", "punjab cricket association is bindra stadium"]
    },
    {
        "venue_id": "IND_DHA_HPCA",
        "canonical_name": "Himachal Pradesh Cricket Association Stadium",
        "city": "Dharamsala",
        "country": "India",
        "latitude": 32.1976,
        "longitude": 76.3260,
        "elevation_m": 1457.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 65.0,
        "boundary_square_leg_m": 65.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 62.0,
        "boundary_avg_m": 64.8,
        "pitch_soil_type": "Cold Climate Loam / Ryegrass",
        "pitch_behavior": "Pace, Swing & Extreme Seam",
        "grass_coverage": "Heavy Grass",
        "aliases": ["himachal pradesh cricket association stadium", "himachal pradesh cricket association stadium, dharamsala"]
    },
    {
        "venue_id": "IND_LKO_EKANA",
        "canonical_name": "BRSABV Ekana Cricket Stadium",
        "city": "Lucknow",
        "country": "India",
        "latitude": 26.7909,
        "longitude": 81.0142,
        "elevation_m": 123.0,
        "boundary_straight_m": 74.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 64.0,
        "boundary_third_man_m": 64.0,
        "boundary_avg_m": 67.6,
        "pitch_soil_type": "Dual (Black Soil & Red Soil)",
        "pitch_behavior": "Two-Paced / Spin on Black; Fast on Red",
        "grass_coverage": "Light Grass",
        "aliases": ["bharat ratna shri atal bihari vajpayee ekana cricket stadium, lucknow", "ekana cricket stadium"]
    },
    {
        "venue_id": "IND_PUN_MCA",
        "canonical_name": "Maharashtra Cricket Association Stadium",
        "city": "Pune",
        "country": "India",
        "latitude": 18.6745,
        "longitude": 73.7065,
        "elevation_m": 560.0,
        "boundary_straight_m": 73.0,
        "boundary_square_off_m": 67.0,
        "boundary_square_leg_m": 67.0,
        "boundary_fine_leg_m": 64.0,
        "boundary_third_man_m": 64.0,
        "boundary_avg_m": 67.0,
        "pitch_soil_type": "Black Cotton Soil",
        "pitch_behavior": "True Bounce & High Scoring",
        "grass_coverage": "Light Grass",
        "aliases": ["maharashtra cricket association stadium", "maharashtra cricket association stadium, pune", "subrata roy sahara stadium"]
    },
    {
        "venue_id": "IND_MUM_BRABOURNE",
        "canonical_name": "Brabourne Stadium",
        "city": "Mumbai",
        "country": "India",
        "latitude": 18.9322,
        "longitude": 72.8236,
        "elevation_m": 11.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 64.0,
        "boundary_square_leg_m": 64.0,
        "boundary_fine_leg_m": 60.0,
        "boundary_third_man_m": 60.0,
        "boundary_avg_m": 63.6,
        "pitch_soil_type": "Red Soil",
        "pitch_behavior": "High Bounce & Fast Outfield",
        "grass_coverage": "Light Grass",
        "aliases": ["brabourne stadium", "brabourne stadium, mumbai"]
    },
    {
        "venue_id": "IND_MUM_DYPATIL",
        "canonical_name": "Dr DY Patil Sports Academy",
        "city": "Navi Mumbai",
        "country": "India",
        "latitude": 19.0436,
        "longitude": 73.0259,
        "elevation_m": 12.0,
        "boundary_straight_m": 72.0,
        "boundary_square_off_m": 66.0,
        "boundary_square_leg_m": 66.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 62.0,
        "boundary_avg_m": 65.6,
        "pitch_soil_type": "Red Soil",
        "pitch_behavior": "True Bounce",
        "grass_coverage": "Moderate Grass",
        "aliases": ["dr dy patil sports academy", "dr dy patil sports academy, mumbai"]
    },
    {
        "venue_id": "IND_VIZ_ACAVDCA",
        "canonical_name": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
        "city": "Visakhapatnam",
        "country": "India",
        "latitude": 17.7972,
        "longitude": 83.3541,
        "elevation_m": 22.0,
        "boundary_straight_m": 71.0,
        "boundary_square_off_m": 65.0,
        "boundary_square_leg_m": 65.0,
        "boundary_fine_leg_m": 61.0,
        "boundary_third_man_m": 61.0,
        "boundary_avg_m": 64.6,
        "pitch_soil_type": "Clay Loam",
        "pitch_behavior": "Batting Paradise / True Bounce",
        "grass_coverage": "Moderate Grass",
        "aliases": ["dr. y.s. rajasekhara reddy aca-vdca cricket stadium", "dr. y.s. rajasekhara reddy aca-vdca cricket stadium, visakhapatnam"]
    },
    {
        "venue_id": "IND_IND_HOLKAR",
        "canonical_name": "Holkar Cricket Stadium",
        "city": "Indore",
        "country": "India",
        "latitude": 22.7247,
        "longitude": 75.8753,
        "elevation_m": 553.0,
        "boundary_straight_m": 68.0,
        "boundary_square_off_m": 60.0,
        "boundary_square_leg_m": 60.0,
        "boundary_fine_leg_m": 56.0,
        "boundary_third_man_m": 56.0,
        "boundary_avg_m": 60.0,
        "pitch_soil_type": "Red Soil / Clay",
        "pitch_behavior": "Batting Paradise / Short Boundaries",
        "grass_coverage": "Light Grass",
        "aliases": ["holkar cricket stadium"]
    },
    {
        "venue_id": "IND_MUL_YADAVINDRA",
        "canonical_name": "Maharaja Yadavindra Singh International Cricket Stadium",
        "city": "Mullanpur",
        "country": "India",
        "latitude": 30.7937,
        "longitude": 76.7329,
        "elevation_m": 320.0,
        "boundary_straight_m": 73.0,
        "boundary_square_off_m": 67.0,
        "boundary_square_leg_m": 67.0,
        "boundary_fine_leg_m": 63.0,
        "boundary_third_man_m": 63.0,
        "boundary_avg_m": 66.6,
        "pitch_soil_type": "Clay Loam",
        "pitch_behavior": "Good Pace & Seam",
        "grass_coverage": "Moderate Grass",
        "aliases": ["maharaja yadavindra singh international cricket stadium, mullanpur", "maharaja yadavindra singh international cricket stadium, new chandigarh"]
    },
    {
        "venue_id": "IND_GUW_BARSAPARA",
        "canonical_name": "Barsapara Cricket Stadium",
        "city": "Guwahati",
        "country": "India",
        "latitude": 26.1417,
        "longitude": 91.7369,
        "elevation_m": 54.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 64.0,
        "boundary_square_leg_m": 64.0,
        "boundary_fine_leg_m": 60.0,
        "boundary_third_man_m": 60.0,
        "boundary_avg_m": 63.6,
        "pitch_soil_type": "Clay / Alluvial Soil",
        "pitch_behavior": "Batting Paradise / High Scoring",
        "grass_coverage": "Light Grass",
        "aliases": ["barsapara cricket stadium, guwahati", "barsapara cricket stadium"]
    },
    {
        "venue_id": "IND_RAJ_SCA",
        "canonical_name": "Saurashtra Cricket Association Stadium",
        "city": "Rajkot",
        "country": "India",
        "latitude": 22.3619,
        "longitude": 70.7061,
        "elevation_m": 138.0,
        "boundary_straight_m": 73.0,
        "boundary_square_off_m": 66.0,
        "boundary_square_leg_m": 66.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 62.0,
        "boundary_avg_m": 65.8,
        "pitch_soil_type": "Black Soil",
        "pitch_behavior": "Flat / Batting Paradise",
        "grass_coverage": "Light Grass",
        "aliases": ["saurashtra cricket association stadium", "saurashtra cricket association stadium, rajkot", "niranjan shah stadium"]
    },

    # --- UAE STADIUMS (HEAVY IPL & T20I USAGE) ---
    {
        "venue_id": "UAE_DXB_DIC",
        "canonical_name": "Dubai International Cricket Stadium",
        "city": "Dubai",
        "country": "United Arab Emirates",
        "latitude": 25.0454,
        "longitude": 55.2185,
        "elevation_m": 10.0,
        "boundary_straight_m": 76.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 65.0,
        "boundary_third_man_m": 65.0,
        "boundary_avg_m": 68.4,
        "pitch_soil_type": "Imported Clay / Sand Sub-base",
        "pitch_behavior": "Balanced / Moderate Pace & Dew",
        "grass_coverage": "Light Grass",
        "aliases": ["dubai international cricket stadium", "dubai international cricket stadium, dubai"]
    },
    {
        "venue_id": "UAE_SHJ_SCS",
        "canonical_name": "Sharjah Cricket Stadium",
        "city": "Sharjah",
        "country": "United Arab Emirates",
        "latitude": 25.3297,
        "longitude": 55.4208,
        "elevation_m": 12.0,
        "boundary_straight_m": 65.0,
        "boundary_square_off_m": 58.0,
        "boundary_square_leg_m": 58.0,
        "boundary_fine_leg_m": 56.0,
        "boundary_third_man_m": 56.0,
        "boundary_avg_m": 58.6,
        "pitch_soil_type": "Clay / Sandy Loam",
        "pitch_behavior": "Batting Paradise / Short Boundaries",
        "grass_coverage": "Dry / Shaved",
        "aliases": ["sharjah cricket stadium", "sharjah cricket stadium, sharjah"]
    },
    {
        "venue_id": "UAE_ABU_SZS",
        "canonical_name": "Sheikh Zayed Stadium",
        "city": "Abu Dhabi",
        "country": "United Arab Emirates",
        "latitude": 24.3989,
        "longitude": 54.5492,
        "elevation_m": 15.0,
        "boundary_straight_m": 78.0,
        "boundary_square_off_m": 70.0,
        "boundary_square_leg_m": 70.0,
        "boundary_fine_leg_m": 66.0,
        "boundary_third_man_m": 66.0,
        "boundary_avg_m": 70.0,
        "pitch_soil_type": "Clay / Sand",
        "pitch_behavior": "Balanced / Large Dimensions",
        "grass_coverage": "Moderate Grass",
        "aliases": ["sheikh zayed stadium", "zayed cricket stadium, abu dhabi", "sheikh zayed stadium, abu dhabi"]
    },

    # --- SOUTH AFRICA (HIGH ALTITUDE & COASTAL) ---
    {
        "venue_id": "RSA_JHB_WANDERERS",
        "canonical_name": "New Wanderers Stadium",
        "city": "Johannesburg",
        "country": "South Africa",
        "latitude": -26.1317,
        "longitude": 28.0583,
        "elevation_m": 1720.0,
        "boundary_straight_m": 74.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 65.0,
        "boundary_third_man_m": 65.0,
        "boundary_avg_m": 68.0,
        "pitch_soil_type": "Bulli Soil / Kikuyu Grass",
        "pitch_behavior": "High Pace & Bounce / Extreme Six-Hitting",
        "grass_coverage": "Moderate Grass",
        "aliases": ["new wanderers stadium", "wanderers stadium", "the wanderers stadium, johannesburg"]
    },
    {
        "venue_id": "RSA_CEN_SUPERSPORT",
        "canonical_name": "SuperSport Park",
        "city": "Centurion",
        "country": "South Africa",
        "latitude": -25.8594,
        "longitude": 28.1969,
        "elevation_m": 1440.0,
        "boundary_straight_m": 75.0,
        "boundary_square_off_m": 69.0,
        "boundary_square_leg_m": 69.0,
        "boundary_fine_leg_m": 65.0,
        "boundary_third_man_m": 65.0,
        "boundary_avg_m": 68.6,
        "pitch_soil_type": "Bulli Clay / Kikuyu Grass",
        "pitch_behavior": "Fast & Bouncy / High Altitude",
        "grass_coverage": "Moderate Grass",
        "aliases": ["supersport park", "supersport park, centurion"]
    },
    {
        "venue_id": "RSA_DUR_KINGSMEAD",
        "canonical_name": "Kingsmead",
        "city": "Durban",
        "country": "South Africa",
        "latitude": -29.8517,
        "longitude": 31.0289,
        "elevation_m": 10.0,
        "boundary_straight_m": 74.0,
        "boundary_square_off_m": 67.0,
        "boundary_square_leg_m": 67.0,
        "boundary_fine_leg_m": 63.0,
        "boundary_third_man_m": 63.0,
        "boundary_avg_m": 66.8,
        "pitch_soil_type": "Coastal Clay / Kikuyu Grass",
        "pitch_behavior": "Early Swing & Seam / Humid Breeze",
        "grass_coverage": "Moderate Grass",
        "aliases": ["kingsmead", "kingsmead, durban"]
    },
    {
        "venue_id": "RSA_CPT_NEWLANDS",
        "canonical_name": "Newlands",
        "city": "Cape Town",
        "country": "South Africa",
        "latitude": -33.9706,
        "longitude": 18.4683,
        "elevation_m": 18.0,
        "boundary_straight_m": 72.0,
        "boundary_square_off_m": 66.0,
        "boundary_square_leg_m": 66.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 62.0,
        "boundary_avg_m": 65.6,
        "pitch_soil_type": "Clay / Kikuyu Grass",
        "pitch_behavior": "Seam & Swing / Mountain Wind",
        "grass_coverage": "Moderate Grass",
        "aliases": ["newlands", "newlands, cape town"]
    },

    # --- AUSTRALIA ---
    {
        "venue_id": "AUS_MEL_MCG",
        "canonical_name": "Melbourne Cricket Ground",
        "city": "Melbourne",
        "country": "Australia",
        "latitude": -37.8200,
        "longitude": 144.9834,
        "elevation_m": 25.0,
        "boundary_straight_m": 84.0,
        "boundary_square_off_m": 76.0,
        "boundary_square_leg_m": 76.0,
        "boundary_fine_leg_m": 72.0,
        "boundary_third_man_m": 72.0,
        "boundary_avg_m": 76.0,
        "pitch_soil_type": "Drop-in Merri Creek Black Clay",
        "pitch_behavior": "True Bounce / Huge Outfield",
        "grass_coverage": "Light Grass",
        "aliases": ["melbourne cricket ground", "mcg"]
    },
    {
        "venue_id": "AUS_SYD_SCG",
        "canonical_name": "Sydney Cricket Ground",
        "city": "Sydney",
        "country": "Australia",
        "latitude": -33.8917,
        "longitude": 151.2247,
        "elevation_m": 38.0,
        "boundary_straight_m": 76.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 64.0,
        "boundary_third_man_m": 64.0,
        "boundary_avg_m": 68.0,
        "pitch_soil_type": "Bulli Soil / Couch Grass",
        "pitch_behavior": "Turn & Bounce",
        "grass_coverage": "Light Grass",
        "aliases": ["sydney cricket ground", "scg"]
    },
    {
        "venue_id": "AUS_ADE_OVAL",
        "canonical_name": "Adelaide Oval",
        "city": "Adelaide",
        "country": "Australia",
        "latitude": -34.9156,
        "longitude": 138.5961,
        "elevation_m": 28.0,
        "boundary_straight_m": 82.0,
        "boundary_square_off_m": 62.0,
        "boundary_square_leg_m": 62.0,
        "boundary_fine_leg_m": 60.0,
        "boundary_third_man_m": 60.0,
        "boundary_avg_m": 65.2,
        "pitch_soil_type": "Drop-in Clay / Rye Grass",
        "pitch_behavior": "Long Straight / Short Square / True Bounce",
        "grass_coverage": "Moderate Grass",
        "aliases": ["adelaide oval"]
    },
    {
        "venue_id": "AUS_BRI_GABBA",
        "canonical_name": "Brisbane Cricket Ground, Woolloongabba",
        "city": "Brisbane",
        "country": "Australia",
        "latitude": -27.4858,
        "longitude": 153.0381,
        "elevation_m": 15.0,
        "boundary_straight_m": 78.0,
        "boundary_square_off_m": 72.0,
        "boundary_square_leg_m": 72.0,
        "boundary_fine_leg_m": 68.0,
        "boundary_third_man_m": 68.0,
        "boundary_avg_m": 71.6,
        "pitch_soil_type": "Acland Bulli Clay",
        "pitch_behavior": "High Pace & Steep Bounce",
        "grass_coverage": "Moderate Grass",
        "aliases": ["brisbane cricket ground, woolloongabba", "the gabba", "gabba"]
    },
    {
        "venue_id": "AUS_PER_OPTUS",
        "canonical_name": "Perth Stadium",
        "city": "Perth",
        "country": "Australia",
        "latitude": -31.9511,
        "longitude": 115.8894,
        "elevation_m": 10.0,
        "boundary_straight_m": 78.0,
        "boundary_square_off_m": 71.0,
        "boundary_square_leg_m": 71.0,
        "boundary_fine_leg_m": 67.0,
        "boundary_third_man_m": 67.0,
        "boundary_avg_m": 70.8,
        "pitch_soil_type": "Drop-in Clay / Couch Grass",
        "pitch_behavior": "Fastest & Bounciest Pitch in World",
        "grass_coverage": "Moderate Grass",
        "aliases": ["perth stadium", "optus stadium"]
    },

    # --- ENGLAND ---
    {
        "venue_id": "ENG_LON_LORDS",
        "canonical_name": "Lord's",
        "city": "London",
        "country": "England",
        "latitude": 51.5298,
        "longitude": -0.1726,
        "elevation_m": 35.0,
        "boundary_straight_m": 74.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 64.0,
        "boundary_third_man_m": 64.0,
        "boundary_avg_m": 67.6,
        "pitch_soil_type": "Ongar Clay Loam / Ryegrass",
        "pitch_behavior": "Natural Slope / Seam & Swing",
        "grass_coverage": "Heavy Grass",
        "aliases": ["lord's", "lord's, london"]
    },
    {
        "venue_id": "ENG_LON_OVAL",
        "canonical_name": "The Oval",
        "city": "London",
        "country": "England",
        "latitude": 51.4837,
        "longitude": -0.1150,
        "elevation_m": 8.0,
        "boundary_straight_m": 75.0,
        "boundary_square_off_m": 69.0,
        "boundary_square_leg_m": 69.0,
        "boundary_fine_leg_m": 65.0,
        "boundary_third_man_m": 65.0,
        "boundary_avg_m": 68.6,
        "pitch_soil_type": "Surrey Loam",
        "pitch_behavior": "True Pace & Good Bounce",
        "grass_coverage": "Moderate Grass",
        "aliases": ["the oval", "kennington oval", "the oval, london"]
    },
    {
        "venue_id": "ENG_NOT_TRENT_BRIDGE",
        "canonical_name": "Trent Bridge",
        "city": "Nottingham",
        "country": "England",
        "latitude": 52.9369,
        "longitude": -1.1322,
        "elevation_m": 24.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 63.0,
        "boundary_square_leg_m": 63.0,
        "boundary_fine_leg_m": 59.0,
        "boundary_third_man_m": 59.0,
        "boundary_avg_m": 62.8,
        "pitch_soil_type": "Boughton Loam",
        "pitch_behavior": "Extreme Swing & Batting Paradise",
        "grass_coverage": "Moderate Grass",
        "aliases": ["trent bridge", "trent bridge, nottingham"]
    },
    {
        "venue_id": "ENG_BIR_EDGBASTON",
        "canonical_name": "Edgbaston",
        "city": "Birmingham",
        "country": "England",
        "latitude": 52.4558,
        "longitude": -1.9028,
        "elevation_m": 120.0,
        "boundary_straight_m": 72.0,
        "boundary_square_off_m": 65.0,
        "boundary_square_leg_m": 65.0,
        "boundary_fine_leg_m": 61.0,
        "boundary_third_man_m": 61.0,
        "boundary_avg_m": 64.8,
        "pitch_soil_type": "Banbury Clay Loam",
        "pitch_behavior": "True Bounce & High Scoring",
        "grass_coverage": "Moderate Grass",
        "aliases": ["edgbaston", "edgbaston, birmingham"]
    },

    # --- HIGH ALTITUDE ASSOCIATE / INTERNATIONAL HUBS ---
    {
        "venue_id": "ZIM_HAR_HSC",
        "canonical_name": "Harare Sports Club",
        "city": "Harare",
        "country": "Zimbabwe",
        "latitude": -17.8181,
        "longitude": 31.0544,
        "elevation_m": 1483.0,
        "boundary_straight_m": 74.0,
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 64.0,
        "boundary_third_man_m": 64.0,
        "boundary_avg_m": 67.6,
        "pitch_soil_type": "Red Clay Loam",
        "pitch_behavior": "High Altitude / Fast Bounce",
        "grass_coverage": "Moderate Grass",
        "aliases": ["harare sports club"]
    },
    {
        "venue_id": "NEP_KIR_TU",
        "canonical_name": "Tribhuvan University International Cricket Ground",
        "city": "Kirtipur",
        "country": "Nepal",
        "latitude": 27.6794,
        "longitude": 85.2831,
        "elevation_m": 1330.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 64.0,
        "boundary_square_leg_m": 64.0,
        "boundary_fine_leg_m": 60.0,
        "boundary_third_man_m": 60.0,
        "boundary_avg_m": 63.6,
        "pitch_soil_type": "Alluvial Valley Clay",
        "pitch_behavior": "High Altitude / Spin Later",
        "grass_coverage": "Light Grass",
        "aliases": ["tribhuvan university international cricket ground, kirtipur", "tribhuvan university ground"]
    },
    {
        "venue_id": "RWA_KIG_GAHANGA",
        "canonical_name": "Gahanga International Cricket Stadium",
        "city": "Kigali",
        "country": "Rwanda",
        "latitude": -2.0238,
        "longitude": 30.1084,
        "elevation_m": 1490.0,
        "boundary_straight_m": 68.0,
        "boundary_square_off_m": 62.0,
        "boundary_square_leg_m": 62.0,
        "boundary_fine_leg_m": 58.0,
        "boundary_third_man_m": 58.0,
        "boundary_avg_m": 61.6,
        "pitch_soil_type": "Laterite Red Clay",
        "pitch_behavior": "High Altitude / Quick Bounce",
        "grass_coverage": "Light Grass",
        "aliases": ["gahanga international cricket stadium, rwanda", "gahanga international cricket stadium. rwanda", "gahanga b ground, rwanda"]
    },
    {
        "venue_id": "MAS_KUL_BAYUEMAS",
        "canonical_name": "Bayuemas Oval",
        "city": "Kuala Lumpur",
        "country": "Malaysia",
        "latitude": 2.9904,
        "longitude": 101.4429,
        "elevation_m": 15.0,
        "boundary_straight_m": 67.0,
        "boundary_square_off_m": 61.0,
        "boundary_square_leg_m": 61.0,
        "boundary_fine_leg_m": 58.0,
        "boundary_third_man_m": 58.0,
        "boundary_avg_m": 61.0,
        "pitch_soil_type": "Tropical Clay Loam",
        "pitch_behavior": "Tropical Humidity / Slow Turner",
        "grass_coverage": "Moderate Grass",
        "aliases": ["bayuemas oval, kuala lumpur", "bayuemas oval"]
    },
    {
        "venue_id": "OMA_ALA_TURF1",
        "canonical_name": "Al Amerat Cricket Ground (Ministry Turf 1)",
        "city": "Al Amarat",
        "country": "Oman",
        "latitude": 23.4912,
        "longitude": 58.4617,
        "elevation_m": 220.0,
        "boundary_straight_m": 72.0,
        "boundary_square_off_m": 66.0,
        "boundary_square_leg_m": 66.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 62.0,
        "boundary_avg_m": 65.6,
        "pitch_soil_type": "Imported Clay / Desert Silt",
        "pitch_behavior": "True Bounce / Evening Dew",
        "grass_coverage": "Light Grass",
        "aliases": ["al amerat cricket ground oman cricket (ministry turf 1)", "al amerat cricket ground oman cricket (ministry turf 2)"]
    },

    # --- SRI LANKA, BANGLADESH, WEST INDIES, NEW ZEALAND ---
    {
        "venue_id": "SRI_COL_PREMADASA",
        "canonical_name": "R. Premadasa Stadium",
        "city": "Colombo",
        "country": "Sri Lanka",
        "latitude": 6.9397,
        "longitude": 79.8718,
        "elevation_m": 7.0,
        "boundary_straight_m": 72.0,
        "boundary_square_off_m": 66.0,
        "boundary_square_leg_m": 66.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 62.0,
        "boundary_avg_m": 65.6,
        "pitch_soil_type": "Coastal Alluvial Clay",
        "pitch_behavior": "Spin & Grip / Slows Down",
        "grass_coverage": "Shaved / Bare",
        "aliases": ["r premadassa stadium", "r.premadasa stadium", "r. premadasa stadium, khettarama", "r premadasa stadium, colombo"]
    },
    {
        "venue_id": "BAN_DHA_MIRPUR",
        "canonical_name": "Sher-e-Bangla National Cricket Stadium",
        "city": "Dhaka",
        "country": "Bangladesh",
        "latitude": 23.8069,
        "longitude": 90.3639,
        "elevation_m": 12.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 65.0,
        "boundary_square_leg_m": 65.0,
        "boundary_fine_leg_m": 61.0,
        "boundary_third_man_m": 61.0,
        "boundary_avg_m": 64.4,
        "pitch_soil_type": "Gangetic Clay / Silt",
        "pitch_behavior": "Low Bounce & Extreme Turn",
        "grass_coverage": "Shaved / Bare",
        "aliases": ["sher-e-bangla national cricket stadium", "sher-e-bangla national cricket stadium, mirpur"]
    },
    {
        "venue_id": "WI_BAR_KENSINGTON",
        "canonical_name": "Kensington Oval",
        "city": "Bridgetown",
        "country": "Barbados",
        "latitude": 13.1042,
        "longitude": -59.6231,
        "elevation_m": 16.0,
        "boundary_straight_m": 73.0,
        "boundary_square_off_m": 67.0,
        "boundary_square_leg_m": 67.0,
        "boundary_fine_leg_m": 63.0,
        "boundary_third_man_m": 63.0,
        "boundary_avg_m": 66.6,
        "pitch_soil_type": "Limestone Clay Loam",
        "pitch_behavior": "Pace & Carry / Caribbean Trade Winds",
        "grass_coverage": "Moderate Grass",
        "aliases": ["kensington oval, bridgetown, barbados", "kensington oval, bridgetown", "kensington oval"]
    },
    {
        "venue_id": "NZ_AUC_EDEN_PARK",
        "canonical_name": "Eden Park",
        "city": "Auckland",
        "country": "New Zealand",
        "latitude": -36.8753,
        "longitude": 174.7447,
        "elevation_m": 42.0,
        "boundary_straight_m": 55.0,  # Iconic short straight boundaries!
        "boundary_square_off_m": 68.0,
        "boundary_square_leg_m": 68.0,
        "boundary_fine_leg_m": 58.0,
        "boundary_third_man_m": 58.0,
        "boundary_avg_m": 61.4,
        "pitch_soil_type": "Drop-in Waikato Clay / Rye Grass",
        "pitch_behavior": "Extreme Short Straight / Seam & Swing",
        "grass_coverage": "Heavy Grass",
        "aliases": ["eden park", "eden park, auckland"]
    }
]

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())

def build_venue_lookup():
    """Builds a fast lookup dictionary mapping normalized names and aliases to curated venue dict."""
    lookup = {}
    for v in CURATED_VENUES:
        canonical_norm = normalize_text(v["canonical_name"])
        lookup[canonical_norm] = v
        for alias in v.get("aliases", []):
            lookup[normalize_text(alias)] = v
    return lookup

def fetch_elevation_openmeteo(lat: float, lon: float) -> float:
    """Queries Open-Meteo elevation API for exact ground elevation."""
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        req = urllib.request.Request(url, headers={"User-Agent": "CricketBenchmark/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return float(data.get("elevation", [0])[0])
    except Exception as e:
        logging.warning(f"Failed to fetch elevation for ({lat}, {lon}): {e}")
        return 50.0  # safe default

def match_or_create_venue(raw_venue: str, raw_city: str, lookup: dict, dynamic_cache: dict) -> dict:
    norm_v = normalize_text(raw_venue)
    if norm_v in lookup:
        return lookup[norm_v]
    
    # Check partial matching
    for key, venue_data in lookup.items():
        if key in norm_v or norm_v in key:
            return venue_data
        # Match core words (e.g. 'wankhede' in norm_v)
        core_words = [w for w in key.split() if len(w) > 4 and w not in ["stadium", "international", "cricket", "ground"]]
        if core_words and any(w in norm_v for w in core_words):
            return venue_data
            
    # Check dynamic cache for previously resolved uncurated venues
    cache_key = f"{raw_venue}___{raw_city}"
    if cache_key in dynamic_cache:
        return dynamic_cache[cache_key]

    # Fallback default estimation for associate/smaller venues
    clean_name = raw_venue.split(",")[0].strip()
    safe_city = raw_city if raw_city else "International Ground"
    vid = "INT_" + re.sub(r"[^A-Z0-9]", "", clean_name.upper())[:15]
    
    # Default estimated standard dimensions
    new_venue = {
        "venue_id": vid,
        "canonical_name": raw_venue,
        "city": safe_city,
        "country": "International",
        "latitude": 20.0,  # approximate default
        "longitude": 75.0,
        "elevation_m": 50.0,
        "boundary_straight_m": 70.0,
        "boundary_square_off_m": 65.0,
        "boundary_square_leg_m": 65.0,
        "boundary_fine_leg_m": 62.0,
        "boundary_third_man_m": 62.0,
        "boundary_avg_m": 64.8,
        "pitch_soil_type": "Standard Clay Loam",
        "pitch_behavior": "Balanced / Standard",
        "grass_coverage": "Moderate Grass",
        "aliases": [norm_v]
    }
    dynamic_cache[cache_key] = new_venue
    return new_venue

def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    lookup = build_venue_lookup()
    cache_path = os.path.join(CACHE_DIR, "dynamic_venues_cache.json")
    dynamic_cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            dynamic_cache = json.load(f)

    logging.info(f"Loaded {len(CURATED_VENUES)} curated master stadiums with ground-truth dimensions.")
    
    # Extract unique venues from all matches
    all_json_files = []
    if os.path.exists(RAW_IPL):
        all_json_files.extend([os.path.join(RAW_IPL, f) for f in os.listdir(RAW_IPL) if f.endswith(".json")])
    if os.path.exists(RAW_T20S):
        all_json_files.extend([os.path.join(RAW_T20S, f) for f in os.listdir(RAW_T20S) if f.endswith(".json")])
        
    logging.info(f"Scanning venues across {len(all_json_files)} match files...")
    
    seen_venues = {}
    for fpath in all_json_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                info = data.get("info", {})
                v_name = info.get("venue", "Unknown Venue")
                c_name = info.get("city", "")
                
                matched = match_or_create_venue(v_name, c_name, lookup, dynamic_cache)
                vid = matched["venue_id"]
                if vid not in seen_venues:
                    seen_venues[vid] = matched
        except Exception:
            continue
            
    # Save dynamic cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dynamic_cache, f, indent=2)
        
    # Convert seen venues to DataFrame
    venues_list = list(seen_venues.values())
    df_venues = pd.DataFrame(venues_list)
    # Exclude aliases column from clean CSV export
    if "aliases" in df_venues.columns:
        df_venues = df_venues.drop(columns=["aliases"])
        
    output_csv = os.path.join(PROCESSED_DIR, "venues_master.csv")
    df_venues.to_csv(output_csv, index=False)
    logging.info(f"Successfully generated venues master database: {output_csv}")
    logging.info(f"Total unique venues cataloged: {len(df_venues)}")
    logging.info("Sample catalog preview:\n" + str(df_venues[["venue_id", "canonical_name", "city", "elevation_m", "boundary_avg_m", "pitch_soil_type"]].head(8)))

if __name__ == "__main__":
    main()
