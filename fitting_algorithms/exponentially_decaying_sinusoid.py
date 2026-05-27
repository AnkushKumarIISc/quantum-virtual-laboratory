### ADAPITIVE ALGORITHM BY PRATEEK AGRAWAL ###

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.fft as fft


class ExponentiallyDecayingSinusoid:
    def __init__(self, naive, coarse_sweep_points, adaptive_points, stop_time, fetch_data):
        self.naive = naive
        self.coarse_sweep_points = coarse_sweep_points
        self.adaptive_points = adaptive_points
        self.stop_time = stop_time
        self.fetch_data = fetch_data

    @staticmethod
    def model(t, freq, decay, amplitude, phase, base_amp, base_decay):
        return base_amp * np.exp(-t / base_decay) + amplitude * np.exp(-t / decay) * np.cos(2 * np.pi * freq * t + phase)

    @staticmethod
    def calc_jacobian(t, params):
        f, T2, A, phi, C, T1 = params
        T2_safe = max(T2, 1e-12)
        T1_safe = max(T1, 1e-12)
        
        exp_T2 = np.exp(-t / T2_safe)
        exp_T1 = np.exp(-t / T1_safe)
        cos_term = np.cos(2 * np.pi * f * t + phi)
        sin_term = np.sin(2 * np.pi * f * t + phi)

        J = np.zeros((len(t), 6))
        J[:, 0] = -A * exp_T2 * sin_term * (2 * np.pi * t)
        J[:, 1] = A * exp_T2 * cos_term * (t / (T2_safe**2))
        J[:, 2] = exp_T2 * cos_term
        J[:, 3] = -A * exp_T2 * sin_term
        J[:, 4] = exp_T1
        J[:, 5] = C * exp_T1 * (t / (T1_safe**2))
        return J

    def _process_raw_data(self, s21_complex, ref_s21, is_batch=False):
        mags = np.abs(np.array(s21_complex) - np.array(ref_s21))
        if is_batch or self.naive:
            self._norm_min = np.min(mags)
            self._norm_max = np.max(mags)
        if hasattr(self, '_norm_max') and self._norm_max > self._norm_min:
            mags = (mags - self._norm_min) / (self._norm_max - self._norm_min)
        return mags

    def fit(self, times_ns, mags, p0_override=None):
        if p0_override is not None:
            p0 = p0_override
        else:
            sort_idx = np.argsort(times_ns)
            t_sorted = np.array(times_ns)[sort_idx]
            m_sorted = np.array(mags)[sort_idx]
            
            if len(t_sorted) > 2:
                diff_m = np.diff(m_sorted)
                diff_t = np.diff(t_sorted)
                dt = np.mean(diff_t) if len(diff_t) > 0 else 1.0
                n = len(diff_m)
                
                n_pad = n * 10 
                yf = fft.fft(diff_m - np.mean(diff_m), n=n_pad)
                xf = fft.fftfreq(n_pad, d=dt)
                idx = np.argmax(np.abs(yf[1:n_pad//2])) + 1 if n_pad > 2 else 0
                freq_guess = xf[idx] if xf[idx] > 0 else 1 / (t_sorted[-1] - t_sorted[0])
            else:
                freq_guess = 1 / (t_sorted[-1] - t_sorted[0]) if len(t_sorted)>1 else 1.0

            base_amp_guess = 0.5
            base_decay_guess = max(times_ns[-1], 1.0) 
            amplitude_guess = 0.5
            decay_guess = max(times_ns[-1] / 2.0, 1.0) 
            phase_guess = np.pi if m_sorted[0] < 0.5 else 0.0
                
            p0 = [freq_guess, decay_guess, amplitude_guess, phase_guess, base_amp_guess, base_decay_guess]

        bounds = ([0, 0, 0, -np.inf, 0, 0], [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf])
        try:
            popt, _ = curve_fit(self.model, times_ns, mags, p0=p0, bounds=bounds, maxfev=10000)
            return popt
        except Exception:
            return p0 

    def get_data_plot(self, times, mags, adaptive_history=None):
        times_ns = np.array(times) * 1e9
        
        plot_mags = (mags - np.min(mags)) / (np.max(mags) - np.min(mags))
        
        plt.figure(figsize=(10, 6))
        plt.title("Data")
        
        if adaptive_history is not None:
            scout_mask = np.array(adaptive_history) == "Scout"
            opt_mask = np.array(adaptive_history) == "Optimal"
            plt.plot(times_ns[scout_mask], plot_mags[scout_mask], 'o-', color='gray', markersize=4, label="Coarse Points")
            plt.plot(times_ns[opt_mask], plot_mags[opt_mask], 'o', color='crimson', markersize=6, label="Adaptive Points")
        else:
            plt.plot(times_ns, plot_mags, 'o-', color='gray', markersize=4, label="Data")
            
        plt.xlabel("Time (ns)")
        plt.ylabel("Normalized Magnitude")
        plt.legend()
        plt.grid(True, alpha=0.3)
        return plt.gcf()

    def get_fit_plot(self, times, mags, popt_si, adaptive_history=None):
        times_fit = np.linspace(min(times), max(times), 1000)
        times_ns = np.array(times) * 1e9
        times_fit_ns = times_fit * 1e9
        
        raw_fit = self.model(times_fit, *popt_si)
        mags_fit = (raw_fit - np.min(mags)) / (np.max(mags) - np.min(mags))
        plot_mags = (mags - np.min(mags)) / (np.max(mags) - np.min(mags))

        plt.figure(figsize=(10, 6))
        plt.title("Fit")
        
        if adaptive_history is not None:
            scout_mask = np.array(adaptive_history) == "Scout"
            opt_mask = np.array(adaptive_history) == "Optimal"
            plt.plot(times_ns[scout_mask], plot_mags[scout_mask], 'o', color='gray', markersize=4, label="Coarse Points")
            plt.plot(times_ns[opt_mask], plot_mags[opt_mask], 'o', color='crimson', markersize=6, label="Adaptive Points")
        else:
            plt.plot(times_ns, plot_mags, 'o', color='gray', markersize=4, label="Data")
            
        plt.plot(times_fit_ns, mags_fit, "-", color="royalblue", lw=2, label="Fit Line")
        plt.xlabel("Time (ns)")
        plt.ylabel("Normalized Magnitude")
        plt.legend()
        plt.grid(True, alpha=0.3)
        return plt.gcf()

    def fitting_routine(self):
        if self.naive:
            return self._run_naive_routine()
        else:
            return self._run_adaptive_routine()

    def _run_naive_routine(self):
        times, s21_complex, ref_s21 = self.fetch_data()
        mags = self._process_raw_data(s21_complex, ref_s21, is_batch=True)
        times_ns = times * 1e9
        
        popt = self.fit(times_ns, mags)
        
        freq_ghz, decay_ns, amp, phase, base_amp, base_decay_ns = popt
        
        popt_si = [freq_ghz * 1e9, decay_ns * 1e-9, amp, phase, base_amp, base_decay_ns * 1e-9]
        freq, decay = popt_si[0], popt_si[1]
        
        plots_dict = {
            "data_dense": self.get_data_plot(times, mags),
            "fitted_dense": self.get_fit_plot(times, mags, popt_si)
        }
        
        return freq, decay, plots_dict, (times_ns, mags)

    def _run_adaptive_routine(self):
        history = {"t": [], "y": [], "phase": []}
        
        t_scout = np.linspace(0, self.stop_time, self.coarse_sweep_points)
        times_raw, s21_raw, ref_raw = self.fetch_data(t_scout)
        y_scout = self._process_raw_data(s21_raw, ref_raw, is_batch=True)
        
        history["t"].extend(times_raw)
        history["y"].extend(y_scout)
        history["phase"].extend(["Scout"] * len(times_raw))
        
        times_ns = np.array(history["t"]) * 1e9
        popt = self.fit(times_ns, history["y"])
        
        current_params = [popt[0]*1e9, popt[1]*1e-9, popt[2], popt[3], popt[4], popt[5]*1e-9]

        def objective_fim(t_new, t_past, params):
            J_past = self.calc_jacobian(t_past, params)
            FIM_past = J_past.T @ J_past 
            J_new = self.calc_jacobian(t_new, params)
            
            # Slightly increased regularization for absolute matrix safety
            FIM_total = FIM_past + (J_new.T @ J_new) + (np.eye(6) * 1e-7) 
            sign, logdet = np.linalg.slogdet(FIM_total)
            obj = -logdet if sign > 0 else 1e6
            
            if len(t_past) > 0:
                dist = np.abs(t_past - t_new[0])
                obj += 2.0 * np.sum(np.exp(- (dist**2) / (2 * (1e-9)**2)))
            return obj

        t_cands = np.linspace(0, self.stop_time, 500)
        
        for iteration in range(self.adaptive_points):
            t_past = np.array(history["t"])
            utils = [objective_fim(np.array([t]), t_past, current_params) for t in t_cands]
            t_next = t_cands[np.argmin(utils)]
            
            t_new, s21_new, ref_new = self.fetch_data([t_next])
            y_new = self._process_raw_data(s21_new, ref_new, is_batch=False)[0]
            
            history["t"].append(t_new[0])
            history["y"].append(y_new)
            history["phase"].append("Optimal")
            
            p0_guess = [current_params[0]/1e9, current_params[1]*1e9, current_params[2], current_params[3], current_params[4], current_params[5]*1e9]
            times_ns = np.array(history["t"]) * 1e9
            popt = self.fit(times_ns, history["y"], p0_override=p0_guess)
            current_params = [popt[0]*1e9, popt[1]*1e-9, popt[2], popt[3], popt[4], popt[5]*1e-9]

        t_arr = np.array(history["t"])
        y_arr = np.array(history["y"])
        
        plots_dict = {
            "data_adaptive": self.get_data_plot(t_arr, y_arr, adaptive_history=history["phase"]),
            "fitted_adaptive": self.get_fit_plot(t_arr, y_arr, current_params, adaptive_history=history["phase"])
        }
        
        return current_params[0], current_params[1], plots_dict, (t_arr, y_arr)
    