import numpy as np
import matplotlib.pyplot as plt

try: from tqdm import tqdm
except ImportError: tqdm = lambda x, **k: x


class VirtualVNA:
    def __init__(self, start_freq=5.5e9, stop_freq=6.5e9, points=401, channel=1):
        self.channel = channel
        self.freqs = np.linspace(start_freq, stop_freq, int(points))
        self.readout_freq = None
        self.s21_data = np.zeros_like(self.freqs, dtype=np.complex128)
        
        self.power_dbm = -100.0
        self.ifbw = 1000.0
        self.averages = 10
        
        self.noise_floor_per_hz_dbm = -160.0
        self.system_impedance = 50.0

    def set_sweep(self, start_freq, stop_freq, points):
        self.freqs = np.linspace(start_freq, stop_freq, int(points))

    def scan(self, dut):
        single_point = len(self.freqs) == 1
        if not single_point:
            print(f"--- [VNA Scan: Freq Sweep] ---")
            print(f"  Range: {self.freqs[0]/1e9:.4f} - {self.freqs[-1]/1e9:.4f} GHz")
            print(f"  Power: {self.power_dbm} dBm | IFBW: {self.ifbw} Hz | Avg: {self.averages}")

        p_drive_watts = 10**(self.power_dbm/10.0)/1000.0
        v_drive = np.sqrt(p_drive_watts * self.system_impedance)
        
        p_noise_dbm = self.noise_floor_per_hz_dbm + 10*np.log10(self.ifbw)
        p_noise_watts = 10**(p_noise_dbm/10.0)/1000.0
        v_noise_sigma = np.sqrt(p_noise_watts * self.system_impedance)
        
        ideal_s21 = []
        
        iterator = tqdm(self.freqs, desc="Acquiring", unit="pts", disable=single_point)
        
        for f in iterator:
            result = dut.response(
                readout_freq=f, 
                readout_dbm=self.power_dbm
            )
            ideal_s21.append(result)
        ideal_s21 = np.array(ideal_s21)

        acc_s21 = np.zeros_like(ideal_s21, dtype=np.complex128)
        for _ in range(self.averages):
            noise_i = np.random.normal(0, v_noise_sigma, len(self.freqs))
            noise_q = np.random.normal(0, v_noise_sigma, len(self.freqs))
            complex_noise = noise_i + 1j * noise_q
            
            measured_voltage = (v_drive * ideal_s21) + complex_noise
            
            acc_s21 += measured_voltage / v_drive

        self.s21_data = acc_s21 / self.averages
        
        if not single_point: print("--- [Hardware Scan Complete] ---\n")
        return self.freqs, self.s21_data

    def read_single_point(self, dut):
        f = self.readout_freq

        p_drive_watts = 10**(self.power_dbm/10.0)/1000.0
        v_drive = np.sqrt(p_drive_watts * self.system_impedance)
        
        p_noise_dbm = self.noise_floor_per_hz_dbm + 10*np.log10(self.ifbw)
        p_noise_watts = 10**(p_noise_dbm/10.0)/1000.0
        v_noise_sigma = np.sqrt(p_noise_watts * self.system_impedance)

        ideal_s21 = dut.response(
            readout_freq=f, 
            readout_dbm=self.power_dbm
        )

        acc_s21 = 0j
        for _ in range(self.averages):
            noise_i = np.random.normal(0, v_noise_sigma)
            noise_q = np.random.normal(0, v_noise_sigma)
            complex_noise = noise_i + 1j * noise_q
            
            measured_voltage = (v_drive * ideal_s21) + complex_noise
            acc_s21 += measured_voltage / v_drive

        return acc_s21 / self.averages
    
    def plot(self):
        s21 = self.s21_data
        s21_mag = np.abs(s21)
        s21_phase = np.angle(s21)

        plt.figure(figsize=(15, 5))
        plt.suptitle(f"Hardware VNA Scan: P={self.power_dbm} dBm | Avg={self.averages}", fontsize=14)

        plt.subplot(1, 3, 1)
        plt.plot(self.freqs, s21_mag, "b")
        plt.title("Magnitude")
        plt.ylabel("|S21|"); plt.xlabel("Frequency (Hz)")
        plt.grid(True, alpha=0.3)

        plt.subplot(1, 3, 2)
        plt.plot(self.freqs, s21_phase, "r")
        plt.title("Phase")
        plt.ylabel("Radians"); plt.xlabel("Frequency (Hz)")
        plt.grid(True, alpha=0.3)

        plt.subplot(1, 3, 3)
        plt.plot(s21.real, s21.imag, "g-", alpha=0.5, marker="o", markersize=3)
        
        res_idx = np.argmin(np.abs(s21)) 
        plt.plot(s21.real[res_idx], s21.imag[res_idx], "ro", label="Res")
        plt.plot(s21.real[0], s21.imag[0], "kx", label="Start")
        
        plt.title("IQ Circle")
        plt.xlabel("I"); plt.ylabel("Q")
        plt.axis("equal")
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        return plt.gcf()
    