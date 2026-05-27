import os
import glob
import streamlit as st
import data_handler
from architectures.qubit_resonator import QubitResonator
from experiments.resonator_scan import ResonatorScan
from experiments.qubit_scan import QubitScan
from experiments.rabi_scan import RabiScan
from experiments.ramsey_scan import RamseyScan
from experiments.t1_scan import T1Scan


def build_dut():
    return QubitResonator(
        wc=st.session_state['dut_wc'], wq=st.session_state['dut_wq'], g=st.session_state['dut_g'],
        Q=st.session_state['dut_Q'], t1=st.session_state['dut_t1'], t2=st.session_state['dut_t2']
    )

def parse_powers(powers_str):
    return [int(float(p.strip())) if float(p.strip()).is_integer() else float(p.strip()) for p in powers_str.split(",") if p.strip()]

def execute_computations(res_status, res_container, qb_status, qb_container, rabi_status, rabi_container, ramsey_status, ramsey_container, t1_status, t1_container):
    if st.session_state['execute_res_sim']:
        with res_status:
            with st.spinner("Simulating Resonator Scan..."):
                data_paths = data_handler.generate_data_folder()
                
                resonator_scan = ResonatorScan(
                    dut=build_dut(), naive=not st.session_state['res_adaptive'], transmission_coupled=st.session_state['dut_tc'],
                    start_freq=st.session_state['res_start'], stop_freq=st.session_state['res_stop'], coarse_sweep_points=st.session_state['res_coarse'],
                    dense_sweep_points=st.session_state['res_dense'], adaptive_sweep_points=st.session_state['res_adapt'],
                    adaptive_iterations=st.session_state['res_iters'], vna_ifbw=st.session_state['res_ifbw'],
                    vna_averages=st.session_state['res_averages'], vna_powers=parse_powers(st.session_state['res_powers']),
                    s21_dir=data_paths["resonator_scan_s21"], plots_dir=data_paths["resonator_scan_plots"], logs_path=data_paths["resonator_scan_logs"]
                )
                
                opt_freq, opt_power = resonator_scan.run()
                
                st.session_state['opt_freq'] = opt_freq
                st.session_state['opt_power'] = opt_power
                st.session_state['res_plot_dir'] = data_paths["resonator_scan_plots"]
                
                clean_opt_freq = float(opt_freq)
                clean_opt_p = float(opt_power)
                
                st.session_state['pending_updates'] = {
                    'qb_readout_freq': clean_opt_freq, 'qb_readout_power': clean_opt_p,
                    'rabi_readout_freq': clean_opt_freq, 'rabi_readout_power': clean_opt_p,
                    'ramsey_readout_freq': clean_opt_freq, 'ramsey_readout_power': clean_opt_p,
                    't1_readout_freq': clean_opt_freq, 't1_readout_power': clean_opt_p
                }
                
                new_plots = glob.glob(f"{data_paths['resonator_scan_plots']}/*.png")
                if new_plots:
                    new_plots.sort()
                    st.session_state['res_choice'] = os.path.basename(new_plots[0])
                else:
                    st.session_state['res_choice'] = "none"
                    
        st.session_state['running'] = False
        st.session_state['execute_res_sim'] = False
        st.session_state['res_sim_finished'] = True
        st.rerun()

    if st.session_state['execute_qubit_sim']:
        with qb_status:
            with st.spinner("Simulating Qubit Scan..."):
                data_paths = data_handler.generate_data_folder()
                
                qubit_scan = QubitScan(
                    dut=build_dut(), naive=not st.session_state['qb_adaptive'], transmission_coupled=not st.session_state['dut_tc'],
                    readout_frequency=st.session_state['qb_readout_freq'], readout_power=st.session_state['qb_readout_power'],
                    vna_ifbw=st.session_state['qb_ifbw'], 
                    vna_averages=st.session_state['qb_averages'], 
                    start_freq=st.session_state['qb_start'], stop_freq=st.session_state['qb_stop'], 
                    coarse_sweep_points=st.session_state['qb_coarse'], dense_sweep_points=st.session_state['qb_dense'], 
                    adaptive_sweep_points=st.session_state['qb_adapt'], adaptive_iterations=st.session_state['qb_iters'],
                    sg_powers=parse_powers(st.session_state['qb_powers']), s21_dir=data_paths["qubit_scan_s21"],
                    plots_dir=data_paths["qubit_scan_plots"], logs_path=data_paths["qubit_scan_logs"]
                )
                
                qubit_freq, qubit_power = qubit_scan.run()
                
                st.session_state['qubit_freq'] = qubit_freq
                st.session_state['qubit_power'] = qubit_power
                st.session_state['qubit_plot_dir'] = data_paths["qubit_scan_plots"]
                
                clean_qb_freq = float(qubit_freq)
                clean_qb_p = float(qubit_power)
                pwr_str = str(int(clean_qb_p)) if clean_qb_p.is_integer() else str(clean_qb_p)
                
                st.session_state['pending_updates'] = {
                    'rabi_qubit_freq': clean_qb_freq, 'rabi_powers': pwr_str,
                    'ramsey_qubit_freq': clean_qb_freq, 'ramsey_qubit_power': clean_qb_p,
                    't1_qubit_freq': clean_qb_freq, 't1_qubit_power': clean_qb_p
                }
                
                new_plots_q = glob.glob(f"{data_paths['qubit_scan_plots']}/*.png")
                if new_plots_q:
                    new_plots_q.sort()
                    st.session_state['qb_choice'] = os.path.basename(new_plots_q[0])
                else:
                    st.session_state['qb_choice'] = "none"

        st.session_state['running'] = False
        st.session_state['execute_qubit_sim'] = False
        st.session_state['qubit_sim_finished'] = True
        st.rerun()

    if st.session_state['execute_rabi_sim']:
        with rabi_status:
            with st.spinner("Simulating Rabi Scan..."):
                data_paths = data_handler.generate_data_folder()
                
                rabi_scan = RabiScan(
                    dut=build_dut(), naive=not st.session_state['rabi_adaptive'], readout_frequency=st.session_state['rabi_readout_freq'],
                    readout_power=st.session_state['rabi_readout_power'], qubit_frequency=st.session_state['rabi_qubit_freq'],
                    qubit_powers=parse_powers(st.session_state['rabi_powers']), shfqc_ifbw=st.session_state['rabi_ifbw'],
                    shfqc_averages=st.session_state['rabi_averages'], start_time=st.session_state['rabi_start'],
                    stop_time=st.session_state['rabi_stop'], coarse_sweep_points=st.session_state['rabi_coarse'],
                    dense_sweep_points=st.session_state['rabi_dense'], adaptive_points=st.session_state['rabi_adapt'],
                    s21_dir=data_paths["rabi_scan_s21"], plots_dir=data_paths["rabi_scan_plots"], logs_path=data_paths["rabi_scan_logs"]
                )
                
                results = rabi_scan.run()
                
                st.session_state['rabi_results'] = results
                st.session_state['rabi_plot_dir'] = data_paths["rabi_scan_plots"]
                
                if results:
                    first_power = list(results.keys())[0]
                    pi_pulse = float(results[first_power][1])
                    st.session_state['pending_updates'] = {
                        'ramsey_pi_time': pi_pulse,
                        't1_pi_time': pi_pulse
                    }
                
                new_plots_r = glob.glob(f"{data_paths['rabi_scan_plots']}/*.png")
                if new_plots_r:
                    new_plots_r.sort()
                    st.session_state['rabi_choice'] = os.path.basename(new_plots_r[0])
                else:
                    st.session_state['rabi_choice'] = "none"

        st.session_state['running'] = False
        st.session_state['execute_rabi_sim'] = False
        st.session_state['rabi_sim_finished'] = True
        st.rerun()

    if st.session_state['execute_ramsey_sim']:
        with ramsey_status:
            with st.spinner("Simulating Ramsey Scan..."):
                data_paths = data_handler.generate_data_folder()
                
                ramsey_scan = RamseyScan(
                    dut=build_dut(), naive=not st.session_state['ramsey_adaptive'], readout_frequency=st.session_state['ramsey_readout_freq'],
                    readout_power=st.session_state['ramsey_readout_power'], qubit_frequency=st.session_state['ramsey_qubit_freq'],
                    qubit_power=st.session_state['ramsey_qubit_power'], pi_time=st.session_state['ramsey_pi_time'],
                    detuning=st.session_state['ramsey_detuning'], shfqc_ifbw=st.session_state['ramsey_ifbw'],
                    shfqc_averages=st.session_state['ramsey_averages'], start_time=st.session_state['ramsey_start'],
                    stop_time=st.session_state['ramsey_stop'], coarse_sweep_points=st.session_state['ramsey_coarse'],
                    dense_sweep_points=st.session_state['ramsey_dense'], adaptive_points=st.session_state['ramsey_adapt'],
                    s21_dir=data_paths["ramsey_scan_s21"], plots_dir=data_paths["ramsey_scan_plots"], logs_path=data_paths["ramsey_scan_logs"]
                )
                
                decay, freq = ramsey_scan.run()
                
                st.session_state['ramsey_t2_star'] = decay
                st.session_state['ramsey_detuning_freq'] = freq
                st.session_state['ramsey_plot_dir'] = data_paths["ramsey_scan_plots"]
                
                new_plots_ramsey = glob.glob(f"{data_paths['ramsey_scan_plots']}/*.png")
                if new_plots_ramsey:
                    new_plots_ramsey.sort()
                    st.session_state['ramsey_choice'] = os.path.basename(new_plots_ramsey[0])
                else:
                    st.session_state['ramsey_choice'] = "none"

        st.session_state['running'] = False
        st.session_state['execute_ramsey_sim'] = False
        st.session_state['ramsey_sim_finished'] = True
        st.rerun()

    if st.session_state['execute_t1_sim']:
        with t1_status:
            with st.spinner("Simulating T1 Scan..."):
                data_paths = data_handler.generate_data_folder()
                
                t1_scan = T1Scan(
                    dut=build_dut(), readout_frequency=st.session_state['t1_readout_freq'], readout_power=st.session_state['t1_readout_power'],
                    qubit_frequency=st.session_state['t1_qubit_freq'], qubit_power=st.session_state['t1_qubit_power'],
                    pi_time=st.session_state['t1_pi_time'], shfqc_ifbw=st.session_state['t1_ifbw'],
                    shfqc_averages=st.session_state['t1_averages'], start_time=st.session_state['t1_start'],
                    stop_time=st.session_state['t1_stop'], dense_sweep_points=st.session_state['t1_dense'],
                    s21_dir=data_paths["t1_scan_s21"], plots_dir=data_paths["t1_scan_plots"], logs_path=data_paths["t1_scan_logs"]
                )
                
                t1_val = t1_scan.run()
                
                st.session_state['t1_relaxation_time'] = t1_val
                st.session_state['t1_plot_dir'] = data_paths["t1_scan_plots"]
                
                new_plots_t1 = glob.glob(f"{data_paths['t1_scan_plots']}/*.png")
                if new_plots_t1:
                    new_plots_t1.sort()
                    st.session_state['t1_choice'] = os.path.basename(new_plots_t1[0])
                else:
                    st.session_state['t1_choice'] = "none"

        st.session_state['running'] = False
        st.session_state['execute_t1_sim'] = False
        st.session_state['t1_sim_finished'] = True
        st.rerun()
        