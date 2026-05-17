#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd


def clean_columns(columns, rpm_label):
    cleaned = [col.strip().replace(" ", "_") for col in columns]
    return [
        rpm_label if any(kw in col.lower() for kw in ["engine_speed", "enginespeed", "engine speed", "rpm"])
        else col
        for col in cleaned
    ]


def clean_file(input_file, rpm_label, output_file):
    input_file = Path(input_file)
    if not input_file.is_file():
        raise FileNotFoundError(f"Missing input file: {input_file.resolve()}")
    df = pd.read_csv(input_file)
    df.columns = clean_columns(df.columns, rpm_label)
    output_path = Path(output_file)
    if not output_path.is_absolute():
        output_path = input_file.parent / output_path
    df.to_csv(output_path, index=False)
    print(f"Wrote {output_path}")


def main():
    p = argparse.ArgumentParser(description="Clean Torque and FIC6 column headers and standardize RPM columns.")
    p.add_argument('--torque-in', default='torque_log.csv')
    p.add_argument('--fic6-in', default='fic6.csv')
    p.add_argument('--torque-out', default='cleaned_torque_log.csv')
    p.add_argument('--fic6-out', default='cleaned_fic6.csv')
    args = p.parse_args()

    clean_file(args.torque_in, 'RPM_A', args.torque_out)
    clean_file(args.fic6_in, 'RPM_B', args.fic6_out)
    print("Sanitization and renaming complete!")


if __name__ == '__main__':
    main()
