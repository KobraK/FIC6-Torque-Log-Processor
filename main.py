import sys
import subprocess
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, scrolledtext, messagebox
except ImportError:
    sys.exit("Tkinter is required for this GUI.")

APP_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = APP_DIR / "requirements.txt"
output_text = None


def script_path(script_name: str) -> str:
    """Return the absolute path to a helper script living beside main.py."""
    path = APP_DIR / script_name
    if not path.is_file():
        raise FileNotFoundError(f"Missing helper script beside main.py: {path}")
    return str(path)


def selected_workdir(fic6_path: str = "", torque_path: str = "") -> Path:
    """
    Put generated files beside the selected log files.
    This avoids writing into C:\\Users\\sputnik or wherever Python was launched from.
    """
    for candidate in (fic6_path, torque_path):
        if candidate:
            p = Path(candidate).expanduser()
            if p.is_file():
                return p.resolve().parent
    return APP_DIR


def run_script(script, *args, cwd=None):
    """Run one helper script by absolute path, with a controlled working directory."""
    try:
        script_abs = script_path(script)
    except FileNotFoundError as e:
        output_text.insert(tk.END, f"\n{e}\n")
        output_text.see(tk.END)
        return False

    workdir = Path(cwd).resolve() if cwd else APP_DIR
    cmd = [sys.executable, script_abs] + [str(a) for a in args if str(a) != ""]
    output_text.insert(tk.END, f"\n> Working folder: {workdir}\n")
    output_text.insert(tk.END, f"> Running: {subprocess.list2cmdline(cmd)}\n")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            check=True,
        )
        if proc.stdout:
            output_text.insert(tk.END, proc.stdout + "\n")
        if proc.stderr:
            output_text.insert(tk.END, proc.stderr + "\n")
        ok = True
    except subprocess.CalledProcessError as e:
        output_text.insert(tk.END, f"Error running {script}:\n")
        if e.stdout:
            output_text.insert(tk.END, e.stdout + "\n")
        if e.stderr:
            output_text.insert(tk.END, e.stderr + "\n")
        ok = False
    output_text.see(tk.END)
    return ok


def install_deps():
    if REQUIREMENTS_FILE.is_file():
        cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(REQUIREMENTS_FILE)]
    else:
        cmd = [sys.executable, '-m', 'pip', 'install', 'pandas', 'numpy', 'plotly']
    output_text.insert(tk.END, f"\n> Running: {subprocess.list2cmdline(cmd)}\n")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if proc.stdout:
            output_text.insert(tk.END, proc.stdout + "\n")
        if proc.stderr:
            output_text.insert(tk.END, proc.stderr + "\n")
        output_text.insert(tk.END, "Dependencies installed.\n")
    except subprocess.CalledProcessError as e:
        output_text.insert(tk.END, "Error installing dependencies:\n")
        if e.stdout:
            output_text.insert(tk.END, e.stdout + "\n")
        if e.stderr:
            output_text.insert(tk.END, e.stderr + "\n")
    output_text.see(tk.END)


def require_fic6(fic6_path: str) -> bool:
    if not fic6_path or not Path(fic6_path).is_file():
        messagebox.showwarning('Missing File', 'Select a FIC6 .txt file first.')
        return False
    return True


def run_text_to_csv(fic6_path: str, torque_path: str):
    if not require_fic6(fic6_path):
        return
    cwd = selected_workdir(fic6_path, torque_path)
    args = [fic6_path]
    if torque_path and Path(torque_path).is_file():
        args.append(torque_path)
    run_script('txt_to_csv.py', *args, cwd=cwd)


def run_in_log_folder(script: str, fic6_path: str, torque_path: str, *args):
    cwd = selected_workdir(fic6_path, torque_path)
    run_script(script, *args, cwd=cwd)


