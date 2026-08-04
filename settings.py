from __future__ import annotations

import os


# ============================================================
# BASIC PROJECT SETTINGS
# ============================================================

PROJECT_NAME = "South Africa Business Risk Desk"

# During testing, the engine writes to a separate file.
# This protects the live website data in briefing.json.
OUTPUT_FILE = "data/briefing_test.json"

# The website will eventually update at 06:00 UK time.
TIMEZONE = "Europe/London"

# Maximum time the program waits for a website to respond.
REQUEST_TIMEOUT_SECONDS = 20

# Identifies the project when requesting information from websites.
USER_AGENT = (
    "South-Africa-Business-Risk-Desk/0.1 "
    "(educational business-risk monitoring project)"
)


# ============================================================
# COLLECTION LIMITS
# ============================================================

# Maximum number of stories collected from each feed or search.
MAX_ITEMS_PER_FEED = 15

# Ordinary news older than this will normally be removed.
MAX_ITEM_AGE_DAYS = 5


# ============================================================
# OPTIONAL TRAFFIC API
# ============================================================

# The i-TRAFFIC collector requires an API key.
# The program will continue safely when no key is available.
ITRAFFIC_API_KEY = os.getenv("ITRAFFIC_API_KEY", "").strip()


# ============================================================
# NATIONAL NEWS SEARCHES
# ============================================================

NATIONAL_QUERIES = [
    "South Africa business risk",
    "South Africa political risk business",
    "South Africa protest OR strike OR demonstration",
    "South Africa road closure OR transport disruption",
    "South Africa electricity OR power outage",
    "South Africa water infrastructure disruption",
    "South Africa airport OR port disruption",
    "South Africa business regulation OR investment",
]


# ============================================================
# CITY NEWS SEARCHES
# ============================================================

CITY_QUERIES = {
    "Johannesburg": [
        "Johannesburg protest OR demonstration OR road closure",
        "Johannesburg crime OR security business district",
        "Johannesburg business disruption OR infrastructure",
        "Johannesburg transport OR electricity disruption",
    ],

    "Cape Town": [
        "Cape Town protest OR demonstration OR road closure",
        "Cape Town crime OR security business district",
        "Cape Town business disruption OR infrastructure",
        "Cape Town transport OR electricity disruption",
    ],

    "Pretoria / Tshwane": [
        "Pretoria OR Tshwane protest OR road closure",
        "Pretoria OR Tshwane crime OR security",
        "Pretoria OR Tshwane business disruption",
        "Pretoria OR Tshwane infrastructure OR transport",
    ],

    "Durban / eThekwini": [
        "Durban OR eThekwini protest OR road closure",
        "Durban OR eThekwini crime OR security",
        "Durban OR eThekwini port OR freight disruption",
        "Durban OR eThekwini infrastructure OR transport",
    ],

    "Gqeberha": [
        "Gqeberha protest OR road closure",
        "Gqeberha crime OR security",
        "Gqeberha business disruption OR infrastructure",
    ],

    "Bloemfontein": [
        "Bloemfontein protest OR road closure",
        "Bloemfontein crime OR security",
        "Bloemfontein business disruption OR infrastructure",
    ],

    "East London": [
        "East London South Africa protest OR road closure",
        "East London South Africa crime OR security",
        "East London South Africa business disruption",
    ],

    "Polokwane": [
        "Polokwane protest OR road closure",
        "Polokwane crime OR security",
        "Polokwane infrastructure OR business disruption",
    ],

    "Mbombela": [
        "Mbombela OR Nelspruit protest OR road closure",
        "Mbombela OR Nelspruit crime OR security",
        "Mbombela OR Nelspruit business disruption",
    ],
}


# ============================================================
# MONITORED LOCATIONS
# ============================================================

MONITORED_CITIES = {
    "johannesburg": {
        "name": "Johannesburg",
        "province": "Gauteng",
        "latitude": -26.2041,
        "longitude": 28.0473,
    },

    "cape-town": {
        "name": "Cape Town",
        "province": "Western Cape",
        "latitude": -33.9249,
        "longitude": 18.4241,
    },

    "pretoria-tshwane": {
        "name": "Pretoria / Tshwane",
        "province": "Gauteng",
        "latitude": -25.7479,
        "longitude": 28.2293,
    },

    "durban-ethekwini": {
        "name": "Durban / eThekwini",
        "province": "KwaZulu-Natal",
        "latitude": -29.8587,
        "longitude": 31.0218,
    },

    "gqeberha": {
        "name": "Gqeberha",
        "province": "Eastern Cape",
        "latitude": -33.9608,
        "longitude": 25.6022,
    },

    "bloemfontein": {
        "name": "Bloemfontein",
        "province": "Free State",
        "latitude": -29.0852,
        "longitude": 26.1596,
    },

    "east-london": {
        "name": "East London",
        "province": "Eastern Cape",
        "latitude": -33.0292,
        "longitude": 27.8546,
    },

    "polokwane": {
        "name": "Polokwane",
        "province": "Limpopo",
        "latitude": -23.9045,
        "longitude": 29.4689,
    },

    "mbombela": {
        "name": "Mbombela",
        "province": "Mpumalanga",
        "latitude": -25.4753,
        "longitude": 30.9694,
    },
}