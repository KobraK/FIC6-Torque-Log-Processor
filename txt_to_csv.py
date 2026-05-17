#!/usr/bin/env python3
"""
txt_to_csv.py

1) Convert a tab-delimited .txt log into fic6.csv
2) Copy or rename a tracklog CSV into torque_log.csv

Usage:
    python txt_to_csv.py <path/to/log…txt> [<path/to/tracklog.csv>]

If you omit the second argument, it will look in the TXT’s folder
for exactly one file matching tracklog*.csv and use that.
"""
import argparse
import os
import sys
import glob
import shutil
import pandas as pd

def convert_txt(input_txt):
    txt_dir = os.path.dirname(input_txt) or '.'
    out_csv = os.path.join(txt_dir, 'fic6.csv')
    df = pd.read_csv(input_txt, sep='\t', engine='python', encoding='utf-8')
    df.to_csv(out_csv, index=False, encoding='utf-8')
    print(f"Wrote {out_csv}")

def find_tracklog(dirpath):
    pattern = os.path.join(dirpath, 'tracklog*.csv')
    candidates = [f for f in glob.glob(pattern)
                  if os.path.basename(f).lower() not in ('torque_log.csv','fic6.csv')]
    if len(candidates) == 1:
        return candidates[0]
    elif not candidates:
        sys.exit(f"Error: No tracklog*.csv found in {dirpath}")
    else:
        sys.exit(f"Error: Multiple tracklog*.csv files found in {dirpath}, please specify one explicitly.")

def copy_tracklog(input_csv, output_dir=None):
    csv_dir = output_dir or os.path.dirname(input_csv) or '.'
    out_csv = os.path.join(csv_dir, 'torque_log.csv')
    # copy (leaves original in place)
    shutil.copy2(input_csv, out_csv)
    print(f"Wrote {out_csv}")

def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('input_txt', help='tab-delimited .txt to convert into fic6.csv')
    p.add_argument('input_csv', nargs='?', help='(optional) your tracklog CSV; if omitted we auto-detect tracklog*.csv')
    args = p.parse_args()

    if not os.path.isfile(args.input_txt):
        sys.exit(f"Error: TXT file not found: {args.input_txt}")

    if args.input_csv:
        tracklog = args.input_csv
    else:
        tracklog = find_tracklog(os.path.dirname(args.input_txt) or '.')

    if not os.path.isfile(tracklog):
        sys.exit(f"Error: CSV file not found: {tracklog}")

    convert_txt(args.input_txt)
    copy_tracklog(tracklog, os.path.dirname(args.input_txt) or '.')

if __name__ == '__main__':
    main()
