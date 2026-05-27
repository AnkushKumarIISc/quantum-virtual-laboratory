import os
import glob
import streamlit as st


def sync_res(): st.session_state['res_choice'] = st.session_state['res_widget']
def sync_qb(): st.session_state['qb_choice'] = st.session_state['qb_widget']
def sync_rabi(): st.session_state['rabi_choice'] = st.session_state['rabi_widget']
def sync_ramsey(): st.session_state['ramsey_choice'] = st.session_state['ramsey_widget']
def sync_t1(): st.session_state['t1_choice'] = st.session_state['t1_widget']

def sync_res_span(): 
    st.session_state['res_start'] = st.session_state['dut_wc'] - 0.5e9
    st.session_state['res_stop'] = st.session_state['dut_wc'] + 0.5e9

def sync_qb_span(): 
    st.session_state['qb_start'] = st.session_state['dut_wq'] - 0.5e9
    st.session_state['qb_stop'] = st.session_state['dut_wq'] + 0.5e9


def render_dut():
    is_running = st.session_state['running']
    st.header("Initialize DUT", anchor=False)

    c1, c2, c3 = st.columns(3)
    c1.number_input("Resonator Frequency (Hz)", format="%.4e", step=None, disabled=is_running, key="dut_wc", on_change=sync_res_span)
    c2.number_input("Qubit Frequency (Hz)", format="%.4e", step=None, disabled=is_running, key="dut_wq", on_change=sync_qb_span)
    c3.number_input("Coupling (Hz)", format="%.4e", step=None, disabled=is_running, key="dut_g")

    c4, c5, c6 = st.columns(3)
    c4.number_input("Q", format="%.4e", step=None, disabled=is_running, key="dut_Q")
    c5.number_input("T1 (s)", format="%.4e", step=None, disabled=is_running, key="dut_t1")
    c6.number_input("T2* (s)", format="%.4e", step=None, disabled=is_running, key="dut_t2")

    st.columns(1)[0].checkbox("Transmission Coupled", disabled=is_running, key="dut_tc")

def render_resonator_ui():
    is_running = st.session_state['running']
    st.header("Resonator Scan", anchor=False)

    controls_col, plot_col = st.columns([1, 2])
    with controls_col:
        st.subheader("Settings", anchor=False)
        with st.expander("Scan Parameters", expanded=True):
            st.text_input("VNA Powers (dBm, Comma-Separated)", disabled=is_running, key="res_powers")
            
            c1, c2 = st.columns(2)
            c1.number_input("Start Frequency (Hz)", format="%.4e", step=None, disabled=is_running, key="res_start")
            c2.number_input("Stop Frequency (Hz)", format="%.4e", step=None, disabled=is_running, key="res_stop")
            c1.number_input("IFBW (Hz)", step=None, disabled=is_running, key="res_ifbw")
            c2.number_input("Averages", step=None, disabled=is_running, key="res_averages")
            
            st.divider()
            adaptive_scan_res = st.checkbox("Adaptive Scan", disabled=is_running, key="res_adaptive")
            naive_scan_res = not adaptive_scan_res
            
            c1, c2 = st.columns(2)
            c1.number_input("Dense Points", step=None, disabled=is_running or (not naive_scan_res), key="res_dense")
            c2.number_input("Coarse Points", step=None, disabled=is_running or naive_scan_res, key="res_coarse")
            c1.number_input("Adaptive Points", step=None, disabled=is_running or naive_scan_res, key="res_adapt")
            c2.number_input("Adaptive Iterations", step=None, disabled=is_running or naive_scan_res, key="res_iters")

        if st.button("Run Resonator Scan", width='stretch', disabled=is_running, key="res_run_btn"):
            st.session_state['running'] = True
            st.session_state['execute_res_sim'] = True
            st.rerun()

    with plot_col:
        st.subheader("Results", anchor=False)
        res_status = st.empty()
        res_container = st.container()
        
        if st.session_state.get('res_sim_finished', False) and not st.session_state.get('execute_res_sim', False):
            res_status.success("Resonator Scan Complete!")
        elif not st.session_state.get('execute_res_sim', False):
            res_status.info("Configure Parameters And Click 'Run Resonator Scan'.")

        with res_container:
            if st.session_state.get('res_sim_finished', False):
                st.info(f"Frequency: {st.session_state['opt_freq']/1e9:.5f} GHz  |  Power: {st.session_state['opt_power']} dBm")
                
                saved_plots = glob.glob(f"{st.session_state['res_plot_dir']}/*.png")
                if saved_plots:
                    saved_plots.sort() 
                    plot_names = [os.path.basename(p) for p in saved_plots] + ["none"]
                    
                    if st.session_state['res_choice'] not in plot_names:
                        st.session_state['res_choice'] = "none"
                    
                    current_idx = plot_names.index(st.session_state['res_choice'])
                    st.selectbox("Select Plot To View:", plot_names, index=current_idx, disabled=is_running, key="res_widget", on_change=sync_res)
                    
                    if st.session_state['res_choice'] != "none":
                        selected_path = saved_plots[plot_names.index(st.session_state['res_choice'])]
                        st.image(selected_path, width='stretch')
                else:
                    st.warning("No Plots Were Found.")
                    
    return res_status, res_container

