#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd


def strip_tz_text(series):
    # Torque exported strings often end in EDT/EST. Remove common suffixes before parsing.
    return (series.astype(str)
            .str.replace("EDT", "", regex=False)
            .str.replace("EST", "", regex=False)
            .str.strip())


def main(rpm_threshold: float, torque_csv: str, fic6_csv: str, out_torque: str, out_fic6: str):
    torque_csv = Path(torque_csv)
    fic6_csv = Path(fic6_csv)

    if not torque_csv.is_file():
        raise FileNotFoundError(f"Missing torque input: {torque_csv.resolve()}")
    if not fic6_csv.is_file():
        raise FileNotFoundError(f"Missing FIC6 input: {fic6_csv.resolve()}")

    dfa = pd.read_csv(torque_csv)
    dfb = pd.read_csv(fic6_csv)

    if 'RPM_A' not in dfa.columns:
        raise KeyError("RPM_A not found in torque log. Run sanitize_column_headers.py first.")
    if 'RPM_B' not in dfb.columns:
        raise KeyError("RPM_B not found in FIC6 data. Run sanitize_column_headers.py first.")
    if 'GPS_Time' not in dfa.columns:
        raise KeyError("GPS_Time not found in cleaned torque log.")
    if 'Time/s' not in dfb.columns:
        raise KeyError("Time/s not found in cleaned FIC6 log.")

    dfa['RPM_A'] = pd.to_numeric(dfa['RPM_A'], errors='coerce')
    dfb['RPM_B'] = pd.to_numeric(dfb['RPM_B'], errors='coerce')

    base_time = pd.to_datetime(strip_tz_text(dfa['GPS_Time']).iloc[0], errors='coerce')
    if pd.isna(base_time):
        raise ValueError("Could not parse first GPS_Time in torque log.")

    dfb['__time'] = base_time + pd.to_timedelta(dfb['Time/s'], unit='s')
    dfa['__time'] = pd.to_datetime(strip_tz_text(dfa['GPS_Time']), errors='coerce')

    try:
        t_evt = dfa.loc[dfa['RPM_A'] > rpm_threshold, '__time'].dropna().iloc[0]
        f_evt = dfb.loc[dfb['RPM_B'] > rpm_threshold, '__time'].dropna().iloc[0]
    except IndexError:
        raise ValueError(f"No RPM event above {rpm_threshold} found. Choose a lower threshold or check your data.")

    offset = t_evt - f_evt
    dfb['__time'] = dfb['__time'] + offset
    print(f"[INFO] Aligned FIC-6 to torque log on RPM>{rpm_threshold}: applied offset {offset}.")

    torque_out = Path(out_torque)
    fic6_out = Path(out_fic6)
    if not torque_out.is_absolute():
        torque_out = torque_csv.parent / torque_out
    if not fic6_out.is_absolute():
        fic6_out = torque_csv.parent / fic6_out

    dfa.to_csv(torque_out, index=False)
    dfb.to_csv(fic6_out, index=False)
    print(f"[INFO] Saved: {torque_out}, {fic6_out}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Align torque and FIC6 logs by GPS start + RPM event shift")
    p.add_argument('--rpm_threshold', type=float, default=300.0, help="RPM threshold for event-based alignment")
    p.add_argument('--torque-csv', default='cleaned_torque_log.csv')
    p.add_argument('--fic6-csv', default='cleaned_fic6.csv')
    p.add_argument('--out-torque', default='aligned_cleaned_torque_log.csv')
    p.add_argument('--out-fic6', default='aligned_cleaned_fic6.csv')
    args = p.parse_args()
    main(args.rpm_threshold, args.torque_csv, args.fic6_csv, args.out_torque, args.out_fic6)
