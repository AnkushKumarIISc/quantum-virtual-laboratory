import os
import time
import numpy as np
import matplotlib.pyplot as plt
from instruments.shfqc import VirtualSHFQC
from fitting_algorithms.exponentially_decaying_sinusoid import ExponentiallyDecayingSinusoid

try: from tqdm import tqdm
except ImportError: tqdm = lambda x, **k: x


class RabiScan:
    def __init__(self, dut, naive, readout_frequency, readout_power, qubit_frequency, qubit_powers, shfqc_ifbw, shfqc_averages, start_time, stop_time, coarse_sweep_points, dense_sweep_points, adaptive_points, s21_dir, plots_dir, logs_path):    
        self.dut = dut
        self.naive = naive
        self.readout_frequency = readout_frequency
        self.qubit_frequency = qubit_frequency
        self.start_time = start_time
        self.stop_time = stop_time
        self.readout_power = readout_power
        self.qubit_powers = qubit_powers
        self.shfqc_ifbw = shfqc_ifbw
        self.shfqc_averages = int(shfqc_averages)
        self.coarse_sweep_points = int(coarse_sweep_points)
        self.dense_sweep_points = int(dense_sweep_points)
        self.adaptive_points = int(adaptive_points)
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
        self.current_power = None

    def _log(self, log):
        print(log)
        if self.logs_path:
            with open(self.logs_path, "a") as f:
                f.write(log + "\n")

    def shfqc_data_fetcher(self, t_array=None):
        times, s21_complex = [], []
        
        if t_array is not None:
            time_array = np.asarray(t_array)
        else:
            sweep_points = self.dense_sweep_points if self.naive else self.coarse_sweep_points
            time_array = np.linspace(self.start_time, self.stop_time, sweep_points)

        self.shfqc.clear_waveforms()
        self.dut.reset_state()
        ref_s21 = self.shfqc.read_single_point(self.dut)
        
        for t in tqdm(time_array, desc="Acquiring", unit="pts", leave=False):
            self.shfqc.clear_waveforms()
            if t > 0:
                self.shfqc.add_square(0, t, self.current_power, self.qubit_frequency, self.dut.conversion_factor)
            
            s21 = self.shfqc.read_single_point(self.dut)
            times.append(t)
            s21_complex.append(s21)
        
        if self.naive or (t_array is not None and len(t_array) > 1):
            suffix = "dense" if self.naive else "scout"
            raw_data_filename = f"raw_data_{self.current_power}dBm_{suffix}.npz"
            raw_data_path = os.path.join(self.s21_dir, raw_data_filename)
            np.savez(raw_data_path, times=np.array(times), s21=np.array(s21_complex))

        self.scan_counter += 1
        return np.array(times), np.array(s21_complex), ref_s21

    def run(self):
        start = time.time()
        self._log(f"--- [Rabi Experiment] ---")
        self._log(f"  Frame Freq: {self.qubit_frequency/1e9:.4f} GHz\n")
        
        results = {}
        compiled_times = []
        compiled_mags = []
        
        for power in self.qubit_powers:
            self.current_power = power
            self._log(f"--- Qubit Power {power} dBm ---")
            
            fitter = ExponentiallyDecayingSinusoid(
                naive=self.naive,
                coarse_sweep_points=self.coarse_sweep_points,
                adaptive_points=self.adaptive_points,
                stop_time=self.stop_time,
                fetch_data=self.shfqc_data_fetcher
            )
            
            freq, decay, plots_dict, (t_arr, y_arr) = fitter.fitting_routine()
            
            pi_pulse = 1.0 / (2.0 * freq) if freq > 1e-6 else 0.0
            results[power] = (freq, pi_pulse, decay)
            
            self._log(f"Rabi Freq: {freq/1e6:.4f} MHz | Pi Pulse: {pi_pulse*1e9:.4f} ns | Decay: {decay*1e9:.4f} ns\n")
            
            compiled_times.append(t_arr)
            compiled_mags.append(y_arr)
            
            np.savez(os.path.join(self.s21_dir, f"raw_data_{power}dBm_compiled.npz"), times=t_arr, mags=y_arr)
            
            for key, fig in plots_dict.items():
                fig.savefig(os.path.join(self.plots_dir, f"{key}_{power}dBm.png"), dpi=150)
                plt.close(fig)
            
        if len(self.qubit_powers) > 1:
            plt.figure(figsize=(10, 6))
            plt.title("Compiled Data")
            for t, m, p in zip(compiled_times, compiled_mags, self.qubit_powers):
                idx = np.argsort(t)
                t = t[idx]
                m = m[idx]
                plt.plot(t*1e9, m, 'o-', markersize=3, label=f"{p} dBm")
            plt.xlabel("Time (ns)")
            plt.ylabel("Normalized Magnitude")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(self.plots_dir, "compiled_data.png"), dpi=150)
            plt.close()
            
        stop = time.time()
        self._log(f"--- RABI OSCILLATIONS FOUND ---")
        self._log(f"Time taken: {(stop-start):.2f}s\n")     

        return results
    