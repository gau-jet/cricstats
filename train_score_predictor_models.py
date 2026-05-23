#!/usr/bin/env python3
"""Retrain Score Predictor XGBoost models from ball-by-ball CSV data."""

import pickle
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

TEAM_NAME_MAPPINGS = {
    "Delhi Daredevils": "Delhi Capitals",
    "Deccan Chargers": "Sunrisers Hyderabad",
    "Gujarat Lions": "Gujarat Titans",
    "Kings XI Punjab": "Punjab Kings",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
    "Pune Warriors": "Rising Pune Supergiant",
}

FEATURE_COLUMNS = [
    "batting_team",
    "bowling_team",
    "venue",
    "current_score",
    "overs",
    "current_wickets",
    "prev_30_runs",
    "prev_30_wickets",
    "prev_30_dot_balls",
    "prev_30_boundaries",
]

SERIES_CONFIG = {
    "IPL": {
        "deliveries": "data/deliveries.csv",
        "matches": "data/matches.csv",
        "output": "data/IPL-Batting-score-xgboost.pkl",
        "apply_team_mapping": True,
    },
    "T20I": {
        "deliveries": "data/T20Ideliveries.csv",
        "matches": "data/T20Imatches.csv",
        "output": "data/T20I-Batting-score-xgboost.pkl",
        "apply_team_mapping": False,
    },
    "WT20": {
        "deliveries": "data/WT20deliveries.csv",
        "matches": "data/WT20matches.csv",
        "output": "data/WT20-Batting-score-xgboost.pkl",
        "apply_team_mapping": False,
    },
}


def apply_team_mapping(df):
    df = df.copy()
    for old_name, new_name in TEAM_NAME_MAPPINGS.items():
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.replace(old_name, new_name, regex=False)
    return df


def build_training_data(deliveries_path, matches_path, apply_mapping=False):
    del_df = pd.read_csv(deliveries_path)
    match_df = pd.read_csv(matches_path)

    del_df = del_df[del_df["is_super_over"] == 0].copy()
    if apply_mapping:
        del_df = apply_team_mapping(del_df)

    venue_by_match = match_df.drop_duplicates("id").set_index("id")["venue"]
    del_df["venue"] = del_df["id"].map(venue_by_match)
    del_df = del_df.dropna(subset=["venue"])
    del_df = del_df.sort_values(["id", "inning", "over", "ball"])

    grouped = del_df.groupby(["id", "inning"], sort=False)
    del_df["current_score"] = grouped["total_runs"].cumsum()
    del_df["current_wickets"] = grouped["is_wicket"].fillna(0).astype(int).cumsum()
    del_df["overs"] = (del_df["over"] - 1) + del_df["ball"] / 6.0
    del_df["is_dot"] = (del_df["total_runs"] == 0).astype(int)
    del_df["is_boundary"] = (del_df["batsman_runs"] >= 4).astype(int)
    del_df["final_score"] = grouped["current_score"].transform("last")

    del_df["prev_30_runs"] = grouped["total_runs"].transform(
        lambda series: series.rolling(30, min_periods=1).sum()
    )
    del_df["prev_30_wickets"] = grouped["is_wicket"].fillna(0).transform(
        lambda series: series.rolling(30, min_periods=1).sum()
    )
    del_df["prev_30_dot_balls"] = grouped["is_dot"].transform(
        lambda series: series.rolling(30, min_periods=1).sum()
    )
    del_df["prev_30_boundaries"] = grouped["is_boundary"].transform(
        lambda series: series.rolling(30, min_periods=1).sum()
    )

    train_df = del_df[del_df["overs"] >= 5.0].copy()
    x = train_df[FEATURE_COLUMNS]
    y = train_df["final_score"]
    return x, y


def build_model():
    categorical = ["batting_team", "bowling_team", "venue"]
    numeric = [
        "current_score",
        "overs",
        "current_wickets",
        "prev_30_runs",
        "prev_30_wickets",
        "prev_30_dot_balls",
        "prev_30_boundaries",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", StandardScaler(), numeric),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                XGBRegressor(
                    n_estimators=200,
                    max_depth=8,
                    learning_rate=0.08,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def train_series(name, config):
    print(f"\nTraining {name} model...")
    x, y = build_training_data(
        config["deliveries"],
        config["matches"],
        apply_mapping=config["apply_team_mapping"],
    )
    print(f"  training rows: {len(x):,}")

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    model = build_model()
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"  test MAE: {mae:.2f} runs")

    output_path = Path(config["output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as model_file:
        pickle.dump(model, model_file)
    print(f"  saved: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Retrain Score Predictor models")
    parser.add_argument(
        "--series",
        choices=list(SERIES_CONFIG.keys()),
        default=None,
        help="Train one series only (default: all)",
    )
    args = parser.parse_args()

    series_to_train = (
        {args.series: SERIES_CONFIG[args.series]}
        if args.series
        else SERIES_CONFIG
    )

    for name, config in series_to_train.items():
        train_series(name, config)

    print("\nDone.")


if __name__ == "__main__":
    main()
