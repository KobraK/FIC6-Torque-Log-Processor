# FIC6 Torque Processor

Windows GUI for processing FIC6 and Torque logs.

## Repo Layout

- `src/` - Python GUI and processing scripts
- `scripts/` - setup and portable EXE build scripts
- `docs/` - user-facing notes and release instructions
- `examples/` - demo FIC6 and Torque logs
- `release/` - portable files ready to share
- `requirements.txt` - Python dependencies

## Portable Release

The ready-to-share app is:

```text
release/FIC6_Torque_Processor.exe
```

Include `release/START_HERE.txt` with the EXE when sharing it with basic users.

## Run From Source

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

## Build Portable EXE

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_portable.ps1
```

The build output is written to `release/`.
