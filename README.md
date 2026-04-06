This repository contains the implementation used in the paper:

Jiyong Lee, Melody Agustin, Joanne Langsdorf, Erhan Kutanolgu, Michael Baldea, and Ilias Mitrai  
"Grid Capacity Expansion under Data Center and Electrified Manufacturing Loads.", Under Review

If you use this repository or build upon this work, please cite the paper above.

## Grid Capacity Expansion Planning Model Under Large Loads from Data Centers and Electrified Manufacturing
Version 1.0.

This repository provides the implementation of a **multi-period grid capacity expansion planning (GCEP) model** developed to study the impacts of rapidly growing electricity demand from data centers and electrified manufacturing on power system investment decisions.

The model is formulated as a **linear programming (LP) optimization problem** using **Pyomo** environment and solved with commercial solver **Gurobi**. The model determines optimal investment and operation strategies for generation, transmission, and storage over a multi-year planning horizon while satisfying hourly power balance and network constraints.

The framework is applied to the **synthetic grid: TEXAS 123-BT** and integrates multiple datasets, including:

- spatially distributed generation and transmission network,
- time-series electricity demand (load) and renewable generation profiles,
- representative-day clustering for computational tractability,
- projected electricity demand from data centers and electrified oil refining, and
- technology cost and fuel price.

The repository contains scripts for:

- building and solving the multi-period grid expansion planning model,
- performing post-processing and multi-year results analysis, and
- generating figures used in the associated study.





--- DESCRIPTIONS ---

## 1. Files and Roles

- **`Case2_LP_multi-periods.py`**  
  Linear optimization model for the multi‑period grid capacity expansion planning on the reference grid of Texas 123‑BT.

- **`Case2_Analysis_excel.py`**  
  Stand‑alone Python script that loads a solved Pyomo model from a `.pkl` file (exported by `Case2_LP_multi-periods.py`) and produces multi‑year summary tables and metrics (saved as Excel workbooks).

- **`Case2_Analysis_plot.ipynb`** 
  Jupyter notebook version of the results analysis, intended for figure generation for the paper/report.

- **Synthetic grid (Texas 123‑BT) data files (inputs to the LP model)**
   Retrieved from the Lu et al. "A Synthetic Texas Power System with Time-Series Weather-Dependent Spatiotemporal Profiles" and modified
  - `TEXAS 123-BT params (bus).csv`: bus information including location, name, weather zone, counties and etc.
  - `TEXAS 123-BT params (generation).csv`: used for initial generation capacity profiles
  - `TEXAS 123-BT params (line).csv`: transmission lines locations, initial capacities, and properties

- **Time‑series and clustering data (inputs to the LP model)**  
  - `TimeSeries/Results Load+CF Clusters/cluster_centers_per_bus.csv`: clustered base load, solar and wind capacity factors hourly profiles for every bus and representative days
  - `TimeSeries/Results Load+CF Clusters/cluster_weights.csv`: weighted days for each representative day (used for summing over days)

- **`TimeSeries/Days Clustering (Load, CF_wind, CF_solar).py` (to modify clusters)**  
  - Script that performs time‑series K‑means clustering on hourly base load and solar/wind capacity‑factor profiles and generates the representative‑day cluster centers and their weights saved in `TimeSeries/Results Load+CF Clusters/`.
  - Through this script, one can generate different representative days

- **Scenario and regional load split‑ratio data for Case 2 (inputs to the LP model)**  
  - `Load_Scenario (2019-2031).csv`: load growth scenario and breakdowns by demand sources (base, data centers, electirifed oil refineries) for seven-year planning horizon from 2019 to 2031. 
  - `Split_Ratio_DataCenters.csv` : regional (county-level) data center load split ratio. provides the counties where data centers located, and their load share for every year. data retrieved and reconstructed from NREL https://maps.nrel.gov/speed-to-power/data-viewer
  - `Split_Ratio_EOR.csv` : regional (county-level) electrified oil refining load split ratio. provides the counties where oil refineries located, and their load share for every year. data retrieved and resconstructed from McMilan et al. (2018) "Industrial process heat demand characterization"

- **Cost and fuel‑price data (inputs to the LP model)**  
  - `ATB2024_NREL_COST PARAMS_nuclearOPEXadded.csv` : CAPEX, OPEX data for generation and storage
  - `AEO2023_EIA_FUEL COST PARAMS.csv`: fuel price of natural gas, coal and nuclear

- **Model result files (outputs of the LP model)**  
  - `Case2_model_results_*.pkl`: pyomo model results file in `.pkl`, saved from the model `Case2_LP_multi-periods.py`.  
  - `Case2_Analysis_*.xlsx`: excel workbooks with summary, multi-year metrics, investments, curtailment, and energy balance. created from `Case2_Analysis_excel.py`
  - figures files generated and saved from the `Case2_Analysis_plot.ipynb`

---

## 2. Software Dependencies

The following dependencies are used across the project's scripts:

- **Python** v 3.12.3
- **Packages**
  - `pyomo` v 6.9.2
  - `pandas` v 2.2.2
  - `numpy` v 1.26.4
  - `openpyxl` v 3.1.5

- **Optimization solver**
  - **Gurobi** v 12.0.0
    - Requires a valid Gurobi installation and license.

- **Standard library modules**
  - `os`, `sys`, `time`, `math`, `pickle`, `datetime`, `pathlib` (implicit), etc.

For running the Jupyter notebook:

- **Jupyter**
  - `jupyter notebook` v 7.2.2

---

## 3. How to Run the Model

### 3.1 Running the LP model (`Case2_LP_multi-periods.py`)

1. **Clone or download** this repository and ensure that all required input CSV files listed in Section 1 are present under the same folder structure as this script (relative paths are used inside the code).  
2. **Install Python dependencies** and make sure Gurobi is installed and accessible from Pyomo.  
3. From the `Project` directory, run (for example):

```bash
python Case2_LP_multi-periods.py
```

4. The script will:
   - Build the Pyomo model using the synthetic grid and input parameters.  
   - Call Gurobi to solve the optimization problem.  
   - Save the solved model object to a timestamped `.pkl` file. path is currently set as the **results** folder in the relative path of this script. (you may change to desired path)

### 3.2 Running the analysis script (`Case2_Analysis_excel.py`)

1. Make sure at least one `.pkl` file produced by `Case2_LP_multi-periods.py` is available at the location expected by the analysis script (the path is currently configured inside `Case2_Analysis.py`).  
2. From the `Project` directory, run:

```bash
python Case2_Analysis_excel.py
```

3. The script will:
   - Load the specified `.pkl` model.  
   - Reconstruct key sets/parameters required for reading results.  
   - Compute a collection of multi‑year indicators (capacities, costs, curtailment, etc.).  
   - Export them into an Excel file with multiple sheets (summary, multi‑year metrics, technology‑specific tables, etc.).

### 3.3 Figure generation using the Jupyter notebook (`Case2_Analysis_plot.ipynb`)

1. Launch Jupyter in this directory:

```bash
jupyter notebook
```

2. Open `Case2_Analysis_plot.ipynb` and edit the input `.pkl` path if necessary.  
3. Run the cells sequentially to:
   - Load a solved model.  
   - Generate plots with desired formats.  
   - Customize figures for publication‑quality graphics.

---

## 4. Notes
- This README is not a full methodological description; please refer to the associated paper for model formulation and assumptions.

