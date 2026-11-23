"""Feature selection. Anything 'fitted' here must only ever see training data."""

from __future__ import annotations

import pandas as pd

from wtpm import config


def candidate_features(columns, suffixes=config.FEATURE_SET_BASELINE) -> list[str]:
    """Sensor columns with the requested statistic suffixes, in original column order.
    Identifiers, timestamps, status and label columns are never returned."""
    return [c for c in columns if c.endswith(tuple(suffixes)) and c not in config.NON_FEATURE_COLS]


def fit_non_constant(X_train: pd.DataFrame) -> list[str]:
    """Drop columns that are constant (or entirely missing) in the TRAINING data."""
    nun = X_train.nunique(dropna=True)
    return [c for c in X_train.columns if nun[c] > 1]


AMBIENT_COL = "sensor_7_avg"                                  # "Ambient temperature" (Farm C)
OUTSIDE_TEMP_COLS = ("sensor_7_avg", "sensor_41_avg", "sensor_177_avg")  # ambient / outside temps


def temperature_columns(columns, farm_dir=None) -> list[str]:
    """_avg columns whose feature_description unit is Celsius."""
    import pandas as pd  # local import keeps module import light
    fd = pd.read_csv((farm_dir or config.FARM_DIR) / "feature_description.csv", sep=";")
    temp_sensors = set(fd.loc[fd["unit"].astype(str).eq("Celsius"), "sensor_name"])
    return [c for c in columns if c.endswith("_avg") and c[:-4] in temp_sensors]


def ambient_delta(X: pd.DataFrame, temp_cols: list[str]) -> pd.DataFrame:
    """Season-robust transform (no fitting -> no leakage): every component temperature becomes
    (temperature - ambient temperature); the ambient/outside temperature columns are dropped."""
    X = X.copy()
    amb = X[AMBIENT_COL]
    for c in temp_cols:
        if c not in OUTSIDE_TEMP_COLS:
            X[c] = X[c] - amb
    return X.drop(columns=[c for c in OUTSIDE_TEMP_COLS if c in X.columns])


def fit_turbine_baselines(df: pd.DataFrame, feats: list[str], reference_mask) -> pd.DataFrame:
    """Per-turbine robust baseline (median, IQR) of each feature from that turbine's OWN reference
    period (its historical `train` part). Uses no labels and no data from other turbines.
    Returns a long DataFrame: asset_id, feature, median, iqr."""
    ref = df.loc[reference_mask, ["asset_id"] + feats]
    g = ref.groupby("asset_id")[feats]
    med = g.median()
    iqr = g.quantile(0.75) - g.quantile(0.25)
    iqr = iqr.where(iqr > 1e-9, 1.0)  # constant in the reference period -> no scaling
    m = med.reset_index().melt(id_vars="asset_id", var_name="feature", value_name="median")
    q = iqr.reset_index().melt(id_vars="asset_id", var_name="feature", value_name="iqr")
    return m.merge(q, on=["asset_id", "feature"])


def apply_turbine_baselines(df: pd.DataFrame, feats: list[str], baselines: pd.DataFrame) -> pd.DataFrame:
    """(value - turbine median) / turbine IQR for every feature. Unknown turbines raise KeyError."""
    unknown = set(df["asset_id"].unique()) - set(baselines["asset_id"].unique())
    if unknown:
        raise KeyError(f"No baseline for turbine(s) {sorted(unknown)}; calibrate them first")
    med = baselines.pivot(index="asset_id", columns="feature", values="median")[feats]
    iqr = baselines.pivot(index="asset_id", columns="feature", values="iqr")[feats]
    a = df["asset_id"].to_numpy()
    X = (df[feats].to_numpy(dtype="float64") - med.loc[a].to_numpy()) / iqr.loc[a].to_numpy()
    out = df.copy()
    out[feats] = X.astype("float32")
    return out


def thin_negatives(df: pd.DataFrame, minute: int = config.THIN_NEGATIVES_MINUTE) -> pd.DataFrame:
    """Training-only class-imbalance reduction: keep all positives and the negatives
    recorded at one fixed minute of the hour (1 per hour). Deterministic, no randomness."""
    keep = (df["label"] == config.LABEL_POS) | (df["ts"].dt.minute == minute)
    return df.loc[keep]
