"""Central configuration. Every value that affects results lives here so runs are reproducible."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = (PROJECT_ROOT / ".." / "CARE_To_Compare").resolve()  # original dataset, READ-ONLY
FARM = "C"
FARM_DIR = DATA_DIR / f"Wind Farm {FARM}"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
METRICS_DIR = REPORTS_DIR / "metrics"

# ---- columns
META_COLS = ["time_stamp", "asset_id", "id", "train_test", "status_type_id"]
# Never model inputs (identifiers, bookkeeping, outcome-revealing status).
NON_FEATURE_COLS = META_COLS + ["event_id", "label", "label_source", "fold", "source_file", "ts"]
FEATURE_SUFFIXES_STORED = ("_avg", "_std")  # stored in processed data (std kept for optional comparison)
FEATURE_SET_BASELINE = ("_avg",)

# ---- cleaning (decided in Stage 1 from feature_description + observed values)
# Wind speeds cannot be negative; -14.9 m/s is a sensor-failure code -> treat as missing.
NEGATIVE_IS_MISSING_PREFIXES = ("wind_speed_235", "wind_speed_236", "wind_speed_237")

# ---- labels
TS_FORMAT = "%Y-%m-%d %H:%M:%S"
FREQ_MINUTES = 10
LABEL_POS, LABEL_NEG, LABEL_EXCLUDED = 1, 0, -1
# label_source categories, highest priority first (used when duplicate records disagree)
SOURCE_PRIORITY = [
    "anomaly_window",       # inside an expert anomaly event window        -> 1
    "excluded_post_event",  # after event_end in an anomaly file (repair)   -> excluded
    "excluded_pre_event",   # prediction rows before event_start (anomaly)  -> excluded
    "normal_window",        # inside an expert normal event window          -> 0 (confirmed)
    "assumed_normal",       # outside any labelled window                   -> 0 (assumed)
]
SOURCE_TO_LABEL = {
    "anomaly_window": LABEL_POS,
    "excluded_post_event": LABEL_EXCLUDED,
    "excluded_pre_event": LABEL_EXCLUDED,
    "normal_window": LABEL_NEG,
    "assumed_normal": LABEL_NEG,
}

# ---- deduplication: a fingerprint match between two files of the same turbine counts as the
# same physical record only if it agrees with that file pair's dominant time offset.
DEDUP_MIN_MATCHES = 100
DEDUP_MIN_OFFSET_SHARE = 0.9

# ---- validation (fold assignment computed in Stage 1 proposal: StratifiedGroupKFold, seed below)
N_FOLDS = 5
FOLD_SEED = 2
TEST_FOLD = 0
RANDOM_STATE = 42

# ---- training-only negative thinning: keep normal records whose minute == 0 (1 per hour)
THIN_NEGATIVES_MINUTE = 0

# ---- alarm rule for event-level evaluation
ALARM_CONSECUTIVE = 6  # 6 x 10 min = one continuous hour
