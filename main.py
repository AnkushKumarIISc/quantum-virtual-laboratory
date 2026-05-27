import config
import data_handler
from architectures.qubit_resonator import QubitResonator
from experiments.resonator_scan import ResonatorScan
from experiments.qubit_scan import QubitScan
from experiments.rabi_scan import RabiScan
from experiments.ramsey_scan import RamseyScan
from experiments.t1_scan import T1Scan


dut = QubitResonator(
    wc=config.DUT_WC, 
    wq=config.DUT_WQ, 
    g=config.DUT_G, 
    t1=config.DUT_T1, 
    t2=config.DUT_T2_STAR
)

data_paths = data_handler.generate_data_folder()


# ==========================================
# --- STEP 1: RESONATOR SCAN ---
# ==========================================
resonator_scan = ResonatorScan(
    dut=dut,
    naive=not config.ADAPTIVE,
    transmission_coupled=config.TRANSMISSION_COUPLED,
    start_freq=config.VNA_START_FREQ, 
    stop_freq=config.VNA_STOP_FREQ, 
    coarse_sweep_points=config.VNA_COARSE_SWEEP_POINTS, 
    dense_sweep_points=config.VNA_DENSE_SWEEP_POINTS, 
    adaptive_sweep_points=config.VNA_ADAPTIVE_SWEEP_POINTS, 
    adaptive_iterations=config.VNA_ADAPTIVE_ITERATIONS, 
    vna_ifbw=config.VNA_IFBW, 
    vna_averages=config.VNA_AVERAGES,
    vna_powers=config.VNA_POWERS,
    s21_dir=data_paths["resonator_scan_s21"],
    plots_dir=data_paths["resonator_scan_plots"],
    logs_path=data_paths["resonator_scan_logs"]
)
READOUT_FREQUENCY, READOUT_POWER = resonator_scan.run()


# ==========================================
# --- STEP 2: QUBIT SPECTROSCOPY ---
# ==========================================
qubit_scan = QubitScan(
    dut=dut,
    naive=not config.ADAPTIVE,
    transmission_coupled=not config.TRANSMISSION_COUPLED,
    readout_frequency=READOUT_FREQUENCY,
    readout_power=READOUT_POWER,
    vna_ifbw=config.VNA_IFBW, 
    vna_averages=config.VNA_AVERAGES, 
    start_freq=config.SG_START_FREQ, 
    stop_freq=config.SG_STOP_FREQ, 
    coarse_sweep_points=config.SG_COARSE_SWEEP_POINTS, 
    dense_sweep_points=config.SG_DENSE_SWEEP_POINTS, 
    adaptive_sweep_points=config.SG_ADAPTIVE_SWEEP_POINTS, 
    adaptive_iterations=config.SG_ADAPTIVE_ITERATIONS,
    sg_powers=config.SG_POWERS,
    s21_dir=data_paths["qubit_scan_s21"],
    plots_dir=data_paths["qubit_scan_plots"],
    logs_path=data_paths["qubit_scan_logs"]
)
DRIVE_FREQUENCY, DRIVE_POWER = qubit_scan.run()


# ==========================================
# --- STEP 3: RABI OSCILLATIONS ---
# ==========================================
rabi_scan = RabiScan(
    dut=dut,
    naive=not config.ADAPTIVE,
    readout_frequency=READOUT_FREQUENCY,
    readout_power=READOUT_POWER,
    qubit_frequency=DRIVE_FREQUENCY,
    qubit_powers=config.RABI_POWERS,
    shfqc_ifbw=config.SHFQC_IFBW,
    shfqc_averages=config.SHFQC_AVERAGES,
    start_time=config.RABI_START_TIME,
    stop_time=config.RABI_STOP_TIME,
    coarse_sweep_points=config.RABI_COARSE_SWEEP_POINTS,
    dense_sweep_points=config.RABI_DENSE_SWEEP_POINTS,
    adaptive_points=config.RABI_ADAPTIVE_POINTS,
    s21_dir=data_paths["rabi_scan_s21"],
    plots_dir=data_paths["rabi_scan_plots"],
    logs_path=data_paths["rabi_scan_logs"]
)
RABI_RESULTS = rabi_scan.run()
QUBIT_DRIVE_POWER = config.RABI_POWERS[0]
QUBIT_PI_TIME = RABI_RESULTS[QUBIT_DRIVE_POWER][1] 


# ==========================================
# --- STEP 4: RAMSEY FRINGES (T2*) ---
# ==========================================
ramsey_scan = RamseyScan(
    dut=dut,
    naive=not config.ADAPTIVE,
    readout_frequency=READOUT_FREQUENCY,
    readout_power=READOUT_POWER,
    qubit_frequency=DRIVE_FREQUENCY,
    qubit_power=QUBIT_DRIVE_POWER, 
    pi_time=QUBIT_PI_TIME,   
    detuning=config.RAMSEY_DETUNING,
    shfqc_ifbw=config.SHFQC_IFBW,
    shfqc_averages=config.SHFQC_AVERAGES,
    start_time=config.RAMSEY_START_TIME,
    stop_time=config.RAMSEY_STOP_TIME,
    coarse_sweep_points=config.RAMSEY_COARSE_SWEEP_POINTS,
    dense_sweep_points=config.RAMSEY_DENSE_SWEEP_POINTS,
    adaptive_points=config.RAMSEY_ADAPTIVE_POINTS,
    s21_dir=data_paths["ramsey_scan_s21"],
    plots_dir=data_paths["ramsey_scan_plots"],
    logs_path=data_paths["ramsey_scan_logs"]
)
T2_STAR, _ = ramsey_scan.run()


# ==========================================
# --- STEP 5: T1 RELAXATION ---
# ==========================================
t1_scan = T1Scan(
    dut=dut,
    readout_frequency=READOUT_FREQUENCY,
    readout_power=READOUT_POWER,
    qubit_frequency=DRIVE_FREQUENCY,
    qubit_power=QUBIT_DRIVE_POWER, 
    pi_time=QUBIT_PI_TIME,   
    shfqc_ifbw=config.SHFQC_IFBW,
    shfqc_averages=config.SHFQC_AVERAGES,
    start_time=config.T1_START_TIME,
    stop_time=config.T1_STOP_TIME,
    dense_sweep_points=config.T1_DENSE_SWEEP_POINTS,
    s21_dir=data_paths["t1_scan_s21"],
    plots_dir=data_paths["t1_scan_plots"],
    logs_path=data_paths["t1_scan_logs"]
)
T1 = t1_scan.run()

print(f"\n--- CALIBRATION COMPLETE ---")
print(f"T1: {T1*1e9:.2f} ns | T2*: {T2_STAR*1e9:.2f} ns")
