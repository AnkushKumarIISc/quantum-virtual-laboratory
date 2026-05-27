import streamlit as st


def setup_page():
    st.set_page_config(page_title="Qubit Characterization", layout="wide")
    st.markdown(
        """
        <style>
            [data-testid="stNumberInputStepUp"] {display: none !important;}
            [data-testid="stNumberInputStepDown"] {display: none !important;}
            input[type="number"]::-webkit-inner-spin-button, 
            input[type="number"]::-webkit-outer-spin-button {
                -webkit-appearance: none !important; margin: 0 !important;
            }
            input[type="number"] { -moz-appearance: textfield !important; }
            .stAppDeployButton, .stDeployButton { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
def init_state():
    flags = [
        'running', 'execute_res_sim', 'res_sim_finished', 
        'execute_qubit_sim', 'qubit_sim_finished',
        'execute_rabi_sim', 'rabi_sim_finished',
        'execute_ramsey_sim', 'ramsey_sim_finished',
        'execute_t1_sim', 't1_sim_finished'
    ]
    for flag in flags:
        if flag not in st.session_state:
            st.session_state[flag] = False

    choices = ['res_choice', 'qb_choice', 'rabi_choice', 'ramsey_choice', 't1_choice']
    for c in choices:
        if c not in st.session_state:
            st.session_state[c] = "none"

    defaults = {
        'dut_wc': 6.0e9, 'dut_wq': 5.2e9, 'dut_g': 200e6, 'dut_Q': 2000, 'dut_t1': 100e-9, 'dut_t2': 200e-9, 'dut_tc': False,
        'res_powers': "-100", 'res_start': 5.5e9, 'res_stop': 6.5e9, 'res_ifbw': 1000, 'res_averages': 100,
        'res_adaptive': True, 'res_dense': 401, 'res_coarse': 101, 'res_adapt': 25, 'res_iters': 3,
        'qb_readout_freq': 6.05e9, 'qb_readout_power': -100.0, 'qb_powers': "-90", 'qb_start': 4.5e9, 'qb_stop': 5.5e9, 'qb_ifbw': 1000, 'qb_averages': 100,
        'qb_adaptive': True, 'qb_dense': 401, 'qb_coarse': 101, 'qb_adapt': 25, 'qb_iters': 3,
        'rabi_readout_freq': 6.05e9, 'rabi_readout_power': -100.0, 'rabi_qubit_freq': 5.2e9, 'rabi_powers': "-80",
        'rabi_start': 0e-9, 'rabi_stop': 500e-9, 'rabi_ifbw': 1, 'rabi_averages': 1000,
        'rabi_adaptive': True, 'rabi_dense': 101, 'rabi_coarse': 20, 'rabi_adapt': 40,
        'ramsey_readout_freq': 6.05e9, 'ramsey_readout_power': -100.0, 'ramsey_qubit_freq': 5.2e9, 'ramsey_qubit_power': -80.0,
        'ramsey_pi_time': 50e-9, 'ramsey_detuning': 10e6, 'ramsey_start': 0e-9, 'ramsey_stop': 500e-9,
        'ramsey_ifbw': 1, 'ramsey_averages': 1000, 'ramsey_adaptive': True, 'ramsey_dense': 101, 'ramsey_coarse': 20, 'ramsey_adapt': 40,
        't1_readout_freq': 6.05e9, 't1_readout_power': -100.0, 't1_qubit_freq': 5.2e9, 't1_qubit_power': -80.0,
        't1_pi_time': 50e-9, 't1_start': 0e-9, 't1_stop': 500e-9, 't1_ifbw': 1, 't1_averages': 1000, 't1_dense': 101
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if 'pending_updates' in st.session_state:
        for key, value in st.session_state['pending_updates'].items():
            st.session_state[key] = value
        del st.session_state['pending_updates']
        