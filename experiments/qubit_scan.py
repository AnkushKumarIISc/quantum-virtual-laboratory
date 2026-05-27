import os
import time
import numpy as np
import matplotlib.pyplot as plt
from instruments.vna import VirtualVNA
from instruments.sg import VirtualSG
from fitting_algorithms.lorentzian import Lorentzian

try: from tqdm import tqdm
except ImportError: tqdm = lambda x, **k: x


class QubitScan:
    def __init__(self, dut, naive, transmission_coupled, readout_frequency, readout_power, vna_ifbw, vna_averages, start_freq, stop_freq, coarse_sweep_points, dense_sweep_points, adaptive_sweep_points, adaptive_iterations, sg_powers, s21_dir, plots_dir, logs_path):
        self.dut = dut
        self.naive = naive
        self.transmission_coupled = transmission_coupled
        self.readout_frequency = readout_frequency
        self.readout_power = readout_power
        self.vna_ifbw = vna_ifbw
        self.vna_averages = int(vna_averages)
        self.start_freq = start_freq
        self.stop_freq = stop_freq
        self.coarse_sweep_points = int(coarse_sweep_points)
        self.dense_sweep_points = int(dense_sweep_points)
        self.adaptive_sweep_points = int(adaptive_sweep_points)
        self.adaptive_iterations = int(adaptive_iterations)
        self.sg_powers = sg_powers
        self.s21_dir = s21_dir
        self.plots_dir = plots_dir
        self.logs_path = logs_path

        self.sg = VirtualSG(self.dut)
        self.vna = VirtualVNA()
        self.vna.readout_freq = self.readout_frequency
        self.vna.ifbw = self.vna_ifbw
        self.vna.averages = self.vna_averages
        self.vna.power_dbm = self.readout_power
        
        self.scan_counter = 0

    def _log(self, log):
        if self.logs_path:
            with open(self.logs_path, "a") as f:
                f.write(log + "\n")

    def vna_data_fetcher(self, new_freqs=None):
        freqs, s21_complex = [], []
        self.sg.on()
        
        if new_freqs is not None:
            suffix = f"{self.scan_counter}_adaptive"
            for freq in tqdm(new_freqs, desc="Acquiring", unit="pts"):
                self.sg.set_cw_tone(freq)
                s21 = self.vna.read_single_point(self.dut)
                freqs.append(freq)
                s21_complex.append(s21)
        else:
            suffix = "dense" if self.naive else "0_coarse"
            for freq in tqdm(np.linspace(self.start_freq, self.stop_freq, self.dense_sweep_points if self.naive else self.coarse_sweep_points), desc="Acquiring", unit="pts"):
                self.sg.set_cw_tone(freq)
                s21 = self.vna.read_single_point(self.dut)
                freqs.append(freq)
                s21_complex.append(s21)
        
        self.sg.off()
        
        raw_data_filename = f"raw_data_{self.sg.power_dbm}dBm_{suffix}.npz"
        raw_data_path = os.path.join(self.s21_dir, raw_data_filename)
        np.savez(raw_data_path, freqs=np.array(freqs), s21=np.array(s21_complex))

        self.scan_counter += 1
        return np.array(freqs), np.array(s21_complex)

    def run(self):
        start = time.time()
        self._log(f"--- SIMULATED QUBIT SCAN LOG ---\n")

        lorentzian = Lorentzian(
            naive=self.naive,
            transmission_coupled=self.transmission_coupled,
            adaptive_sweep_points=self.adaptive_sweep_points,
            adaptive_iterations=self.adaptive_iterations,
            fetch_data=self.vna_data_fetcher
        )
        
        power_sweep_results = []
        compiled_freqs = []
        compiled_mags = []
        
        for power in self.sg_powers:
            loop_start_time = time.time()
            print(f"--- SG Power {power} dBm ---\n")
            self.sg.set_power(power)
            self.scan_counter = 0
            
            f0, kappa, plots_dict, (freqs, s21_mag) = lorentzian.fitting_routine()
            power_sweep_results.append((power, f0, kappa))
            compiled_freqs.append(freqs)
            compiled_mags.append(s21_mag)
            
            for key, fig in plots_dict.items():
                plot_filename = f"{key}_{self.sg.power_dbm}dBm.png"
                plots_path = os.path.join(self.plots_dir, plot_filename)
                fig.savefig(plots_path, dpi=150)
                plt.close(fig)
            
            self._log(f"Power: {power:>4} dBm | f0: {f0/1e9:.6f} GHz | kappa: {kappa/1e6:.4f} MHz | Time: {time.time() - loop_start_time:.2f}s\n")

        if len(self.sg_powers) > 1:
            plt.figure(figsize=(10, 6))
            plt.title("Compiled Data")
            for f, m, p in zip(compiled_freqs, compiled_mags, self.sg_powers):
                plt.plot(f/1e9, m, 'o-', markersize=3, label=f"{p} dBm")
            plt.xlabel("Frequency (GHz)")
            plt.ylabel("|S21|")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(self.plots_dir, "compiled_data.png"), dpi=150)
            plt.close()

        results_array = np.array(power_sweep_results)
        fitted_powers = results_array[:, 0]
        fitted_f0s = results_array[:, 1]
        fitted_kappas = results_array[:, 2]

        baseline_kappa = np.mean(fitted_kappas[:3])
        threshold_kappa = baseline_kappa * 1.20
        
        broadened_indices = np.where(fitted_kappas > threshold_kappa)[0]
        
        if len(broadened_indices) > 0:
            optimal_idx = broadened_indices[0] - 1
            optimal_idx = max(0, optimal_idx)
        else:
            optimal_idx = -1 
            
        drive_power = fitted_powers[optimal_idx]
        drive_frequency = fitted_f0s[optimal_idx]
        
        print(f"\n--- OPTIMAL DRIVE FOUND ---")
        print(f"Freq: {drive_frequency/1e9:.5f} GHz | Power: {drive_power} dBm")

        stop = time.time()
        print(f"Time taken: {(stop-start):.2f}s\n")        
        
        self._log(f"\n--- OPTIMAL DRIVE FOUND ---\n")
        self._log(f"Freq: {drive_frequency/1e9:.5f} GHz | Power: {drive_power} dBm\n")
        self._log(f"Total Sim Time: {(stop-start):.2f}s\n")
        return drive_frequency, drive_power
    