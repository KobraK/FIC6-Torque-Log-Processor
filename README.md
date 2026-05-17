# FIC6 <-> Torque Log Processor

A small Python/Tkinter utility for converting, cleaning, aligning, merging, and analyzing AEM FIC6 logs with Torque/tracklog CSV data.

This tool was built around the Scion xA / 1NZ-FE turbo tuning workflow, but the pipeline is generic enough for any setup where you need to line up a tab-delimited FIC6 log with a timestamped Torque CSV.

## What it does

The GUI in `main.py` runs the pipeline in order:

1. Convert the FIC6 `.txt` log into `fic6.csv`.
2. Copy the selected Torque/tracklog CSV into the same working folder as `torque_log.csv`.
3. Clean column headers and normalize RPM columns.
4. Build aligned time columns using Torque GPS time plus FIC6 elapsed seconds.
5. Align both logs using an RPM threshold event.
6. Resample and merge both logs into a fused dataset.
7. Correct RPM offset between ECU/Torque and FIC6 data.
8. Run AFR and fuel-trim analysis.
9. Generate an interactive Plotly time-series HTML file.

## Requirements

- Windows, Linux, or macOS
- Python 3.10+
- Tkinter support for the GUI
- Python packages:
  - `pandas`
  - `numpy`
  - `plotly` for the interactive plot

Install the packages:

```bash
python -m pip install pandas numpy plotly
```

On Windows, use the same Python executable that runs the tool:

```powershell
py -m pip install pandas numpy plotly
```

## Files

| File | Purpose |
|---|---|
| `main.py` | Tkinter GUI and pipeline runner |
| `txt_to_csv.py` | Converts FIC6 tab-delimited `.txt` to `fic6.csv`; copies Torque CSV to `torque_log.csv` |
| `sanitize_column_headers.py` | Cleans column names and renames RPM columns to `RPM_A` and `RPM_B` |
| `sanitize_column_headers_2ndstep_time.py` | Creates `__time` columns and aligns FIC6/Torque logs using RPM event offset |
| `resample_merge.py` | Resamples, interpolates/forward-fills, and merges aligned logs |
| `rpm_offset_correction.py` | Calculates and applies mean RPM offset correction |
| `AFR_analysis_by_powerband.py` | Summarizes AFR by load/power band |
| `fuel_trim_analysis.py` | Analyzes LTFT/STFT by RPM and MAP/PSIA bins |
| `interactive_plot_corrected_auto.py` | Creates an interactive HTML time-series plot |

## Quick start

1. Put all `.py` files in the same folder.
2. Run:

```bash
python main.py
```

3. In the GUI, select:
   - your FIC6 `.txt` log
   - your Torque/tracklog `.csv`
4. Click the buttons in this order:

```text
Text to CSV
Sanitize Headers
Sanitize 2nd Step
Resample & Merge
RPM Offset Correction
AFR Analysis
Fuel Trim Analysis
Interactive Plot
```

The patched version resolves scripts relative to `main.py`, so it no longer fails when Python starts from `C:\Users\sputnik` or another unrelated working directory.

## Windows setup

On Windows 10/11, run the setup script from inside the `tuning tool` folder:

```powershell
.\setup_windows.bat
```

It creates a local `.venv`, installs `pandas`, `numpy`, and `plotly`, and launches the GUI.

## Input expectations

### FIC6 log

Expected format:

- tab-delimited `.txt`
- includes elapsed time column such as `Time/s`
- includes RPM and AFR-related columns

### Torque/tracklog CSV

Expected format:

- CSV exported from Torque or similar logger
- includes a GPS timestamp column such as `GPS_Time`
- includes engine speed/RPM
- may include fuel trims, engine load, MAP, or related ECU data

## Output files

The tool writes output files into the same folder as the selected FIC6 `.txt` log.

| Output | Description |
|---|---|
| `fic6.csv` | Converted FIC6 CSV |
| `torque_log.csv` | Copied/standardized Torque CSV |
| `cleaned_fic6.csv` | Header-normalized FIC6 data |
| `cleaned_torque_log.csv` | Header-normalized Torque data |
| `aligned_cleaned_fic6.csv` | FIC6 data with aligned `__time` |
| `aligned_cleaned_torque_log.csv` | Torque data with parsed `__time` |
| `fused.csv` | Resampled and merged data |
| `fused_corrected.csv` | Merged data with corrected FIC6 RPM |
| `fuel_trim_issues.csv` | Rows where fuel trims exceed thresholds |
| `fuel_trim_issue_blocks.csv` | Continuous fuel-trim issue blocks |
| `fuel_trim_summary.csv` | Fuel-trim recommendation summary by RPM/load bin |
| `interactive_time_series_corrected.html` | Interactive Plotly chart |

## Command-line usage

Each script can also be run manually.

```bash
python txt_to_csv.py "path/to/fic6_log.txt" "path/to/tracklog.csv"
python sanitize_column_headers.py
python sanitize_column_headers_2ndstep_time.py --rpm_threshold 300
python resample_merge.py aligned_cleaned_torque_log.csv aligned_cleaned_fic6.csv fused.csv --freq 10ms --interp --rpm-limit 40
python rpm_offset_correction.py fused.csv fused_corrected.csv
python AFR_analysis_by_powerband.py fused_corrected.csv
python fuel_trim_analysis.py fused_corrected.csv --min-rpm 0 --load-bins "0,3,5,7,10,13,14.7,15,16,17,20,22" --atm-psia 14.7
python interactive_plot_corrected_auto.py
```

## Common fixes

### `can't open file C:\Users\sputnik\txt_to_csv.py`

This means the GUI or shell is trying to run scripts from the wrong folder. Use the patched `main.py`; it resolves helper scripts relative to the folder containing `main.py`.

### Missing `cleaned_fic6.csv` or `cleaned_torque_log.csv`

Run `Text to CSV` first, then `Sanitize Headers`.

### No RPM event above threshold

Lower the RPM threshold in the GUI. The default is `300`, but some logs may need a lower threshold.

### Plotly missing

Click `Install Dependencies` in the GUI, or run:

```bash
python -m pip install -r "tuning tool/requirements.txt"
```

## Notes

This is a tuning-analysis helper, not a replacement for safe mechanical testing. Treat the analysis output as a decision-support tool and verify changes with short, controlled logs.
