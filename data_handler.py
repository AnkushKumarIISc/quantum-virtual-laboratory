import os
from datetime import datetime
import shutil


def generate_data_folder():
    run_timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    base_dir = os.path.join("data", run_timestamp)

    paths = {
        "resonator_scan_s21":  os.path.join(base_dir, "resonator_scan", "s21"),
        "resonator_scan_plots": os.path.join(base_dir, "resonator_scan", "plots"),
        "resonator_scan_logs": os.path.join(base_dir, "resonator_scan", "logs.txt"),
        
        "qubit_scan_s21":   os.path.join(base_dir, "qubit_scan", "s21"),
        "qubit_scan_plots":  os.path.join(base_dir, "qubit_scan", "plots"),
        "qubit_scan_logs": os.path.join(base_dir, "qubit_scan", "logs.txt"),

        "rabi_scan_s21":   os.path.join(base_dir, "rabi_scan", "s21"),
        "rabi_scan_plots":  os.path.join(base_dir, "rabi_scan", "plots"),
        "rabi_scan_logs": os.path.join(base_dir, "rabi_scan", "logs.txt"),
        
        "ramsey_scan_s21":   os.path.join(base_dir, "ramsey_scan", "s21"),
        "ramsey_scan_plots":  os.path.join(base_dir, "ramsey_scan", "plots"),
        "ramsey_scan_logs": os.path.join(base_dir, "ramsey_scan", "logs.txt"),
        
        "t1_scan_s21":   os.path.join(base_dir, "t1_scan", "s21"),
        "t1_scan_plots":  os.path.join(base_dir, "t1_scan", "plots"),
        "t1_scan_logs": os.path.join(base_dir, "t1_scan", "logs.txt"),
    }

    for path in paths.values():
        if not path.endswith(".txt"):
            os.makedirs(path, exist_ok=True)

    shutil.copy("config.py", os.path.join(base_dir, "config_snapshot.txt"))

    return paths
