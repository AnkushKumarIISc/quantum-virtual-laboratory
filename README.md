# Simulating and Automating Quantum Measurements for Characterizing Transmon Qubits

A modular, simulation-based characterization software for transmon qubit-resonator systems.


## Key Features
* **Physics Engine:** Simulated dynamics of transmon qubit-resonator system using QuTiP (Quantum Toolbox in Python).
* **Virtual Instruments:** Object-oriented implementations of a Vector Network Analyzer (VNA), Signal Generator (SG), and Qubit Controller (SHFQC).
* **Automated Pipeline:** Sequential execution of core characterization experiments:
  1. **Resonator Scan:** Locates readout cavity.
  2. **Qubit Scan:** Locates qubit transition.
  3. **Rabi Scan:** Calibrates $\pi$-pulse duration.
  4. **Ramsey Scan:** Extracts $T_2^*$ and fine-tunes drive frequency.
  5. **$T_1$ Scan:** Measures energy relaxation time.
* **Interactive UI:** Built with Streamlit for easy parameter tuning and visualization of experiments.


## Installation
To ensure a clean setup, it is recommended to run this project inside a Python virtual environment.

```bash
# Clone the repository
git clone https://github.com/AnkushKumarIISc/simulated-virtual-laboratory.git
cd simulated-virtual-laboratory

# Install required dependencies
pip install -r requirements.txt
```

## Usage

### 1. Interactive Web Application
Launch the Streamlit interface to configure settings, run experiments, and visualize experiment results.
```bash
streamlit run app.py
```

### 2. Command Line Automation
To execute the characterization pipeline directly from the terminal without the web interface:
1. Open `config.py` to initialize your experiment parameters.
2. Execute:
```bash
python main.py
```
