"""Reusable prediction interface (independent of the training code).

Example::

    from wtpm.predict import predict_turbine_status
    result = predict_turbine_status({"asset_id": 13, "time_stamp": "2023-08-01 10:00:00",
                                     "sensor_0_avg": 88.5, ...})

Input : one record (dict), a list of dicts, or a pandas DataFrame with the model's feature columns
        (names listed in artifacts/model_metadata_<set>.json -> "features"). Extra fields are ignored
        (identifiers such as asset_id / time_stamp are echoed back but never used by the model).
        null / NaN feature values are allowed (Random Forest handles them); missing *keys* are an error.
Output: list of dicts, one per record:
        {"asset_id", "time_stamp", "prediction": "anomaly"|"normal", "label": 1|0,
         "anomaly_probability", "threshold", "model_version", "validation": {...}}

The model classifies the CURRENT anomaly state of a record. It does not forecast future failures.
Use ``AlarmTracker`` to turn per-record predictions into alarms (6 consecutive 10-min positives).
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from wtpm import config

ECHO_FIELDS = ("asset_id", "time_stamp")


class InputValidationError(ValueError):
    """Raised when input records do not match the model's feature schema."""


@lru_cache(maxsize=4)
def load_model(feature_set: str = "avg", artifacts_dir: str | None = None):
    d = Path(artifacts_dir) if artifacts_dir else config.ARTIFACTS_DIR
    meta_path, model_path = d / f"model_metadata_{feature_set}.json", d / f"model_{feature_set}.joblib"
    if not meta_path.exists() or not model_path.exists():
        raise FileNotFoundError(f"Model artifacts not found in {d} (run `python -m wtpm.train` first)")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    model = joblib.load(model_path)
    if list(getattr(model, "feature_names_in_", meta["features"])) != meta["features"]:
        raise RuntimeError("Saved model and metadata disagree on feature order")
    return model, meta


@lru_cache(maxsize=4)
def _load_baselines(feature_set, artifacts_dir, filename) -> pd.DataFrame:
    d = Path(artifacts_dir) if artifacts_dir else config.ARTIFACTS_DIR
    return pd.read_csv(d / filename)


def _to_frame(input_data) -> pd.DataFrame:
    if isinstance(input_data, pd.DataFrame):
        return input_data.copy()
    if isinstance(input_data, dict):
        return pd.DataFrame([input_data])
    if isinstance(input_data, list) and all(isinstance(r, dict) for r in input_data):
        if not input_data:
            raise InputValidationError("Empty input list")
        return pd.DataFrame(input_data)
    raise InputValidationError("input_data must be a dict, a list of dicts or a pandas DataFrame")


def validate_input(input_data, features: list[str]) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Return (X in exact training feature order, validation info, raw input frame).
    Raises InputValidationError."""
    df = _to_frame(input_data)
    missing = [c for c in features if c not in df.columns]
    if missing:
        raise InputValidationError(f"{len(missing)} required feature(s) missing, e.g. {missing[:10]}")
    X = df[features]
    bad = []
    for c in features:
        if not pd.api.types.is_numeric_dtype(X[c]):
            conv = pd.to_numeric(X[c], errors="coerce")
            if (conv.isna() & X[c].notna()).any():
                bad.append(c)
    if bad:
        raise InputValidationError(f"Non-numeric values in feature(s): {bad[:10]}")
    X = X.apply(pd.to_numeric, errors="coerce").astype("float64")
    if np.isinf(X.to_numpy()).any():
        raise InputValidationError("Infinite values are not allowed")
    # same cleaning as training: negative wind speeds are a sensor-failure code -> missing
    n_sentinel = 0
    for c in features:
        if c.startswith(config.NEGATIVE_IS_MISSING_PREFIXES) and c.endswith("_avg"):
            m = X[c] < 0
            n_sentinel += int(m.sum())
            X.loc[m, c] = np.nan
    null_per_row = X.isna().sum(axis=1)
    info = {
        "n_records": int(len(X)),
        "ignored_fields": [c for c in df.columns if c not in features and c not in ECHO_FIELDS],
        "sentinel_values_set_missing": n_sentinel,
        "null_features_per_record": null_per_row.astype(int).tolist(),
    }
    return X, info, df


def required_input_features(meta: dict) -> list[str]:
    """Raw sensor fields the caller must send (before any model-side transform)."""
    return meta.get("raw_input_features") or meta["features"]


def predict_turbine_status(input_data, feature_set: str = "avg", artifacts_dir: str | None = None) -> list[dict]:
    model, meta = load_model(feature_set, artifacts_dir)
    X, info, raw = validate_input(input_data, required_input_features(meta))
    tf = meta.get("transform")
    if tf and tf["type"] == "ambient_delta":
        from wtpm.features import ambient_delta
        X = ambient_delta(X, tf["temperature_columns"])
    X = X[meta["features"]]
    if meta.get("turbine_baselines_file"):
        from wtpm.features import apply_turbine_baselines
        if "asset_id" not in raw.columns or raw["asset_id"].isna().any():
            raise InputValidationError("asset_id is required: this model uses per-turbine baselines")
        bl = _load_baselines(feature_set, artifacts_dir, meta["turbine_baselines_file"])
        try:
            X = apply_turbine_baselines(X.assign(asset_id=raw["asset_id"].astype(int).to_numpy()),
                                        meta["features"], bl)[meta["features"]]
        except KeyError as e:
            raise InputValidationError(str(e)) from e
    proba = model.predict_proba(X)[:, 1]
    thr = meta["threshold"]
    out = []
    for i, p in enumerate(proba):
        label = int(p >= thr)
        rec = {f: (None if f not in raw.columns else _plain(raw[f].iloc[i])) for f in ECHO_FIELDS}
        rec.update({
            "prediction": "anomaly" if label else "normal", "label": label,
            "anomaly_probability": round(float(p), 6), "threshold": thr,
            "model_version": meta["model_version"],
            "validation": {"null_features": info["null_features_per_record"][i],
                           "high_missingness": info["null_features_per_record"][i] > 0.2 * X.shape[1]},
        })
        out.append(rec)
    if info["ignored_fields"] or info["sentinel_values_set_missing"]:
        out[0]["validation"]["batch_notes"] = {"ignored_fields": info["ignored_fields"],
                                               "sentinel_values_set_missing": info["sentinel_values_set_missing"]}
    return out


def _plain(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if math.isnan(v) else float(v)
    if isinstance(v, pd.Timestamp):
        return str(v)
    return v


class AlarmTracker:
    """Per-turbine streaming alarm: raises when ``k`` consecutive records are 'anomaly' AND each is
    exactly ``freq_minutes`` after the previous one (a gap or an out-of-order record resets the run)."""

    def __init__(self, k: int = config.ALARM_CONSECUTIVE, freq_minutes: int = config.FREQ_MINUTES):
        self.k, self.step = k, pd.Timedelta(minutes=freq_minutes)
        self._state: dict = {}  # asset_id -> (last_ts, run_length)

    def update(self, asset_id, time_stamp, label: int) -> dict:
        ts = pd.Timestamp(time_stamp)
        last_ts, run = self._state.get(asset_id, (None, 0))
        contiguous = last_ts is not None and ts - last_ts == self.step
        run = (run + 1 if contiguous else 1) if label == 1 else 0
        self._state[asset_id] = (ts, run)
        return {"asset_id": asset_id, "time_stamp": str(ts), "consecutive_anomalies": run, "alarm": run >= self.k}