def create_gui():
    root = tk.Tk()
    root.title('FIC6 <-> Torque Processor')

    frame_files = tk.Frame(root, pady=5)
    frame_files.pack(fill=tk.X)

    tk.Label(frame_files, text='FIC6 Log (.txt):', width=15, anchor='w').grid(row=0, column=0, padx=5)
    fic6_entry = tk.Entry(frame_files)
    fic6_entry.grid(row=0, column=1, sticky='we', padx=5)
    tk.Button(frame_files, text='Browse', command=lambda: browse_file(fic6_entry, [('Text Files','*.txt')])).grid(row=0, column=2)

    tk.Label(frame_files, text='Torque Log (.csv):', width=15, anchor='w').grid(row=1, column=0, padx=5)
    torque_entry = tk.Entry(frame_files)
    torque_entry.grid(row=1, column=1, sticky='we', padx=5)
    tk.Button(frame_files, text='Browse', command=lambda: browse_file(torque_entry, [('CSV Files','*.csv')])).grid(row=1, column=2)
    frame_files.columnconfigure(1, weight=1)

    frame_params = tk.Frame(root, pady=5)
    frame_params.pack(fill=tk.X)

    tk.Label(frame_params, text='Sanitize RPM Threshold:', width=20, anchor='w').grid(row=0, column=0, padx=5)
    sanitize_rpm_entry = tk.Entry(frame_params)
    sanitize_rpm_entry.insert(0, '300')
    sanitize_rpm_entry.grid(row=0, column=1, sticky='we', padx=5)

    tk.Label(frame_params, text='Merge RPM Limit:', width=20, anchor='w').grid(row=1, column=0, padx=5)
    merge_limit_entry = tk.Entry(frame_params)
    merge_limit_entry.insert(0, '40')
    merge_limit_entry.grid(row=1, column=1, sticky='we', padx=5)

    tk.Label(frame_params, text='Resample Frequency:', width=20, anchor='w').grid(row=2, column=0, padx=5)
    freq_entry = tk.Entry(frame_params)
    freq_entry.insert(0, '10ms')
    freq_entry.grid(row=2, column=1, sticky='we', padx=5)

    interp_var = tk.BooleanVar(value=True)
    tk.Checkbutton(frame_params, text='Interpolate', variable=interp_var).grid(row=3, column=0, columnspan=2, padx=5)

    tk.Label(frame_params, text='Fuel Trim Min RPM:', width=20, anchor='w').grid(row=4, column=0, padx=5)
    fueltrim_minrpm_entry = tk.Entry(frame_params)
    fueltrim_minrpm_entry.insert(0, '0')
    fueltrim_minrpm_entry.grid(row=4, column=1, sticky='we', padx=5)

    tk.Label(frame_params, text='Load Bins (PSIA):', width=20, anchor='w').grid(row=5, column=0, padx=5)
    loadbins_entry = tk.Entry(frame_params)
    loadbins_entry.insert(0, '0,3,5,7,10,13,14.7,15,16,17,20,22')
    loadbins_entry.grid(row=5, column=1, sticky='we', padx=5)

    tk.Label(frame_params, text='Atmospheric PSIA:', width=20, anchor='w').grid(row=6, column=0, padx=5)
    atm_entry = tk.Entry(frame_params)
    atm_entry.insert(0, '14.7')
    atm_entry.grid(row=6, column=1, sticky='we', padx=5)
    frame_params.columnconfigure(1, weight=1)

    frame_buttons = tk.Frame(root, pady=5)
    frame_buttons.pack(side=tk.LEFT, fill=tk.Y, padx=5)

    tk.Button(frame_buttons, text='Text to CSV', width=20,
              command=lambda: run_text_to_csv(fic6_entry.get(), torque_entry.get())).pack(pady=2)
    tk.Button(frame_buttons, text='Sanitize Headers', width=20,
              command=lambda: run_in_log_folder('sanitize_column_headers.py', fic6_entry.get(), torque_entry.get())).pack(pady=2)
    tk.Button(frame_buttons, text='Sanitize 2nd Step', width=20,
              command=lambda: run_in_log_folder(
                  'sanitize_column_headers_2ndstep_time.py', fic6_entry.get(), torque_entry.get(),
                  '--rpm_threshold', sanitize_rpm_entry.get()
              )).pack(pady=2)
    tk.Button(frame_buttons, text='Resample & Merge', width=20,
              command=lambda: run_in_log_folder(
                  'resample_merge.py', fic6_entry.get(), torque_entry.get(),
                  'aligned_cleaned_torque_log.csv',
                  'aligned_cleaned_fic6.csv',
                  'fused.csv',
                  '--freq', freq_entry.get(),
                  *(['--interp'] if interp_var.get() else []),
                  '--rpm-limit', merge_limit_entry.get()
              )).pack(pady=2)
    tk.Button(frame_buttons, text='RPM Offset Correction', width=20,
              command=lambda: run_in_log_folder(
                  'rpm_offset_correction.py', fic6_entry.get(), torque_entry.get(), 'fused.csv', 'fused_corrected.csv'
              )).pack(pady=2)
    tk.Button(frame_buttons, text='AFR Analysis', width=20,
              command=lambda: run_in_log_folder(
                  'AFR_analysis_by_powerband.py', fic6_entry.get(), torque_entry.get(), 'fused_corrected.csv'
              )).pack(pady=2)
    tk.Button(frame_buttons, text='Fuel Trim Analysis', width=20,
              command=lambda: run_in_log_folder(
                  'fuel_trim_analysis.py', fic6_entry.get(), torque_entry.get(), 'fused_corrected.csv',
                  '--min-rpm', fueltrim_minrpm_entry.get(),
                  '--load-bins', loadbins_entry.get(),
                  '--atm-psia', atm_entry.get()
              )).pack(pady=2)
    tk.Button(frame_buttons, text='Install Dependencies', width=20, command=install_deps).pack(pady=2)
    tk.Button(frame_buttons, text='Interactive Plot', width=20,
              command=lambda: run_in_log_folder('interactive_plot_corrected_auto.py', fic6_entry.get(), torque_entry.get(), 'fused_corrected.csv')).pack(pady=2)
    tk.Button(frame_buttons, text='Exit', width=20, command=root.quit).pack(pady=10)

    frame_output = tk.Frame(root)
    frame_output.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    global output_text
    output_text = scrolledtext.ScrolledText(frame_output, wrap=tk.WORD, width=90, height=24)
    output_text.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


def browse_file(entry, filetypes):
    path = filedialog.askopenfilename(filetypes=filetypes)
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)


if __name__ == '__main__':
    create_gui()
