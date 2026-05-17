#!/usr/bin/env python3
import sys
from pathlib import Path
import pandas as pd


def main():
    if len(sys.argv) != 3:
        print("Usage: python rpm_offset_correction.py <input_csv> <output_csv>")
        sys.exit(1)

    input_csv, output_csv = sys.argv[1], sys.argv[2]
    input_path = Path(input_csv)
    df = pd.read_csv(input_path)

    # Backward compatible: older resample_merge.py wrote Time instead of __time.
    if '__time' not in df.columns and 'Time' in df.columns:
        df = df.rename(columns={'Time': '__time'})
    if '__time' not in df.columns:
        print("Error: '__time' column not found.")
        print("Available columns:", df.columns.tolist())
        sys.exit(1)

    df['__time'] = pd.to_datetime(df['__time'], errors='coerce')
    df = df.dropna(subset=['__time']).sort_values('__time')

    cols_lower = [c.lower() for c in df.columns]
    try:
        ecu_col = df.columns[cols_lower.index(next(c for c in cols_lower if c.startswith('rpm_a')))]
        fic6_col = df.columns[cols_lower.index(next(c for c in cols_lower if c.startswith('rpm_b')))]
    except StopIteration:
        print("Error: couldn't find columns starting with 'rpm_a' or 'rpm_b'.")
        print("Available columns:", df.columns.tolist())
        sys.exit(1)

    df[ecu_col] = pd.to_numeric(df[ecu_col], errors='coerce')
    df[fic6_col] = pd.to_numeric(df[fic6_col], errors='coerce')

    ecu_series = df.set_index('__time')[ecu_col]
    ecu_interp = ecu_series.reindex(df['__time']).interpolate(method='time')

    offset = (df[fic6_col] - ecu_interp.values).mean()
    print(f"Mean RPM offset = {offset:.2f} RPM (using '{fic6_col}' vs '{ecu_col}')")
    df[f'{fic6_col}_corrected'] = df[fic6_col] - offset

    output_path = Path(output_csv)
    if not output_path.is_absolute():
        output_path = input_path.resolve().parent / output_path

    df.to_csv(output_path, index=False)
    print(f"Wrote bias-corrected file to {output_path}")


if __name__ == '__main__':
    main()
