import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


class ExponentialDecay:
    def __init__(self, fetch_data):
        self.fetch_data = fetch_data

    @staticmethod
    def model(t, decay, amplitude, baseline):
        return baseline + amplitude * np.exp(-t / decay)

    def get_data_plot(self, times_ns, mags):
        plt.figure(figsize=(10, 6))
        plt.title("Data")
        plt.plot(times_ns, mags, 'o-', color='gray', markersize=4, label="Data")
        plt.xlabel("Time (ns)")
        plt.ylabel("Normalized Magnitude")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()

    def get_fit_plot(self, times_ns, mags, popt):
        times_fit_ns = np.linspace(min(times_ns), max(times_ns), 1000)
        mags_fit = self.model(times_fit_ns, *popt)

        plt.figure(figsize=(10, 6))
        plt.title("Fit")
        plt.plot(times_ns, mags, 'o', color='gray', markersize=4, label="Data")
        plt.plot(times_fit_ns, mags_fit, "-", color="royalblue", lw=2, label="Fit Line")
        plt.xlabel("Time (ns)")
        plt.ylabel("Normalized Magnitude")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()

    def fitting_routine(self):
        times, s21_complex, ref_s21 = self.fetch_data()
        
        mags = np.abs(np.array(s21_complex) - np.array(ref_s21))
        if np.max(mags) > np.min(mags):
            mags = (mags - np.min(mags)) / (np.max(mags) - np.min(mags))
        
        times_ns = times * 1e9
        
        baseline_guess = np.mean(mags[-10:]) if len(mags) > 10 else np.mean(mags)
        amplitude_guess = (np.max(mags) - np.min(mags))
        decay_guess = max(times_ns[-1] / 3.0, 1.0)
        
        p0 = [decay_guess, amplitude_guess, baseline_guess]
        bounds = ([0, 0, -np.inf], [np.inf, np.inf, np.inf])

        try:
            popt, _ = curve_fit(self.model, times_ns, mags, p0=p0, bounds=bounds, maxfev=10000)
        except Exception:
            popt = p0

        decay_s = popt[0] * 1e-9
        
        plots_dict = {
            "data_dense": self.get_data_plot(times_ns, mags),
            "fitted_dense": self.get_fit_plot(times_ns, mags, popt)
        }
        
        return 0.0, decay_s, plots_dict, (times_ns, mags)
    