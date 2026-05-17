#!/usr/bin/env python3
"""Summarize AFR by load band from a merged log."""

import argparse
from pathlib import Path

import pandas as pd


BUCKETS = [
    ("idle", 0, 6),
    ("light", 6, 9),
    ("mid", 9, 12),
    ("boost", 12, 17),
]


def normalize(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def find_column(columns, candidates):
    normalized = {normalize(col): col for col in columns}
    for candidate in candidates:
        needle = normalize(candidate)
        for key, original in normalized.items():
            if needle in key:
                return original
    return None


def main():
    parser = argparse.ArgumentParser(description="Summarize AFR by load band from a merged log.")
    parser.add_argument("input_csv", help="Path to fused.csv or fused_corrected.csv")
    args = parser.parse_args()

    log_path = Path(args.input_csv)
    if not log_path.is_file():
        raise FileNotFoundError(f"Missing input file: {log_path.resolve()}")

    df = pd.read_csv(log_path)
    afr_col = find_column(df.columns, ["afr", "airfuelratio"])
    load_col = find_column(df.columns, ["engine_load", "map", "manifold"])

    if not afr_col:
        raise KeyError("Could not find an AFR column in the merged log.")
    if not load_col:
        raise KeyError("Could not find a load or MAP column in the merged log.")

    afr = pd.to_numeric(df[afr_col], errors="coerce")
    load = pd.to_numeric(df[load_col], errors="coerce")
    valid = afr.between(8, 20) & load.notna()

    print("\nAFR summary")
    print("-----------")
    for name, lo, hi in BUCKETS:
        mask = valid & load.ge(lo) & load.lt(hi)
        count = int(mask.sum())
        if count:
            avg = float(afr[mask].mean())
            print(f"{name:5s}:  {avg:5.2f}  ({count:,} samples)")
        else:
            print(f"{name:5s}:   ---   (no data)")


if __name__ == "__main__":
    main()