def render_qubit_ui():
    is_running = st.session_state['running']
    st.header("Qubit Scan", anchor=False)

    controls_col, plot_col = st.columns([1, 2])
    with controls_col:
        st.subheader("Settings", anchor=False)
        with st.expander("Scan Parameters", expanded=True):
            
            c1, c2 = st.columns(2)
            c1.number_input("Readout Frequency (Hz)", format="%.4e", step=None, disabled=is_running, key="qb_readout_freq")
            c2.number_input("Readout Power (dBm)", step=None, disabled=is_running, key="qb_readout_power")
            c1.number_input("IFBW (Hz)", step=None, disabled=is_running, key="qb_ifbw")
            c2.number_input("Averages", step=None, disabled=is_running, key="qb_averages")
            
            st.divider()
            
            st.text_input("SG Powers (dBm, Comma-Separated)", disabled=is_running, key="qb_powers")
            
            c3, c4 = st.columns(2)
            c3.number_input("Start Frequency (Hz)", format="%.4e", step=None, disabled=is_running, key="qb_start")
            c4.number_input("Stop Frequency (Hz)", format="%.4e", step=None, disabled=is_running, key="qb_stop")
            
            st.divider()
            
            adaptive_scan_qb = st.checkbox("Adaptive Scan", disabled=is_running, key="qb_adaptive")
            naive_scan_qb = not adaptive_scan_qb
            
            c5, c6 = st.columns(2)
            c5.number_input("Dense Points", step=None, disabled=is_running or (not naive_scan_qb), key="qb_dense")
            c6.number_input("Coarse Points", step=None, disabled=is_running or naive_scan_qb, key="qb_coarse")
            
            c7, c8 = st.columns(2)
            c7.number_input("Adaptive Points", step=None, disabled=is_running or naive_scan_qb, key="qb_adapt")
            c8.number_input("Adaptive Iterations", step=None, disabled=is_running or naive_scan_qb, key="qb_iters")

        if st.button("Run Qubit Scan", width='stretch', disabled=is_running, key="qb_run_btn"):
            st.session_state['running'] = True
            st.session_state['execute_qubit_sim'] = True
            st.rerun()

    with plot_col:
        st.subheader("Results", anchor=False)
        qb_status = st.empty()
        qb_container = st.container()
        
        if st.session_state.get('qubit_sim_finished', False) and not st.session_state.get('execute_qubit_sim', False):
            qb_status.success("Qubit Scan Complete!")
        elif not st.session_state.get('execute_qubit_sim', False):
            qb_status.info("Configure Parameters And Click 'Run Qubit Scan'.")

        with qb_container:
            if st.session_state.get('qubit_sim_finished', False):
                st.info(f"Frequency: {st.session_state['qubit_freq']/1e9:.5f} GHz  |  Power: {st.session_state['qubit_power']} dBm")
                
                saved_plots_q = glob.glob(f"{st.session_state['qubit_plot_dir']}/*.png")
                if saved_plots_q:
                    saved_plots_q.sort() 
                    plot_names_q = [os.path.basename(p) for p in saved_plots_q] + ["none"]
                    
                    if st.session_state['qb_choice'] not in plot_names_q:
                        st.session_state['qb_choice'] = "none"
                    
                    current_idx_q = plot_names_q.index(st.session_state['qb_choice'])
                    st.selectbox("Select Plot To View:", plot_names_q, index=current_idx_q, disabled=is_running, key="qb_widget", on_change=sync_qb)
                    
                    if st.session_state['qb_choice'] != "none":
                        selected_path_q = saved_plots_q[plot_names_q.index(st.session_state['qb_choice'])]
                        st.image(selected_path_q, width='stretch')
                else:
                    st.warning("No Plots Were Found.")

    return qb_status, qb_container

