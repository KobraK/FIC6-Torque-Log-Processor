#!/usr/bin/env python3
import sys
import pandas as pd
import numpy as np
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Fuel trim analysis with color-coded recommendations and CSV summary output"
    )
    parser.add_argument("input_csv", help="Path to fused_corrected.csv")
    parser.add_argument("--min-rpm", type=float, default=None, help="Minimum corrected RPM to include")
    parser.add_argument("--max-rpm", type=float, default=None, help="Maximum corrected RPM to include")
    parser.add_argument("--rpm-bin", type=float, default=400, help="RPM bin size for grouping")
    parser.add_argument(
        "--load-bins", type=str,
        default="0,3,5,7,10,13,14.7,15,16,17,20,22",
        help="Comma-separated MAP (PSIA) bin edges"
    )
    parser.add_argument(
        "--atm-psia", type=float, default=14.7,
        help="Atmospheric pressure in PSIA for load ratio (default 14.7)"
    )
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    if not input_path.is_file():
        sys.exit(f"Error: input file not found: {input_path.resolve()}")

    # Load and rename
    df = pd.read_csv(input_path)
    if "__time" not in df.columns and "Time" in df.columns:
        df = df.rename(columns={"Time": "__time"})
    if "__time" not in df.columns:
        sys.exit("Error: No __time or Time column found.")
    df["__time"] = pd.to_datetime(df["__time"], errors="coerce")
    rename_map = {}
    for column in df.columns:
        normalized = "".join(ch.lower() for ch in column if ch.isalnum())
        if "fueltrim" in normalized and "longterm" in normalized:
            rename_map[column] = "LTFT"
        elif "fueltrim" in normalized and ("shortterm" in normalized or "shrtterm" in normalized):
            rename_map[column] = "STFT"
    df = df.rename(columns=rename_map)
    if "LTFT" not in df.columns or "STFT" not in df.columns:
        sys.exit("Error: Could not find LTFT/STFT columns in the merged log.")

    # Detect RPM
    rpm_col = next((c for c in df.columns if "rpm" in c.lower() and "corrected" in c.lower()), None)
    if not rpm_col:
        rpm_col = next((c for c in df.columns if "rpm" in c.lower()), None)
        if not rpm_col:
            sys.exit("Error: No RPM column found.")
        print(f"Warning: no corrected RPM column found, using raw RPM column '{rpm_col}'.")
    df = df.rename(columns={rpm_col: "RPM"})

    # Detect MAP or Engine Load
    map_col = next((c for c in df.columns if c.lower().startswith("map") or "manifold" in c.lower()), None)
    eng_load_col = next((c for c in df.columns if "engine_load" in c.lower()), None)
    if map_col:
        df = df.rename(columns={map_col: "MAP_PSIA"})
    elif eng_load_col:
        df["MAP_PSIA"] = df[eng_load_col] / 100.0 * args.atm_psia
    else:
        sys.exit("Error: No MAP (PSIA) or Engine_Load column found.")

    # Compute load ratio
    df["LOAD_RATIO"] = df["MAP_PSIA"] / args.atm_psia

    # RPM filtering
    if args.min_rpm is not None:
        df = df[df["RPM"] >= args.min_rpm]
    if args.max_rpm is not None:
        df = df[df["RPM"] <= args.max_rpm]
    print(f"Analyzing {len(df)} rows after RPM filtering")

    # Thresholds
    LTFT_THRESH, STFT_THRESH = 5.0, 10.0

    # Flag out-of-range rows
    mask = (df["LTFT"].abs() > LTFT_THRESH) | (df["STFT"].abs() > STFT_THRESH)
    issues = df.loc[mask, ["__time", "RPM", "MAP_PSIA", "LTFT", "STFT"]]
    issues_path = input_path.parent / "fuel_trim_issues.csv"
    issues.to_csv(issues_path, index=False)
    print(f"Flagged rows saved to {issues_path}: {len(issues)} / {len(df)}")

    # Issue blocks
    df["issue"] = mask
    df["block_id"] = (df["issue"] != df["issue"].shift()).cumsum()
    blocks = df[df["issue"]].groupby("block_id", observed=False).agg(
        start_time=("__time","first"), end_time=("__time","last"),
        duration=("__time", lambda x: x.iloc[-1] - x.iloc[0]),
        count=("issue","size"), min_RPM=("RPM","min"), max_RPM=("RPM","max"),
        min_PSIA=("MAP_PSIA","min"), max_PSIA=("MAP_PSIA","max"),
        max_LTFT=("LTFT","max"), min_LTFT=("LTFT","min"),
        max_STFT=("STFT","max"), min_STFT=("STFT","min")
    ).reset_index(drop=True)
    blocks_path = input_path.parent / "fuel_trim_issue_blocks.csv"
    blocks.to_csv(blocks_path, index=False)
    print(f"Issue blocks saved to {blocks_path}: {len(blocks)} blocks")

    # Binning
    rpm_edges = np.arange(
        (df["RPM"].min() // args.rpm_bin) * args.rpm_bin,
        df["RPM"].max() + args.rpm_bin,
        args.rpm_bin
    )
    df["RPM_BIN"] = pd.cut(df["RPM"], rpm_edges)
    psia_edges = [float(x) for x in args.load_bins.split(",")]
    df["PSIA_BIN"] = pd.cut(df["MAP_PSIA"], psia_edges)

    # Summary list
    summary = []
    print("\nFuel Trim Suggestions by RPM and MAP (PSIA) bins:")
    for (rbin, pbin), grp in df.groupby(["RPM_BIN","PSIA_BIN"], observed=False):
        avg_ltft = grp["LTFT"].mean()
        status = "within thresholds"
        if avg_ltft < -LTFT_THRESH:
            status = f"Decrease fuel by {abs(avg_ltft):.1f}%"
        elif avg_ltft > LTFT_THRESH:
            status = f"Increase fuel by {avg_ltft:.1f}%"
        line = f"RPM {rbin} | PSIA {pbin} => {status}"
        print(line)
        summary.append({
            "RPM_BIN": str(rbin),
            "PSIA_BIN": str(pbin),
            "Avg_LTFT": avg_ltft,
            "Recommendation": status
        })

    # Write summary CSV to avoid external dependencies
    df_sum = pd.DataFrame(summary)
    out_file = input_path.parent / "fuel_trim_summary.csv"
    df_sum.to_csv(out_file, index=False)
    print(f"CSV summary written to {out_file}")

if __name__ == "__main__":
    main()
