"""Configuration for trial-voices: patient clinical-trial experience miner."""
import os

# --- Reddit API (https://www.reddit.com/prefs/apps -> create "script" app) ---
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "trial-voices/0.1 by u/yourname")

# --- Anthropic ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
EXTRACT_MODEL = "claude-haiku-4-5-20251001"   # cheap per-comment extraction
SYNTH_MODEL = "claude-sonnet-4-6"             # synthesis / analysis

DB_PATH = os.path.join(os.path.dirname(__file__), "trial_voices.db")

# Subreddits rich in trial discussion. Tune freely.
SUBREDDITS = [
    "clinicaltrials", "cancer", "leukemia", "multiplemyeloma", "lymphoma",
    "CAR_T", "breastcancer", "lungcancer", "ALS", "MultipleSclerosis",
    "ParkinsonsDisease", "rheumatoid", "Crohns",
]

# Search terms used per-subreddit (Reddit search syntax).
SEARCH_TERMS = [
    "clinical trial", "investigational drug", "trial infusion",
    "on the trial", "drug trial experience", "phase 1 trial",
    "phase 2 trial", "study drug", "enrolled in a trial",
]

# Pre-filter: a comment/post must contain >=1 of these (cheap relevance gate
# before spending tokens). Lowercased substring match.
RELEVANCE_KEYWORDS = [
    "trial", "investigational", "study drug", "infusion", "cycle",
    "dose", "dosing", "enrolled", "phase 1", "phase 2", "phase 3",
    "placebo", "randomized", "experimental drug", "compassionate use",
]
