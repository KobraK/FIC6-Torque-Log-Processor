#!/usr/bin/env python3
import argparse
from pathlib import Path
import webbrowser
import pandas as pd
import plotly.express as px


def main():
    p = argparse.ArgumentParser(description="Create an interactive Plotly time-series HTML from a fused CSV.")
    p.add_argument('input_csv', nargs='?', default='fused_corrected.csv')
    p.add_argument('--output-html', default='interactive_time_series_corrected.html')
    args = p.parse_args()

    df = pd.read_csv(args.input_csv)
    if '__time' not in df.columns and 'Time' in df.columns:
        df = df.rename(columns={'Time': '__time'})
    if '__time' not in df.columns:
        raise KeyError("No __time or Time column found for plotting.")
    df['__time'] = pd.to_datetime(df['__time'], errors='coerce')

    metrics = [c for c in df.select_dtypes("number").columns]
    if not metrics:
        raise ValueError("No numeric columns found to plot.")

    melted = df.melt(id_vars="__time", value_vars=metrics, var_name="Metric", value_name="Value")
    fig = px.line(melted, x="__time", y="Value", color="Metric", title="Time-series of All Metrics")
    fig.update_layout(xaxis_title="Time", yaxis_title="Value", legend_title="Metric", hovermode="x unified")

    html_file = Path(args.output_html)
    if not html_file.is_absolute():
        html_file = Path(args.input_csv).resolve().parent / html_file
    html_file = html_file.resolve()
    fig.write_html(html_file, include_plotlyjs="cdn")
    print(f"Opening {html_file}")
    webbrowser.open(html_file.as_uri())


if __name__ == "__main__":
    main()
