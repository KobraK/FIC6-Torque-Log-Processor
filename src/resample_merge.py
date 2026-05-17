#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import pandas as pd

ap = argparse.ArgumentParser(description="Resample aligned Torque and FIC6 logs and merge onto one time grid.")
ap.add_argument("file_a")
ap.add_argument("file_b")
ap.add_argument("output")
ap.add_argument("--freq", default="10ms")
ap.add_argument("--interp", action="store_true")
ap.add_argument("--rpm-limit", type=float)
args = ap.parse_args()

dfa = pd.read_csv(args.file_a)
dfb = pd.read_csv(args.file_b)

for name, df in ((args.file_a, dfa), (args.file_b, dfb)):
    if '__time' not in df.columns:
        sys.exit(f"{name} is missing __time. Run sanitize_column_headers_2ndstep_time.py first.")

dfa['__time'] = pd.to_datetime(dfa['__time'], errors='coerce')
dfb['__time'] = pd.to_datetime(dfb['__time'], errors='coerce')

dfa = dfa.dropna(subset=['__time']).drop_duplicates(subset='__time').set_index('__time')
dfb = dfb.dropna(subset=['__time']).drop_duplicates(subset='__time').set_index('__time')
dfa = dfa[~dfa.index.duplicated()].sort_index()
dfb = dfb[~dfb.index.duplicated()].sort_index()

for c in dfa.columns:
    dfa[c] = pd.to_numeric(dfa[c], errors='coerce')
for c in dfb.columns:
    dfb[c] = pd.to_numeric(dfb[c], errors='coerce')

f = (lambda d: d.interpolate(method='time')) if args.interp else (lambda d: d.ffill())

dfa = dfa[~dfa.index.isna()]
dfb = dfb[~dfb.index.isna()]

dfa = f(dfa).resample(args.freq).ffill()
dfb = f(dfb).resample(args.freq).ffill()

grid = dfa.index.union(dfb.index).unique().sort_values()
dfa = dfa.reindex(grid).ffill()
dfb = dfb.reindex(grid).ffill()

dfa.columns = [f"{c}_a" for c in dfa.columns]
dfb.columns = [f"{c}_b" for c in dfb.columns]
fused = pd.concat([dfa, dfb], axis=1).reset_index().rename(columns={'index': '__time'})

if args.rpm_limit is not None:
    rpm_cols = [c for c in fused.columns if 'rpm' in c.lower()]
    if len(rpm_cols) < 2:
        sys.exit("Need two RPM columns for --rpm-limit filter.")
    rpm_a, rpm_b = rpm_cols[:2]
    fused[rpm_a] = pd.to_numeric(fused[rpm_a], errors='coerce')
    fused[rpm_b] = pd.to_numeric(fused[rpm_b], errors='coerce')
    mask = fused[rpm_a].notna() & fused[rpm_b].notna() & ((fused[rpm_a] - fused[rpm_b]).abs() <= args.rpm_limit)
    fused = fused[mask]

output_path = Path(args.output)
if not output_path.is_absolute():
    output_path = Path(args.file_a).resolve().parent / output_path

fused.to_csv(output_path, index=False)
print(f"Wrote {len(fused):,} rows to {output_path}")
