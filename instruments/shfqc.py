import numpy as np


class VirtualSHFQC:
    def __init__(self, start_freq=3.0e9, stop_freq=9.0e9, points=401, readout_freq=6.0e9, channel=1, sample_rate=20.0e9):
        self.channel = channel
        self.freqs = np.linspace(start_freq, stop_freq, int(points))
        self.readout_freq = readout_freq
        self.s21_data = np.zeros_like(self.freqs, dtype=np.complex128)
        
        self.power_dbm = -100.0
        self.ifbw = 1000.0
        self.averages = 10
        self.elec_delay = 0.0
        
        self.integration_time = 10e-9 
        
        self.noise_floor_per_hz_dbm = -160.0
        self.system_impedance = 50.0

        self.sample_rate = sample_rate
        self.waveforms = []
        self.frame_freq = 0.0 
        self.tlist = None

    def set_sweep(self, start_freq, stop_freq, points):
        self.freqs = np.linspace(start_freq, stop_freq, int(points))

    def clear_waveforms(self):
        self.waveforms = []
        self.tlist = None

    def _dbm_to_amp(self, power_dbm, freq, conversion_factor):
        p_watts = 10**(power_dbm / 10.0) / 1000.0
        freq_radsec = freq * 2 * np.pi
        return conversion_factor * np.sqrt(p_watts / freq_radsec)

    def add_square(self, start_time, duration, power, freq, conversion_factor, phase_rad=0.0):
        if duration <= 0: return
        
        num_samples = max(2, int(duration * self.sample_rate))
        t = np.linspace(0, duration, num_samples)
        
        delta_w_radsec = (freq - self.frame_freq) * 2 * np.pi
        t_abs = t + start_time
        
        envelope = self._dbm_to_amp(power, freq, conversion_factor)
        argument = (delta_w_radsec * t_abs) + phase_rad
        
        i_sig = envelope * np.cos(argument)
        q_sig = envelope * np.sin(argument)
        
        self.waveforms.append((t_abs, i_sig, q_sig))

        pulse_end_time = start_time + duration + 1e-9
        if self.tlist is None or pulse_end_time > self.tlist[-1]:
            self.tlist = np.linspace(0, pulse_end_time, max(10, int(pulse_end_time * self.sample_rate) + 10))

    def get_waveform(self, tlist):
        i_total = np.zeros_like(tlist)
        q_total = np.zeros_like(tlist)
        
        for (t_pulse, i_pulse, q_pulse) in self.waveforms:
            i_interp = np.interp(tlist, t_pulse, i_pulse, left=0, right=0)
            q_interp = np.interp(tlist, t_pulse, q_pulse, left=0, right=0)
            i_total += i_interp
            q_total += q_interp
            
        return i_total + 1j * q_total

    def read_single_point(self, dut):
        f = self.readout_freq
        p_drive_watts = 10**(self.power_dbm/10.0)/1000.0
        v_drive = np.sqrt(p_drive_watts * self.system_impedance)
        
        p_noise_dbm = self.noise_floor_per_hz_dbm + 10*np.log10(self.ifbw)
        p_noise_watts = 10**(p_noise_dbm/10.0)/1000.0
        v_noise_sigma = np.sqrt(p_noise_watts * self.system_impedance)

        dut.reset_state()
        
        if self.tlist is not None and len(self.waveforms) > 0:
            wave = self.get_waveform(self.tlist)
            result = dut.response(
                tlist=self.tlist,
                qubit_drive_freq=self.frame_freq,
                i_signal=np.real(wave),
                q_signal=np.imag(wave),
                initial_state=dut.current_state
            )
            dut.current_state = result.states[-1]

        readout_tlist = np.linspace(0, self.integration_time, max(10, int(self.integration_time * 2e9)))
        
        ideal_s21 = dut.response(
            tlist=readout_tlist,
            readout_freq=f,
            readout_dbm=self.power_dbm,
            initial_state=dut.current_state
        )

        if self.elec_delay != 0:
            omega = 2 * np.pi * f 
            ideal_s21 *= np.exp(-1j * omega * self.elec_delay)

        acc_s21 = 0j
        for _ in range(self.averages):
            noise_i = np.random.normal(0, v_noise_sigma)
            noise_q = np.random.normal(0, v_noise_sigma)
            complex_noise = noise_i + 1j * noise_q
            
            measured_voltage = (v_drive * ideal_s21) + complex_noise
            acc_s21 += measured_voltage / v_drive

        return acc_s21 / self.averages
    