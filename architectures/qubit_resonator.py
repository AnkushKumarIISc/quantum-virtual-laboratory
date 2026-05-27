import numpy as np
import qutip as qt


class QubitResonator:
    def __init__(self, wc=6.0e9, wq=5.2e9, g=200e6, Q=2_000, N=10, t1=1000e-9, t2=500e-9):
        self.wc = wc * 2 * np.pi
        self.wq = wq * 2 * np.pi
        self.g  = g * 2 * np.pi
        self.kappa = self.wc / Q
        self.N = N
        
        self.delta = self.wq - self.wc
        self.chi = (self.g ** 2) / self.delta
        
        self.a  = qt.tensor(qt.qeye(2), qt.destroy(N))
        self.n  = self.a.dag() * self.a
        
        self.sm = qt.tensor(qt.sigmam(), qt.qeye(N))
        self.sp = qt.tensor(qt.sigmap(), qt.qeye(N))
        self.sx = qt.tensor(qt.sigmax(), qt.qeye(N))
        self.sy = qt.tensor(qt.sigmay(), qt.qeye(N))
        self.sz = qt.tensor(qt.sigmaz(), qt.qeye(N))

        self.current_state = qt.tensor(qt.basis(2, 1), qt.basis(self.N, 0))
        
        self.cw_drive_freq = None
        self.cw_drive_dbm = None
        
        self.H_full = lambda d_c, d_q: (d_c * self.n) + (0.5 * d_q * self.sz) + (self.g * (self.a.dag() * self.sm + self.a * self.sp))
        self.H_disp = lambda d_c, d_q: (d_c * self.n) + (0.5 * d_q * self.sz) + (self.chi * self.n * self.sz)

        self.c_ops = []
        self.c_ops.append(np.sqrt(self.kappa) * self.a)
        
        if t1 is not None:
            self.gamma_1 = 1.0 / t1
            self.c_ops.append(np.sqrt(self.gamma_1) * self.sm)
        else:
            self.gamma_1 = 0
            
        if t2 is not None:
            gamma_total = 1.0 / t2
            gamma_pure = gamma_total - (self.gamma_1 / 2.0)
            gamma_pure = max(0.0, gamma_pure) 
            if gamma_pure > 0:
                self.c_ops.append(np.sqrt(gamma_pure / 2.0) * self.sz)

        p_ref_dbm = -100.0
        n_ref_photons = 0.1
        epsilon_ref = self.kappa * np.sqrt(n_ref_photons) / 2.0
        p_ref_watts = 10**(p_ref_dbm/10.0) / 1000.0
        self.conversion_factor = epsilon_ref / np.sqrt(p_ref_watts / self.wc)

    def _dbm_to_amp(self, power_dbm, freq_rad):
        p_watts = 10**(power_dbm / 10.0) / 1000.0
        return self.conversion_factor * np.sqrt(p_watts / freq_rad)

    def reset_state(self):
        self.current_state = qt.tensor(qt.basis(2, 1), qt.basis(self.N, 0))

    def apply_cw_drive(self, freq, power_dbm):
        self.cw_drive_freq = freq
        self.cw_drive_dbm = power_dbm

    def remove_cw_drive(self):
        self.cw_drive_freq = None
        self.cw_drive_dbm = None

    def response(self, readout_freq=None, readout_dbm=None, 
                       qubit_drive_freq=None, qubit_drive_dbm=None, 
                       i_signal=None, q_signal=None,
                       initial_state=None, tlist=None):
        q_freq = qubit_drive_freq if qubit_drive_freq is not None else self.cw_drive_freq
        q_dbm = qubit_drive_dbm if qubit_drive_dbm is not None else self.cw_drive_dbm

        w_r = readout_freq * 2 * np.pi if readout_freq else 0
        w_q = q_freq * 2 * np.pi if q_freq else 0
        
        amp_r = 0
        if readout_dbm is not None:
            amp_r = self._dbm_to_amp(readout_dbm, w_r)
            
        amp_q = 0
        if q_dbm is not None:
            amp_q = self._dbm_to_amp(q_dbm, w_q)

        if tlist is None: 
            if q_freq is not None:
                d_c = self.wc - w_r
                d_q = self.wq - w_q
            else:
                d_c = self.wc - w_r
                d_q = self.wq - w_r
                
        else:
            if q_freq is not None:
                d_c = self.wc - w_q
                d_q = self.wq - w_q
            else:
                d_c = self.wc - w_r
                d_q = self.wq - w_r
        
        H = self.H_disp(d_c=d_c, d_q=d_q)
        
        if amp_r != 0:
            H += amp_r * (self.a + self.a.dag())
            
        H_solver = H
        
        if tlist is not None:
            H_solver = [H]
            
            if amp_q != 0:
                 H_solver.append([self.sx, lambda t, args: amp_q])
                 
            if i_signal is not None: H_solver.append([self.sx, i_signal])
            if q_signal is not None: H_solver.append([self.sy, q_signal])
            
            if len(H_solver) == 1: H_solver = H
            
        else:
            if amp_q != 0: H += amp_q * self.sx
            H_solver = H
        
        if tlist is None:
            rho_ss = qt.steadystate(H_solver, self.c_ops)
            a_avg = qt.expect(self.a, rho_ss)
            
            s21 = 1.0 - 1j * (self.kappa * a_avg / (2.0 * amp_r)) if amp_r != 0 else 0
            return s21

        else:
            if initial_state is None:
                initial_state = qt.tensor(qt.basis(2, 1), qt.basis(self.N, 0))

            if readout_freq is not None:
                e_ops = [self.a]
            else:
                e_ops = [self.sz]

            result = qt.mesolve(H_solver, initial_state, tlist, 
                                c_ops=self.c_ops, e_ops=e_ops, 
                                options={
                                    'store_states': True,
                                    'nsteps': 1_000_000,
                                    'atol': 1e-12,
                                    'rtol': 1e-12,
                                    'method': 'bdf'
                                })
            
            if readout_freq is not None:
                start_idx = int(len(tlist) * 0.5)
                
                a_avg_time = np.mean(result.expect[0][start_idx:])
                if amp_r != 0:
                    s21_time = 1.0 - 1j * (self.kappa * a_avg_time / (2.0 * amp_r))
                else:
                    s21_time = 0
                
                return s21_time
            else:
                return result
            