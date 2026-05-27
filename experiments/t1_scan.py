import os
import time
import numpy as np
import matplotlib.pyplot as plt
from instruments.shfqc import VirtualSHFQC
from fitting_algorithms.exponential_decay import ExponentialDecay

try: from tqdm import tqdm
except ImportError: tqdm = lambda x, **k: x


class T1Scan:
    def __init__(self, dut, readout_frequency, readout_power, qubit_frequency, qubit_power, pi_time, shfqc_ifbw, shfqc_averages, start_time, stop_time, dense_sweep_points, s21_dir, plots_dir, logs_path):
        self.dut = dut
        self.readout_frequency = readout_frequency
        self.qubit_frequency = qubit_frequency
        self.start_time = start_time
        self.stop_time = stop_time
        self.pi_time = pi_time
        self.readout_power = readout_power
        self.qubit_power = qubit_power
        self.shfqc_ifbw = shfqc_ifbw
        self.shfqc_averages = int(shfqc_averages)
        self.dense_sweep_points = int(dense_sweep_points)
        self.s21_dir = s21_dir
        self.plots_dir = plots_dir
        self.logs_path = logs_path

        self.shfqc = VirtualSHFQC()
        self.shfqc.readout_freq = self.readout_frequency
        self.shfqc.ifbw = self.shfqc_ifbw
        self.shfqc.averages = self.shfqc_averages
        self.shfqc.power_dbm = self.readout_power
        self.shfqc.frame_freq = self.qubit_frequency
        self.scan_counter = 0

    def _log(self, log):
        print(log)
        if self.logs_path:
            with open(self.logs_path, "a") as f:
                f.write(log + "\n")

    def shfqc_data_fetcher(self):
        times, s21_complex = [], []
        
        sweep_points = self.dense_sweep_points
        time_array = np.linspace(self.start_time, self.stop_time, sweep_points)

        self.shfqc.clear_waveforms()
        self.dut.reset_state()
        ref_s21 = self.shfqc.read_single_point(self.dut)
        
        drive_freq = self.qubit_frequency
        
        for wait in tqdm(time_array, desc="Acquiring", unit="pts", leave=False):
            self.shfqc.clear_waveforms()
            if self.pi_time > 0:
                self.shfqc.add_square(start_time=0, duration=self.pi_time, power=self.qubit_power, freq=drive_freq, conversion_factor=self.dut.conversion_factor)
            
            t_second_pulse = self.pi_time + wait
            self.shfqc.add_square(start_time=t_second_pulse, duration=1e-10, power=-100.0, freq=drive_freq, conversion_factor=self.dut.conversion_factor)
            
            s21 = self.shfqc.read_single_point(self.dut)
            times.append(wait)
            s21_complex.append(s21)
        
        raw_data_filename = f"raw_data_{self.qubit_power}dBm_dense.npz"
        raw_data_path = os.path.join(self.s21_dir, raw_data_filename)
        np.savez(raw_data_path, times=np.array(times), s21=np.array(s21_complex))

        self.scan_counter += 1
        return np.array(times), np.array(s21_complex), ref_s21

    def run(self):
        start = time.time()
        self._log(f"--- [T1 Decay Experiment] ---")
        self._log(f"  Drive: {self.qubit_power} dBm @ {self.qubit_frequency/1e9:.4f} GHz")
        self._log(f"  Pi-Pulse: {self.pi_time*1e9:.2f} ns\n")

        fitter = ExponentialDecay(fetch_data=self.shfqc_data_fetcher)
        
        freq, t1, plots_dict, (t_arr, y_arr) = fitter.fitting_routine()
        
        np.savez(os.path.join(self.s21_dir, f"raw_data_{self.qubit_power}dBm_compiled.npz"), times=t_arr, mags=y_arr)
        
        for key, fig in plots_dict.items():
            plot_filename = f"{key}_{self.qubit_power}dBm.png"
            plots_path = os.path.join(self.plots_dir, plot_filename)
            fig.savefig(plots_path, dpi=150)
            plt.close(fig)
        
        self._log(f"--- T1 RELAXATION FOUND ---")
        self._log(f"T1: {t1*1e9:.2f} ns\n")
        
        stop = time.time()
        self._log(f"Time taken: {(stop-start):.2f}s\n")        
        return t1
    