import streamlit as st
from ui.core import setup_page, init_state
from ui.components import render_dut, render_resonator_ui, render_qubit_ui, render_rabi_ui, render_ramsey_ui, render_t1_ui
from ui.engine import execute_computations


setup_page()
init_state()

st.title("Qubit Characterization", anchor=False)
st.divider()

render_dut()
st.divider()

res_status, res_container = render_resonator_ui()
st.divider()

qb_status, qb_container = render_qubit_ui()
st.divider()

rabi_status, rabi_container = render_rabi_ui()
st.divider()

ramsey_status, ramsey_container = render_ramsey_ui()
st.divider()

t1_status, t1_container = render_t1_ui()
st.divider()

execute_computations(res_status, res_container, qb_status, qb_container, rabi_status, rabi_container, ramsey_status, ramsey_container, t1_status, t1_container)
