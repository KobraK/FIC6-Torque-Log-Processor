Path-fix build

Replace your old files with these files in one folder. Run main.py from that folder.

What changed:
- main.py now runs helper scripts by absolute path beside main.py.
- main.py sets the working folder to the selected FIC6/Torque log folder, so generated CSVs stay with the logs.
- txt_to_csv.py copies the Torque CSV to torque_log.csv in the FIC6 log folder.
- sanitize_column_headers_2ndstep_time.py no longer contains a pasted duplicate GUI block.
- resample_merge.py outputs __time instead of Time so later scripts work.
- rpm_offset_correction.py, fuel_trim_analysis.py, and the interactive plot tolerate older files that still use Time.

Normal button order:
1. Text to CSV
2. Sanitize Headers
3. Sanitize 2nd Step
4. Resample & Merge
5. RPM Offset Correction
6. AFR Analysis / Fuel Trim Analysis / Interactive Plot