def render_rabi_ui():
    is_running = st.session_state['running']
    st.header("Rabi Scan", anchor=False)

    controls_col, plot_col = st.columns([1, 2])
    with controls_col:
        st.subheader("Settings", anchor=False)
        with st.expander("Scan Parameters", expanded=True):
            c1, c2 = st.columns(2)
            c1.number_input("Readout Freq (Hz)", format="%.4e", step=None, disabled=is_running, key="rabi_readout_freq")
            c2.number_input("Readout Power (dBm)", step=None, disabled=is_running, key="rabi_readout_power")
            
            st.divider()
            c3, c4 = st.columns(2)
            c3.number_input("Qubit Freq (Hz)", format="%.4e", step=None, disabled=is_running, key="rabi_qubit_freq")
            st.text_input("Qubit Powers (dBm, Comma-Separated)", disabled=is_running, key="rabi_powers")
            
            st.divider()
            c5, c6 = st.columns(2)
            c5.number_input("Start Time (s)", format="%.4e", step=None, disabled=is_running, key="rabi_start")
            c6.number_input("Stop Time (s)", format="%.4e", step=None, disabled=is_running, key="rabi_stop")
            
            c7, c8 = st.columns(2)
            c7.number_input("Noise (1–inf)", step=None, disabled=is_running, key="rabi_ifbw")
            c8.number_input("Averages", step=None, disabled=is_running, key="rabi_averages")
            
            st.divider()
            adaptive_scan_rabi = st.checkbox("Adaptive Scan", disabled=is_running, key="rabi_adaptive")
            naive_scan_rabi = not adaptive_scan_rabi
            
            c9, c10, c11 = st.columns(3)
            c9.number_input("Dense Points", step=None, disabled=is_running or (not naive_scan_rabi), key="rabi_dense")
            c10.number_input("Coarse Points", step=None, disabled=is_running or naive_scan_rabi, key="rabi_coarse")
            c11.number_input("Adaptive Points", step=None, disabled=is_running or naive_scan_rabi, key="rabi_adapt")

        if st.button("Run Rabi Scan", width='stretch', disabled=is_running, key="rabi_run_btn"):
            st.session_state['running'] = True
            st.session_state['execute_rabi_sim'] = True
            st.rerun()

    with plot_col:
        st.subheader("Results", anchor=False)
        rabi_status = st.empty()
        rabi_container = st.container()
        
        if st.session_state.get('rabi_sim_finished', False) and not st.session_state.get('execute_rabi_sim', False):
            rabi_status.success("Rabi Scan Complete!")
        elif not st.session_state.get('execute_rabi_sim', False):
            rabi_status.info("Configure Parameters And Click 'Run Rabi Scan'.")

        with rabi_container:
            if st.session_state.get('rabi_sim_finished', False):
                selected_power_str = ""
                choice = st.session_state.get('rabi_choice', 'none')
                if choice != "none" and "dBm" in choice:
                    selected_power_str = choice.split("_")[-1].replace("dBm.png", "")
                
                if selected_power_str:
                    try:
                        p_val = float(selected_power_str)
                        if p_val in st.session_state.get('rabi_results', {}):
                            freq, pi_pulse, decay = st.session_state['rabi_results'][p_val]
                            st.info(f"Drive: {p_val} dBm | Pi Pulse: {pi_pulse*1e9:.2f} ns | Osc Freq: {freq/1e6:.4f} MHz")
                    except ValueError:
                        pass
                
                saved_plots_r = glob.glob(f"{st.session_state['rabi_plot_dir']}/*.png")
                if saved_plots_r:
                    saved_plots_r.sort() 
                    plot_names_r = [os.path.basename(p) for p in saved_plots_r] + ["none"]
                    
                    if st.session_state['rabi_choice'] not in plot_names_r:
                        st.session_state['rabi_choice'] = "none"
                    
                    current_idx_r = plot_names_r.index(st.session_state['rabi_choice'])
                    st.selectbox("Select Plot To View:", plot_names_r, index=current_idx_r, disabled=is_running, key="rabi_widget", on_change=sync_rabi)
                    
                    if st.session_state['rabi_choice'] != "none":
                        selected_path_r = saved_plots_r[plot_names_r.index(st.session_state['rabi_choice'])]
                        st.image(selected_path_r, width='stretch')
                else:
                    st.warning("No Plots Were Found.")

    return rabi_status, rabi_container

