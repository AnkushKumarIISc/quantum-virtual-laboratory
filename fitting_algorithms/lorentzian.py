### ADAPTIVE ALGORITHM BY ABHIJEET BHATTA ###

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


class Lorentzian:
    def __init__(self, naive, transmission_coupled, adaptive_sweep_points, adaptive_iterations, fetch_data):
        self.naive = naive
        self.transmission_coupled = transmission_coupled
        self.adaptive_sweep_points = adaptive_sweep_points
        self.adaptive_iterations = adaptive_iterations
        self.fetch_data = fetch_data

        self.f0_approx = None
        self.kappa_approx = None

    @staticmethod
    def transmission_lorentzian(f, f_r, kappa, baseline, separation):
        complex_s21 = baseline + separation / (1 + 1j * 2 * (f - f_r) / kappa)
        return np.abs(complex_s21)
    
    @staticmethod
    def side_coupled_lorentzian(f, f_r, kappa, baseline, separation):
        complex_s21 = baseline - separation / (1 + 1j * 2 * (f - f_r) / kappa)
        return np.abs(complex_s21)

    def generate_new_freqs(self):
        epsilon = 1e-6
        theta = np.linspace(np.pi/2 - epsilon, -np.pi/2 + epsilon, self.adaptive_sweep_points)
        new_freqs = self.f0_approx + self.kappa_approx * np.tan(theta)
        new_freqs = new_freqs[(new_freqs <= 1e10) & (new_freqs >= 1e9)]
        return np.sort(new_freqs)

    def fit(self, freqs, s21_mag):
        if self.transmission_coupled:
            f0_guess = freqs[np.argmax(s21_mag)] 
            baseline_guess = np.min(s21_mag) 
            separation_guess = np.max(s21_mag) - baseline_guess
            kappa_guess = np.abs((freqs[-1] - freqs[0])) / 10.0

            p0 = [f0_guess, kappa_guess, baseline_guess, separation_guess]
            bounds = ([0., 0., 0., 0.], [np.inf, np.inf, np.inf, np.inf])
            popt, _ = curve_fit(self.transmission_lorentzian, freqs, s21_mag, p0=p0, bounds=bounds, maxfev=1e6)
            return popt
        else:
            f0_guess = freqs[np.argmin(s21_mag)]
            baseline_guess = np.max(s21_mag)
            separation_guess = baseline_guess - np.min(s21_mag)
            kappa_guess = np.abs((freqs[-1] - freqs[0])) / 10.0

            p0 = [f0_guess, kappa_guess, baseline_guess, separation_guess]
            bounds = ([0., 0., 0., 0.], [np.inf, np.inf, np.inf, np.inf])
            popt, _ = curve_fit(self.side_coupled_lorentzian, freqs, s21_mag, p0=p0, bounds=bounds, maxfev=1e6)
            return popt

    def get_data_plot(self, freqs, s21_mag):    
        plt.figure(figsize=(10, 6))
        plt.title("Data")
        plt.plot(freqs/1e9, s21_mag, 'o-', markersize=4, label="Data", color="gray")
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("|S21|")
        plt.legend()
        plt.tight_layout()
        plt.grid(True, alpha=0.3)
        return plt.gcf()

    def get_fit_plot(self, freqs, s21_mag, popt, N=1e3):    
        freqs_fit = np.linspace(freqs.min(), freqs.max(), int(N))
        s21_fit = self.transmission_lorentzian(freqs_fit, *popt) if self.transmission_coupled else self.side_coupled_lorentzian(freqs_fit, *popt)
        plt.figure(figsize=(10, 6))
        plt.title("Fit")
        plt.plot(freqs/1e9, s21_mag, 'o', markersize=4, label="Data", color="gray")
        plt.plot(freqs_fit/1e9, s21_fit, "-", color="royalblue", lw=2, label="Fit")
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("|S21|")
        plt.legend()
        plt.tight_layout()
        plt.grid(True, alpha=0.3)
        return plt.gcf()

    def fitting_routine(self):
        freqs, s21_complex = self.fetch_data()
        s21_mag = np.abs(s21_complex)

        popt = self.fit(freqs, s21_mag)
        self.f0_approx = popt[0]
        self.kappa_approx = popt[1]
        print(f"f0 = {popt[0]/1e9:.4f} GHz, kappa = {np.abs(popt[1])/1e6:.4f} MHz\n")

        plots_dict = {
            "data_dense" if self.naive else "data_0_coarse": self.get_data_plot(freqs, s21_mag),
            "fitted_dense" if self.naive else "fitted_0_coarse": self.get_fit_plot(freqs, s21_mag, popt)
        }

        if not self.naive:
            for i in range(self.adaptive_iterations):
                new_sweep_freqs = self.generate_new_freqs()
                freqs, s21_complex = self.fetch_data(new_sweep_freqs)
                s21_mag = np.abs(s21_complex)

                popt = self.fit(freqs, s21_mag)
                self.f0_approx = popt[0]
                self.kappa_approx = popt[1]
                print(f"f0 = {popt[0]/1e9:.4f} GHz, kappa = {np.abs(popt[1])/1e6:.4f} MHz\n")

                plots_dict[f"data_{i+1}_adaptive"] = self.get_data_plot(freqs, s21_mag)
                plots_dict[f"fitted_{i+1}_adaptive"] = self.get_fit_plot(freqs, s21_mag, popt)

        return popt[0], popt[1], plots_dict, (freqs, s21_mag)
    