def render_ramsey_ui():
    is_running = st.session_state['running']
    st.header("Ramsey Scan", anchor=False)

    controls_col, plot_col = st.columns([1, 2])
    with controls_col:
        st.subheader("Settings", anchor=False)
        with st.expander("Scan Parameters", expanded=True):
            c1, c2 = st.columns(2)
            c1.number_input("Readout Freq (Hz)", format="%.4e", step=None, disabled=is_running, key="ramsey_readout_freq")
            c2.number_input("Readout Power (dBm)", step=None, disabled=is_running, key="ramsey_readout_power")
            
            st.divider()
            c3, c4 = st.columns(2)
            c3.number_input("Qubit Freq (Hz)", format="%.4e", step=None, disabled=is_running, key="ramsey_qubit_freq")
            c4.number_input("Qubit Power (dBm)", step=None, disabled=is_running, key="ramsey_qubit_power")
            
            c5, c6 = st.columns(2)
            c5.number_input("Pi Time (s)", format="%.4e", step=None, disabled=is_running, key="ramsey_pi_time")
            c6.number_input("Detuning (Hz)", format="%.4e", step=None, disabled=is_running, key="ramsey_detuning")
            
            st.divider()
            c7, c8 = st.columns(2)
            c7.number_input("Start Time (s)", format="%.4e", step=None, disabled=is_running, key="ramsey_start")
            c8.number_input("Stop Time (s)", format="%.4e", step=None, disabled=is_running, key="ramsey_stop")
            
            c9, c10 = st.columns(2)
            c9.number_input("Noise (1–inf)", step=None, disabled=is_running, key="ramsey_ifbw")
            c10.number_input("Averages", step=None, disabled=is_running, key="ramsey_averages")
            
            st.divider()
            adaptive_scan_ramsey = st.checkbox("Adaptive Scan", disabled=is_running, key="ramsey_adaptive")
            naive_scan_ramsey = not adaptive_scan_ramsey
            
            c11, c12, c13 = st.columns(3)
            c11.number_input("Dense Points", step=None, disabled=is_running or (not naive_scan_ramsey), key="ramsey_dense")
            c12.number_input("Coarse Points", step=None, disabled=is_running or naive_scan_ramsey, key="ramsey_coarse")
            c13.number_input("Adaptive Points", step=None, disabled=is_running or naive_scan_ramsey, key="ramsey_adapt")

        if st.button("Run Ramsey Scan", width='stretch', disabled=is_running, key="ramsey_run_btn"):
            st.session_state['running'] = True
            st.session_state['execute_ramsey_sim'] = True
            st.rerun()

    with plot_col:
        st.subheader("Results", anchor=False)
        ramsey_status = st.empty()
        ramsey_container = st.container()
        
        if st.session_state.get('ramsey_sim_finished', False) and not st.session_state.get('execute_ramsey_sim', False):
            ramsey_status.success("Ramsey Scan Complete!")
        elif not st.session_state.get('execute_ramsey_sim', False):
            ramsey_status.info("Configure Parameters And Click 'Run Ramsey Scan'.")

        with ramsey_container:
            if st.session_state.get('ramsey_sim_finished', False):
                decay = st.session_state.get('ramsey_t2_star', 0)
                freq = st.session_state.get('ramsey_detuning_freq', 0)
                st.info(f"T2*: {decay*1e9:.4f} ns | Fitted Detuning: {freq/1e6:.4f} MHz")
                
                saved_plots_ramsey = glob.glob(f"{st.session_state['ramsey_plot_dir']}/*.png")
                if saved_plots_ramsey:
                    saved_plots_ramsey.sort() 
                    plot_names_ramsey = [os.path.basename(p) for p in saved_plots_ramsey] + ["none"]
                    
                    if st.session_state['ramsey_choice'] not in plot_names_ramsey:
                        st.session_state['ramsey_choice'] = "none"
                    
                    current_idx_ramsey = plot_names_ramsey.index(st.session_state['ramsey_choice'])
                    st.selectbox("Select Plot To View:", plot_names_ramsey, index=current_idx_ramsey, disabled=is_running, key="ramsey_widget", on_change=sync_ramsey)
                    
                    if st.session_state['ramsey_choice'] != "none":
                        selected_path_ramsey = saved_plots_ramsey[plot_names_ramsey.index(st.session_state['ramsey_choice'])]
                        st.image(selected_path_ramsey, width='stretch')
                else:
                    st.warning("No Plots Were Found.")

    return ramsey_status, ramsey_container

def render_t1_ui():
    is_running = st.session_state['running']
    st.header("T1 Scan", anchor=False)

    controls_col, plot_col = st.columns([1, 2])
    with controls_col:
        st.subheader("Settings", anchor=False)
        with st.expander("Scan Parameters", expanded=True):
            c1, c2 = st.columns(2)
            c1.number_input("Readout Freq (Hz)", format="%.4e", step=None, disabled=is_running, key="t1_readout_freq")
            c2.number_input("Readout Power (dBm)", step=None, disabled=is_running, key="t1_readout_power")
            
            st.divider()
            c3, c4 = st.columns(2)
            c3.number_input("Qubit Freq (Hz)", format="%.4e", step=None, disabled=is_running, key="t1_qubit_freq")
            c4.number_input("Qubit Power (dBm)", step=None, disabled=is_running, key="t1_qubit_power")
            
            st.number_input("Pi Time (s)", format="%.4e", step=None, disabled=is_running, key="t1_pi_time")
            
            st.divider()
            c5, c6 = st.columns(2)
            c5.number_input("Start Time (s)", format="%.4e", step=None, disabled=is_running, key="t1_start")
            c6.number_input("Stop Time (s)", format="%.4e", step=None, disabled=is_running, key="t1_stop")
            
            c7, c8 = st.columns(2)
            c7.number_input("Noise (1–inf)", step=None, disabled=is_running, key="t1_ifbw")
            c8.number_input("Averages", step=None, disabled=is_running, key="t1_averages")
            
            st.divider()
            st.number_input("Dense Sweep Points", step=None, disabled=is_running, key="t1_dense")

        if st.button("Run T1 Scan", width='stretch', disabled=is_running, key="t1_run_btn"):
            st.session_state['running'] = True
            st.session_state['execute_t1_sim'] = True
            st.rerun()

    with plot_col:
        st.subheader("Results", anchor=False)
        t1_status = st.empty()
        t1_container = st.container()
        
        if st.session_state.get('t1_sim_finished', False) and not st.session_state.get('execute_t1_sim', False):
            t1_status.success("T1 Scan Complete!")
        elif not st.session_state.get('execute_t1_sim', False):
            t1_status.info("Configure Parameters And Click 'Run T1 Scan'.")

        with t1_container:
            if st.session_state.get('t1_sim_finished', False):
                t1_val = st.session_state.get('t1_relaxation_time', 0)
                st.info(f"T1 Decay: {t1_val*1e9:.4f} ns")
                
                saved_plots_t1 = glob.glob(f"{st.session_state['t1_plot_dir']}/*.png")
                if saved_plots_t1:
                    saved_plots_t1.sort() 
                    plot_names_t1 = [os.path.basename(p) for p in saved_plots_t1] + ["none"]
                    
                    if st.session_state['t1_choice'] not in plot_names_t1:
                        st.session_state['t1_choice'] = "none"
                    
                    current_idx_t1 = plot_names_t1.index(st.session_state['t1_choice'])
                    st.selectbox("Select Plot To View:", plot_names_t1, index=current_idx_t1, disabled=is_running, key="t1_widget", on_change=sync_t1)
                    
                    if st.session_state['t1_choice'] != "none":
                        selected_path_t1 = saved_plots_t1[plot_names_t1.index(st.session_state['t1_choice'])]
                        st.image(selected_path_t1, width='stretch')
                else:
                    st.warning("No Plots Were Found.")

    return t1_status, t1_container
