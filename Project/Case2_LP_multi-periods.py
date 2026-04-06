# Basic imports
from pyomo.environ import *
import pandas as pd
import numpy as np
from math import pi
import time

# ----------------------------------------------------
# MODEL BUILDING TIME TRACKING
# ----------------------------------------------------
print("Starting model building...")
model_build_start_time = time.time()

# ----------------------------------------------------
# Load bus data from CSV
# ----------------------------------------------------
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

df_bus = pd.read_csv(os.path.join(script_dir, "TEXAS 123-BT params (bus).csv"))
df_gen = pd.read_csv(os.path.join(script_dir, "TEXAS 123-BT params (generation).csv"))
df_line = pd.read_csv(os.path.join(script_dir, "TEXAS 123-BT params (line).csv"))
df_cluster_centers = pd.read_csv(os.path.join(script_dir, "TimeSeries/Results Load+CF Clusters/cluster_centers_per_bus.csv"))

# Load new data files for Case2
df_load_scenario = pd.read_csv(os.path.join(script_dir, "Load_Scenario (2019-2031).csv"))
df_split_dc = pd.read_csv(os.path.join(script_dir, "Split_Ratio_DataCenters.csv"))
df_split_eor = pd.read_csv(os.path.join(script_dir, "Split_Ratio_EOR.csv"))

# ----------------------------------------------------
# Model
# ----------------------------------------------------
model = ConcreteModel()

# ----------------------------------------------------
# Sets
# ----------------------------------------------------
# Global parameters for time horizons

time_planningHorizon = 7  # Number of years in the planning horizon
time_planningStartYear = 2025  # Start year for the planning
time_financialBaseYear = 2022  # Base year for the financial analysis

time_daysHorizon = 5  # Number of days in the planning horizon (5 representative days)
time_hoursHorizon = 24  # Number of hours in a day


unit_hour = 1  # Unit hour to account for the unit match
unit_day = 1  # Unit day
unit_year = 1  # Unit year
BaseMVA = 100  # Base power in MVA, used for per unit calculations


# Create a set of valid undirected line pairs (n, n') where n < n'
# This ensures each transmission line is represented only once regardless of direction
def create_undirected_line_pairs(df_line):
    """
    Create undirected line pairs from directional line data.
    Returns pairs (n, n') where n < n', and the bidirectional connection data.
    """
    undirected_pairs = set()
    connection_data = {}  # Store all connection data for parameter calculation

    for _, row in df_line.iterrows():
        bus1 = row["From Bus Number"]
        bus2 = row["To Bus Number"]

        # Create undirected pair (ensure smaller bus number comes first)
        pair = (min(bus1, bus2), max(bus1, bus2))
        undirected_pairs.add(pair)

        # Store connection data for both directions
        if pair not in connection_data:
            connection_data[pair] = {
                "entries": [],
                "r_values": [],
                "x_values": [],
                "b_values": [],
                "capacity_values": [],
                "mile_values": [],
            }

        connection_data[pair]["entries"].append(row)
        connection_data[pair]["r_values"].append(row["R, pu"])
        connection_data[pair]["x_values"].append(row["X, pu"])
        connection_data[pair]["b_values"].append(row["B, pu"])
        connection_data[pair]["capacity_values"].append(row["Capacity (MW)"])
        connection_data[pair]["mile_values"].append(row["Length (Mile)"])

    return sorted(undirected_pairs), connection_data


valid_line_pairs, line_connection_data = create_undirected_line_pairs(df_line)

# Create a set of valid (bus_number, fuel_type) pairs
valid_gen_paris = sorted((row["Bus Number"], row["Fuel type"]) for _, row in df_gen.iterrows())

# Define sets
model.N = Set(initialize=df_bus["Bus Number"].unique())  # Set of buses
model.G = Set(initialize=valid_gen_paris, dimen=2)  # Set of generators (as pairs of bus number and fuel type. use tuples)
model.L = Set(initialize=valid_line_pairs, dimen=2)  # Set of lines (as pairs of bus numbers. use tuples)
model.T = Set(initialize=range(1, time_planningHorizon + 1))  # Set of time periods for investment decisions. 1-based indexing.
model.D = Set(initialize=range(1, time_daysHorizon + 1))  # Set of days. 1-based indexing.
model.H = Set(initialize=range(1, time_hoursHorizon + 1))  # Set of hours. 1-based indexing.
model.I_gen = Set(initialize=df_gen["Fuel type"].unique())  # Set of generator technologies
model.I_gen_TH = Set(initialize=df_gen[df_gen["Fuel type"].isin(["Natural Gas", "Coal", "Nuclear"])]["Fuel type"].unique())  # Set of thermal generator technologies
model.I_gen_RN = Set(initialize=df_gen[df_gen["Fuel type"].isin(["Wind", "Solar", "Hydro"])]["Fuel type"].unique())  # Set of renewable generators
model.W = Set(initialize=df_bus["Weather Zone"].unique())  # Set of weather zones
model.C = Set(initialize=df_split_dc["County"].unique()) # Set of counties that data centers are located in
model.E = Set(initialize=df_split_eor["County"].unique()) # Set of counties that electrification of oil refineries are located in

# ----- County-Bus Mapping for DC and EOR Counties Only ----
buses_in_county = {}  # Only for counties that have DC or EOR
all_buses_DC = set()  # All buses in any DC county
all_buses_EOR = set()  # All buses in any EOR county

for _, row in df_bus.iterrows():
    county = row["County"]
    bus_number = row["Bus Number"]

    # Add to all_buses sets if county has DC or EOR
    if county in model.C:
        all_buses_DC.add(bus_number)
        buses_in_county.setdefault(county, set()).add(bus_number)
    if county in model.E:
        all_buses_EOR.add(bus_number)
        buses_in_county.setdefault(county, set()).add(bus_number)

# Define sets for buses with DC and EOR facilities
model.N_DC = Set(initialize=sorted(all_buses_DC))  # All buses in DC counties
model.N_EOR = Set(initialize=sorted(all_buses_EOR))  # All buses in EOR counties

print("COMPLETED: defining sets")


# ----------------------------------------------------
# Parameters
# ----------------------------------------------------
# ----- Time Parameters ----
def time_currentYear_init(model, t):
    return time_planningStartYear + t - 1


model.time_currentYear = Param(model.T, initialize=time_currentYear_init)
# t_currentYear is the current year for the time period t. To use for parameter finding for t_currentYear
# print(model.t_currentYear.extract_values())

time_gen_construction_dict = {}
for i in model.I_gen:

    fuel_type = i

    if fuel_type == "Natural Gas":
        time_gen_construction_dict[i] = 3  
    elif fuel_type == "Coal": 
        time_gen_construction_dict[i] = 5 
    elif fuel_type == "Nuclear":
        time_gen_construction_dict[i] = 6 
    elif fuel_type == "Wind":
        time_gen_construction_dict[i] = 3 
    elif fuel_type == "Solar":
        time_gen_construction_dict[i] = 1
    elif fuel_type == "Hydro":
        time_gen_construction_dict[i] = 3
    else:
        time_gen_construction_dict[i] = 0  # Default to 0 for other types

model.time_gen_construction = Param(model.I_gen, initialize=time_gen_construction_dict)

time_trans_construction_dict = 3 
model.time_trans_construction = Param(initialize=time_trans_construction_dict)

time_stor_construction_dict = 1
model.time_stor_construction = Param(initialize=time_stor_construction_dict)


# ----- Bus Parameters ----
bus_name_dict = {row["Bus Number"]: row["Bus Name"] for _, row in df_bus.iterrows()}
bus_latitude_dict = {row["Bus Number"]: row["Bus latitude"] for _, row in df_bus.iterrows()}
bus_longitude_dict = {row["Bus Number"]: row["Bus longitude"] for _, row in df_bus.iterrows()}
bus_genBool_dict = {row["Bus Number"]: row["Gen bus/ Non-gen bus"] for _, row in df_bus.iterrows()}
bus_nominalVoltage_dict = {row["Bus Number"]: row["Nominal Voltage (KV)"] for _, row in df_bus.iterrows()}
bus_weatherZone_dict = {row["Bus Number"]: row["Weather Zone"] for _, row in df_bus.iterrows()}
bus_county_dict = {row["Bus Number"]: row["County"] for _, row in df_bus.iterrows()}
bus_countyFIPS_dict = {row["Bus Number"]: row["County_FIPS"] for _, row in df_bus.iterrows()}
bus_neighboringCounties_dict = {row["Bus Number"]: row["Neighboring_Counties"] for _, row in df_bus.iterrows()}
bus_totalCountiesServed_dict = {row["Bus Number"]: row["Total_Counties_Served"] for _, row in df_bus.iterrows()}
model.bus_name = Param(model.N, initialize=bus_name_dict, within=Any)
model.bus_latitude = Param(model.N, initialize=bus_latitude_dict)
model.bus_longitude = Param(model.N, initialize=bus_longitude_dict)
model.bus_genBool = Param(model.N, initialize=bus_genBool_dict)
model.bus_nominalVoltage = Param(model.N, initialize=bus_nominalVoltage_dict)
model.bus_weatherZone = Param(model.N, initialize=bus_weatherZone_dict, within=Any)
model.bus_county = Param(model.N, initialize=bus_county_dict, within=Any)
model.bus_countyFIPS = Param(model.N, initialize=bus_countyFIPS_dict, within=Any)
model.bus_neighboringCounties = Param(model.N, initialize=bus_neighboringCounties_dict, within=Any)
model.bus_totalCountiesServed = Param(model.N, initialize=bus_totalCountiesServed_dict)


# ----- Generator Parameters ----
# Generator initial capacity based on the bus number and fuel type
gen_c_gen_init_dict = (df_gen.groupby(["Bus Number", "Fuel type"])["Pmax (MW)"].sum().to_dict())  # Group by (Bus Number, Fuel type) and sum Pmax (MW) # Note that there is multiple generators of same fuel type at the same bus
model.gen_c_gen_init = Param(model.G, initialize=gen_c_gen_init_dict)

# Generator ramping rate parameter [%*capacity_gen/min] from ATB 2024, NREL
# Assign values by fuel type for each generator in I_gen_TH
# Hydro, Solar, Wind have no ramping rate
gen_r_ramp_dict = {}
for i in model.I_gen_TH:

    fuel_type = i

    if fuel_type == "Natural Gas":
        gen_r_ramp_dict[i] = 0.05
    elif fuel_type == "Coal":
        gen_r_ramp_dict[i] = 0.04
    elif fuel_type == "Nuclear":
        gen_r_ramp_dict[i] = 0.04
    else:
        gen_r_ramp_dict[i] = 0  # Default to 0 for other types

model.gen_r_ramp = Param(model.I_gen_TH, initialize=gen_r_ramp_dict)

# ----- Line Parameters ----

def calculate_line_parameters(valid_line_pairs, line_connection_data):
    """
    Calculate line parameters for undirected transmission lines.

    For R, X, B, mile: Take average of all entries between buses n and n'
    For capacity: Sum all entries between buses n and n'
    """
    line_r_dict = {}
    line_x_dict = {}
    line_b_dict = {}
    line_c_trans_init_dict = {}
    line_mile_dict = {}

    for pair in valid_line_pairs:
        data = line_connection_data[pair]

        # Average values for R, X, B, and mile
        line_r_dict[pair] = np.mean(data["r_values"])
        line_x_dict[pair] = np.mean(data["x_values"])
        line_b_dict[pair] = np.mean(data["b_values"])
        line_mile_dict[pair] = np.mean(data["mile_values"])

        # Sum values for capacity
        line_c_trans_init_dict[pair] = sum(data["capacity_values"])

    return line_r_dict, line_x_dict, line_b_dict, line_c_trans_init_dict, line_mile_dict


line_r_dict, line_x_dict, line_b_dict, line_c_trans_init_dict, line_mile_dict = (calculate_line_parameters(valid_line_pairs, line_connection_data))

model.line_r = Param(model.L, initialize=line_r_dict)
model.line_x = Param(model.L, initialize=line_x_dict)
model.line_b = Param(model.L, initialize=line_b_dict)
model.line_c_trans_init = Param(model.L, initialize=line_c_trans_init_dict)
model.line_mile = Param(model.L, initialize=line_mile_dict)


# Pre-compute bus connections by lines for efficient energy balance constraint
bus_connections = {}
for n in model.N:
    bus_connections[n] = []

for n_min, n_max in model.L:
    bus_connections[n_min].append(n_max)
    bus_connections[n_max].append(n_min)


# ----- Storage Parameters ----
model.E_stor_level_init = Param(model.N, initialize=0)  # [MWh]. No initial storage energy (since c_stor_init = 0)
model.eta_charge = Param(initialize=sqrt(0.85))  # From ATB2024 NREL. eta_charge = eta_discharge = sqrt(eta_RTE)
model.eta_discharge = Param(initialize=sqrt(0.85))  # From ATB2024 NREL. eta_charge = eta_discharge = sqrt(eta_RTE)
model.c_stor_init = Param(model.N, initialize=0)  # [MW]. No storage is considered at the beginning of the planning horizon
model.hr_stor_max = Param(initialize=4)  # From ATB2024 NREL. hr_stor_max = 4 [hr]

print("COMPLETED: loading reference grid from TEXAS 123-BT")


# ----- Load Parameters ----
# Initialize energy parameters E_base[t], E_DC[t], E_EOR[t] from Load_Scenario CSV
def init_E_base(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["E_Base(MWh)"].iloc[0]
    return 0

def init_E_DC(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["E_DataCenters(MWh)"].iloc[0]
    return 0

def init_E_EOR(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["E_EOR(MWh)"].iloc[0]
    return 0

def init_E_total(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["E_Total(MWh)"].iloc[0]
    return 0

model.E_base = Param(model.T, initialize=init_E_base)  # Annual base load energy [MWh]
model.E_DC = Param(model.T, initialize=init_E_DC)  # Annual data center energy [MWh]
model.E_EOR = Param(model.T, initialize=init_E_EOR)  # Annual EOR energy [MWh]
model.E_total = Param(model.T, initialize=init_E_total)  # Annual total energy [MWh]


# Initialize peak power parameters P_peak_base[t], P_peak_DC[t], P_peak_EOR[t]
def init_P_peak_base(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["P_Peak_Base(MW)"].iloc[0]
    return 0

def init_P_peak_DC(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["P_Peak_DataCenters(MW)"].iloc[0]
    return 0

def init_P_peak_EOR(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["P_EOR(MW)"].iloc[0]
    return 0

def init_P_peak_total(model, t):
    year = model.time_currentYear[t]
    row = df_load_scenario[df_load_scenario["Year"] == year]
    if not row.empty:
        return row["P_Peak_Total(MW)"].iloc[0]
    return 0

model.P_peak_base = Param(model.T, initialize=init_P_peak_base)  # Annual base peak power [MW]
model.P_peak_DC = Param(model.T, initialize=init_P_peak_DC)  # Annual data center peak power [MW]
model.P_peak_EOR = Param(model.T, initialize=init_P_peak_EOR)  # Annual EOR peak power [MW]
model.P_peak_total = Param(model.T, initialize=init_P_peak_total)  # Annual total peak power [MW]


# Initialize split ratio parameters phi_DC[c] and phi_EOR[e]
def init_phi_DC(model, c):
    row = df_split_dc[df_split_dc["County"] == c]
    if not row.empty:
        return row["Split_Ratio_DC"].iloc[0]
    return 0


def init_phi_EOR(model, e):
    row = df_split_eor[df_split_eor["County"] == e]
    if not row.empty:
        return row["Split_Ratio_EOR"].iloc[0]
    return 0


model.phi_DC = Param(model.C, initialize=init_phi_DC)  # Data center split ratios by county
model.phi_EOR = Param(model.E, initialize=init_phi_EOR)  # EOR split ratios by county


# Load weight of clustered days (number of days represented by each cluster) from CSV
df_cluster_weights = pd.read_csv(os.path.join(script_dir, "TimeSeries/Results Load+CF Clusters/cluster_weights.csv"))

weight_repDays_dict = {}
for idx, row in df_cluster_weights.iterrows():
    day_id = row["cluster"] + 1
    weight_repDays_dict[day_id] = row["days"]

# Declare the parameter for representative day counts
model.weight_repDays = Param(model.D, initialize=weight_repDays_dict)
# model.weight_repDays = Param(model.D, initialize=1)

# Function to initialize D_base from cluster centers CSV (base year only)
def init_D_base_2019(model, n, t, d, h):
    """
    Initialize D_base parameter from cluster centers data for year 2019.
    n: bus number, t: dummy set, d: day (cluster), h: hour
    """
    # Convert from 1-based indexing to 0-based for CSV lookup
    cluster = d - 1  # model.D is 1-based, CSV cluster is 0-based
    bus = n  # both are 1-based
    hour = h  # both are 1-based

    # Find the corresponding row in the CSV for load data
    row = df_cluster_centers[(df_cluster_centers["parameter"] == "load") & (df_cluster_centers["cluster"] == cluster) & (df_cluster_centers["bus"] == bus)]

    if not row.empty:
        return row[f"hour_{hour}"].iloc[0]
    else:
        return 0  # Default value if not found


# Function to initialize D_base with time dimension
def init_D_base(model, n, t, d, h):
    """
    Initialize base load "D_base" parameter from cluster centers data with time dimension.
    n: bus number, t: year, d: day, h: hour
    """
    # Get D_base 2019
    D_base_2019 = init_D_base_2019(model, n, t, d, h)  # base load profile for 2019

    # Calculate alpha load increment factor
    E_base_2019 = 383845048  # [MWh]

    delta_E_base = model.E_base[t] - E_base_2019
    alpha = delta_E_base / (123 * 365 * 24)
    # N: 123 buses, D: 365 days, H: 24 hours - equal distribution [MW]

    D_base = D_base_2019 + alpha

    return D_base

model.D_base = Param(model.N, model.T, model.D, model.H, initialize=init_D_base)  # Base load


def init_D_DC(model, c, t, d, h):
    """
    Initialize data center load "D_DC" parameter.
    Assumed LF=0.9 from the peak load, and flat load profile
    c: county of data centers, t: year, d: day, h: hour
    """

    D_DC = model.phi_DC[c] * model.E_DC[t] / (365 * 24)  # [MW]

    return D_DC

model.D_DC = Param(model.C, model.T, model.D, model.H, initialize=init_D_DC)  # Data centers load


def init_D_EOR(model, e, t, d, h):
    """
    Initialize electrification of oil refineries load "D_EOR" parameter.
    Assumed  flat load profile
    e: county of EOR, t: year, d: day, h: hour
    """
    D_EOR = model.phi_EOR[e] * model.E_EOR[t] / (365 * 24)  # [MW]

    return D_EOR

model.D_EOR = Param(model.E, model.T, model.D, model.H, initialize=init_D_EOR)  # EOR load

print("COMPLETED: setting load parameters (D_base, D_DC, D_EOR)")


# ----- Investment Parameters ----
# Maximum capacity for generators, transmission lines, and storage
model.c_gen_max = Param(model.G, initialize=100000)  # Maximum gen capacity (MW) for generators. Increased to allow sufficient capacity expansion
model.c_trans_max = Param(model.L, initialize=100000)  # Maximum capacity for transmission lines (MW).
model.c_stor_max = Param(model.N, initialize=100000)  # Maximum capacity for storage at each bus (MW).


# ----- Objective Function Parameters ----
# Cost parameters for CAPEX and OPEX
# CAREFUL ABOUT UNITS WHEN IMPLOYING A NEW PARAMETER eg. $/MW, $/MWh

# alpha_CAPEX_gen, alpha_CAPEX_trans, gamma_stor
# VOM_gen, COST_fuel, HR, FOM_gen

# Financial Parameters
def DF(Ir, currentYear, baseYear):
    """
    Calculate the discount factor (DF) given an interest rate, current year, and base year.

    DF = 1 / (1 + Ir) ** (currentYear - baseYear)

    Args:
        Ir (float): Interest rate (as a decimal, e.g., 0.05 for 5%)
        currentYear (int): The year for which the discount factor is calculated
        baseYear (int): The reference year

    Returns:
        float: The discount factor
    """
    return 1 / (1 + Ir) ** (currentYear - baseYear)

Ir = 0.044  # Interest rate of scenario "moderate" from ATB(2024) NREL

# ----------------------------------------------------
# Load ATB2024 NREL Cost Parameters
# ----------------------------------------------------

# Load the ATB CSV data
atb_csv_path = os.path.join(script_dir, "ATB2024_NREL_COST PARAMS_nuclearOPEXadded.csv")
df_atb = pd.read_csv(atb_csv_path)

# Technology mapping from model I_gen to ATB display_name
tech_mapping = {
    "Coal": "Coal-new",
    "Natural Gas": "NG 2-on-1 Combined Cycle (H-Frame)",
    "Nuclear": "Nuclear - Large",  # For nuclear, nuclear-small (SMR) is also available in the ATB data.
    "Solar": "Utility PV - Class 4",
    "Wind": "Land-Based Wind - Class 4 - Technology 1",
    "Hydro": "Hydropower - NPD 2",
}

# Thermal units for heat rate mapping
thermal_units = ["Coal", "Nuclear", "Natural Gas"]

def get_atb_value(display_name, core_metric_parameter, year):
    """Extract value from ATB data for specific technology, parameter, and year"""
    filtered_data = df_atb[
        (df_atb["display_name"] == display_name)
        & (df_atb["core_metric_parameter"] == core_metric_parameter)
        & (df_atb["core_metric_variable"] == year)
    ]

    if not filtered_data.empty:
        return filtered_data["value"].iloc[0]
    else:
        print(f"WARNING: No data found for {display_name}, {core_metric_parameter}, {year}")
        return 0

def print_parameter_summary(param_name, param_dict):
    """Print a summary of loaded parameters for verification"""
    print(f"\n--- {param_name} ---")
    for key, value in param_dict.items():
        if isinstance(key, tuple):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value:.2f}")


# ----------------------------------------------------
# 1. CAPEX Parameters
# ----------------------------------------------------

# alpha_CAPEX_gen[i,t] - Generation CAPEX
alpha_CAPEX_gen_dict = {}
for tech in model.I_gen:
    for t in model.T:
        if tech in tech_mapping:
            atb_tech = tech_mapping[tech]
            value = get_atb_value(atb_tech, "CAPEX", model.time_currentYear[t])
            alpha_CAPEX_gen_dict[(tech, t)] = value
        else:
            alpha_CAPEX_gen_dict[(tech, t)] = 0

# print_parameter_summary("alpha_CAPEX_gen", alpha_CAPEX_gen_dict)

# alpha_CAPEX_trans
alpha_CAPEX_trans_dict = 0.93  # [$/miles*kW] this is the value for the reference: Estimation of Transmission Costs for New Generation. UT Austin 2017.

# alpha_CAPEX_stor[t] - Battery Storage CAPEX
alpha_CAPEX_stor_dict = {}
for t in model.T:
    current_year = model.time_currentYear[t]
    value = get_atb_value("Utility-Scale Battery Storage - 4Hr", "CAPEX", current_year)
    alpha_CAPEX_stor_dict[t] = value if value > 0 else 0

# print_parameter_summary("alpha_CAPEX_stor", alpha_CAPEX_stor_dict)

# ----------------------------------------------------
# 2. OPEX Parameters
# ----------------------------------------------------

# VOM_gen[i,t] - Variable O&M
VOM_gen_dict = {}
for tech in model.I_gen:
    for t in model.T:
        current_year = model.time_currentYear[t]
        if tech in tech_mapping:
            atb_tech = tech_mapping[tech]
            value = get_atb_value(atb_tech, "Variable O&M", current_year)
            # VOM = 0 for solar, wind, and hydro
            if value == 0 and tech in ["Solar", "Wind", "Hydro"]:
                if tech == "Solar":
                    value = 0.0  # Solar PV has very low VOM
                elif tech == "Wind":
                    value = 0.0  # Wind has very low VOM
                elif tech == "Hydro":
                    value = 0.0  # Hydro has very low VOM
            VOM_gen_dict[(tech, t)] = value
        else:
            VOM_gen_dict[(tech, t)] = 0

# print_parameter_summary("VOM_gen", VOM_gen_dict)

# FOM_gen[i,t] - Fixed O&M
FOM_gen_dict = {}
for tech in model.I_gen:
    for t in model.T:
        current_year = model.time_currentYear[t]
        if tech in tech_mapping:
            atb_tech = tech_mapping[tech]
            value = get_atb_value(atb_tech, "Fixed O&M", current_year)
            FOM_gen_dict[(tech, t)] = value
        else:
            FOM_gen_dict[(tech, t)] = 0

# print_parameter_summary("FOM_gen", FOM_gen_dict)

# COST_fuel[i,t] - Fuel costs from AEO2023
# Tech to fuel mapping for AEO2023 data
tech_fuel_mapping = {
    "Coal": "Steam Coal",
    "Natural Gas": "Natural Gas",
    "Nuclear": "Uranium",
}

# Load AEO2023 fuel cost data
aeo_csv_path = os.path.join(script_dir, "AEO2023_EIA_FUEL COST PARAMS.csv")
df_aeo = pd.read_csv(aeo_csv_path)

def get_aeo_fuel_cost(fuel_name, year):
    """Extract fuel cost from AEO2023 data for specific fuel and year"""
    filtered_data = df_aeo[(df_aeo["fuel"] == fuel_name) & (df_aeo["year"] == year)]

    if not filtered_data.empty:
        return filtered_data["value"].iloc[0]
    else:
        print(f"WARNING: No fuel cost data found for {fuel_name}, {year}")
        return 0

COST_fuel_dict = {}
for tech in model.I_gen:
    for t in model.T:
        current_year = model.time_currentYear[t]
        if tech in tech_fuel_mapping:
            fuel_name = tech_fuel_mapping[tech]
            fuel_cost = get_aeo_fuel_cost(fuel_name, current_year)
            COST_fuel_dict[(tech, t)] = fuel_cost
        else:
            # Non-thermal generators (Wind, Solar, Hydro) have zero fuel cost
            COST_fuel_dict[(tech, t)] = 0

# print_parameter_summary("COST_fuel", COST_fuel_dict)

# HeatRate[i,t] - Heat Rate for thermal units only
HeatRate_dict = {}
for tech in model.I_gen:
    for t in model.T:
        current_year = model.time_currentYear[t]
        if tech in thermal_units and tech in tech_mapping:
            atb_tech = tech_mapping[tech]
            value = get_atb_value(atb_tech, "Heat Rate", current_year)
            HeatRate_dict[(tech, t)] = value
        else:
            # Non-thermal units get 0 heat rate
            HeatRate_dict[(tech, t)] = 0

# print_parameter_summary("HeatRate", HeatRate_dict)

# FOM_stor[t] - Storage Fixed O&M
FOM_stor_dict = {}
for t in model.T:
    current_year = model.time_currentYear[t]
    stor_fom_value = get_atb_value("Utility-Scale Battery Storage - 4Hr", "Fixed O&M", current_year)
    FOM_stor_dict[t] = stor_fom_value

# print_parameter_summary("FOM_stor", FOM_stor_dict)

# VOM_stor is zero for battery storage


# ----------------------------------------------------
# 3. Curtailment Parameters
# ----------------------------------------------------
# For later, curtailment can be break down into residential, data center, and chemical manufacturing.
alpha_curt_dict = 5000  # [$/MWh] for curtailment.
alpha_curt_gen_dict = 100  # [$/MWh] for curtailment by generators.

# ----------------------------------------------------
# Create Pyomo Parameters
# ----------------------------------------------------

# CAPEX parameters
model.alpha_CAPEX_gen = Param(model.I_gen, model.T, initialize=alpha_CAPEX_gen_dict)
model.alpha_CAPEX_trans = Param(initialize=alpha_CAPEX_trans_dict)
model.alpha_CAPEX_stor = Param(model.T, initialize=alpha_CAPEX_stor_dict)

# OPEX parameters
model.VOM_gen = Param(model.I_gen, model.T, initialize=VOM_gen_dict)
model.FOM_gen = Param(model.I_gen, model.T, initialize=FOM_gen_dict)
model.COST_fuel = Param(model.I_gen, model.T, initialize=COST_fuel_dict)
model.HeatRate = Param(model.I_gen, model.T, initialize=HeatRate_dict)
model.FOM_stor = Param(model.T, initialize=FOM_stor_dict)

# Curtailment parameters
model.alpha_curt = Param(initialize=alpha_curt_dict)
model.alpha_curt_gen = Param(initialize=alpha_curt_gen_dict)

print("COMPLETED: setting cost parameters and heat rate (CAPEX_gen, CAPEX_trans, CAPEX_stor, FOM_stor, VOM_gen, FOM_gen, COST_fuel, HeatRate)")

# ----------------------------------------------------
# Capacity Factor Parameters
# ----------------------------------------------------

# Thermal generators minimum and maximum capacity factors (ATB 2024 NREL)
CF_TH_min_dict = {"Nuclear": 0.15, "Coal": 0.4, "Natural Gas": 0.5}
CF_TH_max_dict = {"Nuclear": 0.91, "Coal": 0.82, "Natural Gas": 0.85}

model.CF_TH_min = Param(model.I_gen_TH, initialize=CF_TH_min_dict)
model.CF_TH_max = Param(model.I_gen_TH, initialize=CF_TH_max_dict)

# Hydro capacity factor (fixed throughout the year)
CF_RN_hydro_dict = {"Hydro": 0.41}
model.CF_RN_hydro = Param(model.I_gen_RN, initialize=CF_RN_hydro_dict, default=0)


# Function to initialize CF_RN (Solar and Wind capacity factors from cluster data)
# Calculated from the cluster centers data for Solar and Wind original data from TX-123BT
def init_CF_RN(model, n, i, d, h):
    """
    Initialize CF_RN parameter from cluster centers data for Solar and Wind.
    n: bus number, i: technology (Solar/Wind), d: day (cluster), h: hour
    """
    if i not in ["Solar", "Wind"]:
        return 0  # Only Solar and Wind use this parameter

    # Convert from 1-based indexing to 0-based for CSV lookup
    cluster = d - 1  # model.D is 1-based, CSV cluster is 0-based
    bus = n  # both are 1-based
    hour = h  # both are 1-based

    # Determine the parameter name based on technology
    if i == "Solar":
        param_name = "CF_solar"
    elif i == "Wind":
        param_name = "CF_wind"
    else:
        return 0

    # Find the corresponding row in the CSV
    row = df_cluster_centers[
        (df_cluster_centers["parameter"] == param_name)
        & (df_cluster_centers["cluster"] == cluster)
        & (df_cluster_centers["bus"] == bus)
    ]

    if not row.empty:
        return row[f"hour_{hour}"].iloc[0]
    else:
        return 0  # Default value if not found


model.CF_RN = Param(model.N, model.I_gen_RN, model.D, model.H, initialize=init_CF_RN)  # Renewable capacity factors for Solar and Wind from cluster data

print("COMPLETED: setting capacity factor for renewables (CF_RN)")

# ----------------------------------------------------
# Variables
# ----------------------------------------------------
model.p_gen = Var(model.G, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Power generated by each generator (n, i) at day (d) and hour (h). [MW]
model.p_stor_discharge = Var(model.N, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Power discharged by storage at each bus (n), day (d), and hour (h). [MW]
model.p_stor_charge = Var(model.N, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Power charged by storage at each bus (n), day (d), and hour (h). [MW]
model.theta = Var(model.N, model.T, model.D, model.H, domain=Reals, bounds=(-pi, pi))  # Phase angle at each bus (n), day (d), and hour (h) in radians. Bounds: [-pi, pi]
model.p_EOR = Var(model.N_EOR, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Power consumed by chemical manufacturing at buses in EOR counties only [MW]
model.p_DC = Var(model.N_DC, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Power consumed by data centers at buses in DC counties only [MW]
model.curt = Var(model.N, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Power curtailed at at each bus (n), day (d), and hour (h). [MW]
model.curt_gen = Var(model.G, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Power curtailed by generators at at each generator (n, i), day (d), and hour (h). [MW]
model.E_stor_level = Var(model.N, model.T, model.D, model.H, domain=NonNegativeReals, bounds=(0, 1e6))  # Energy level of storage at each bus (n), day (d), and hour (h). [MWh]
model.c_gen = Var(model.G, model.T, domain=NonNegativeReals, bounds=(0, 1e6))  # capacity of each generator (n, i) for planning year t. [MW]
model.c_trans = Var(model.L, model.T, domain=NonNegativeReals, bounds=(0, 1e6))  # capacity of transmission lines (n, n_prime) for planning year t. [MW]
model.c_stor = Var(model.N, model.T, domain=NonNegativeReals, bounds=(0, 1e6))  # capacity of storage at each bus (n) for planning year t. [MW]

print("COMPLETED: defining variables")


# ----------------------------------------------------
# Constraints
# ----------------------------------------------------
# operational constraints
def const_oper_energyBalance_rule(m, n, t, d, h):
    p_gen_sum = sum(m.p_gen[g, t, d, h] for g in m.G if g[0] == n)  # Sum of power by generators at bus n

    curt_gen_sum = sum(m.curt_gen[g, t, d, h] for g in m.G if g[0] == n)  # Sum of power curtailed by generators at bus n

    p_transmission_net_sum = sum(BaseMVA / m.line_x[min(n, n_prime), max(n, n_prime)] * (m.theta[n, t, d, h] - m.theta[n_prime, t, d, h]) for n_prime in bus_connections[n])  # Net power transmitted from bus n (positive = outgoing, negative = incoming)

    # Activate p_EOR and p_DC only for bus n is in the set of C and E, otherwise 0
    p_DC = m.p_DC[n, t, d, h] if n in m.N_DC else 0
    p_EOR = m.p_EOR[n, t, d, h] if n in m.N_EOR else 0

    return (
        p_gen_sum
        - curt_gen_sum
        + m.p_stor_discharge[n, t, d, h]
        - m.p_stor_charge[n, t, d, h]
        - p_transmission_net_sum  # Net transmission outflow (subtract from supply)
        == m.D_base[n, t, d, h] + p_DC + p_EOR - m.curt[n, t, d, h]
    )  # Power balance with undirected transmission lines

model.const_oper_energyBalance = Constraint(model.N, model.T, model.D, model.H, rule=const_oper_energyBalance_rule)


def const_oper_loadBalanceOfDataCenter_rule(m, c, t, d, h):
    return m.D_DC[c, t, d, h] == sum(m.p_DC[n, t, d, h] for n in buses_in_county[c]) # regional load balance for data centers

model.const_oper_loadBalanceOfDataCenter = Constraint(model.C, model.T, model.D, model.H, rule=const_oper_loadBalanceOfDataCenter_rule)


def const_oper_loadBalanceOfChemManu_rule(m, e, t, d, h):
    return m.D_EOR[e, t, d, h] == sum(m.p_EOR[n, t, d, h] for n in buses_in_county[e])  # regional load balance for EOR

model.const_oper_loadBalanceOfChemManu = Constraint(model.E, model.T, model.D, model.H, rule=const_oper_loadBalanceOfChemManu_rule)

def const_oper_genCapacity_peakLoad_rule(m, t):
    """
    Ensure total generation capacity at year t meets peak load at year t
    """
    if t <= min(time_gen_construction_dict.values()):
        return Constraint.Skip
    else:
        return m.P_peak_total[t] <= sum(m.gen_c_gen_init[n, i] for (n, i) in m.G) + sum(m.c_gen[n, i, t_prime] for (n, i) in m.G for t_prime in m.T if t_prime <= t - time_gen_construction_dict[i])


model.const_oper_genCapacity_peakLoad = Constraint(model.T, rule=const_oper_genCapacity_peakLoad_rule)


# Thermal generator capacity constraints with min/max capacity factors
def const_oper_genCapacity_thermal_min_rule(m, n, i, t, d, h):
    # Skip if (n, i) is not a valid generator in G
    if (n, i) not in m.G:
        return Constraint.Skip
    # Skip if i is not a thermal generator
    if i not in m.I_gen_TH:
        return Constraint.Skip
    if t <= m.time_gen_construction[i]:
        return m.p_gen[n, i, t, d, h] >= m.CF_TH_min[i] * m.gen_c_gen_init[n, i]
    else:
        return m.p_gen[n, i, t, d, h] >= m.CF_TH_min[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i]))


model.const_oper_genCapacity_thermal_min = Constraint(model.N, model.I_gen, model.T, model.D, model.H, rule=const_oper_genCapacity_thermal_min_rule)


def const_oper_genCapacity_thermal_max_rule(m, n, i, t, d, h):
    # Skip if (n, i) is not a valid generator in G
    if (n, i) not in m.G:
        return Constraint.Skip
    # Skip if i is not a thermal generator
    if i not in m.I_gen_TH:
        return Constraint.Skip
    if t <= m.time_gen_construction[i]:
        return m.p_gen[n, i, t, d, h] <= m.CF_TH_max[i] * m.gen_c_gen_init[n, i]
    else:
        return m.p_gen[n, i, t, d, h] <= m.CF_TH_max[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i]))
            
model.const_oper_genCapacity_thermal_max = Constraint(model.N, model.I_gen, model.T, model.D, model.H, rule=const_oper_genCapacity_thermal_max_rule)


# Solar and Wind generators follow spatial and temporal capacity factors (inequality constraint)
def const_oper_genCapacity_solarwind_rule(m, n, i, t, d, h):
    # Skip if (n, i) is not a valid generator in G
    if (n, i) not in m.G:
        return Constraint.Skip
    # Skip if i is not Solar or Wind
    if i not in ["Solar", "Wind"]:
        return Constraint.Skip
    if t <= m.time_gen_construction[i]:
        return m.p_gen[n, i, t, d, h] == m.CF_RN[n, i, d, h] * m.gen_c_gen_init[n, i]
    else:
        return m.p_gen[n, i, t, d, h] == m.CF_RN[n, i, d, h] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i]))


model.const_oper_genCapacity_solarwind = Constraint(model.N, model.I_gen, model.T, model.D, model.H, rule=const_oper_genCapacity_solarwind_rule)  # Solar and Wind can generate up to their capacity factor potential (allows curtailment)

# Hydro generators follow fixed capacity factor (inequality constraint)
def const_oper_genCapacity_hydro_rule(m, n, i, t, d, h):
    # Skip if (n, i) is not a valid generator in G
    if (n, i) not in m.G:
        return Constraint.Skip
    # Skip if i is not Hydro
    if i != "Hydro":
        return Constraint.Skip
    if t <= m.time_gen_construction[i]:
        return m.p_gen[n, i, t, d, h] == m.CF_RN_hydro[i] * m.gen_c_gen_init[n, i]
    else:
        return m.p_gen[n, i, t, d, h] == m.CF_RN_hydro[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i]))


model.const_oper_genCapacity_hydro = Constraint(model.N, model.I_gen, model.T, model.D, model.H, rule=const_oper_genCapacity_hydro_rule)  # Hydro can generate up to its capacity factor potential (allows curtailment)



def const_oper_genRampingUp_rule(m, n, i, t, d, h):
    # Skip if (n, i) is not a valid generator in G
    if (n, i) not in m.G:
        return Constraint.Skip
    # Skip if i is not a thermal generator
    if i not in m.I_gen_TH:
        return Constraint.Skip

    if (t == 1) and (d == 1) and (h == 1):
        return Constraint.Skip
    elif (d == 1) and (h == 1):
        if t <= m.time_gen_construction[i]:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t - 1, m.D.last(), m.H.last()]) / unit_hour <= m.gen_r_ramp[i] * m.gen_c_gen_init[n, i] * 60
        else:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t - 1, m.D.last(), m.H.last()]) / unit_hour <= m.gen_r_ramp[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i])) * 60

    elif h == 1:
        if t <= m.time_gen_construction[i]:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d - 1, m.H.last()]) / unit_hour <= m.gen_r_ramp[i] * m.gen_c_gen_init[n, i] * 60
        else:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d - 1, m.H.last()]) / unit_hour <= m.gen_r_ramp[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i])) * 60

    else:
        if t <= m.time_gen_construction[i]:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d, h - 1]) / unit_hour <= m.gen_r_ramp[i] * m.gen_c_gen_init[n, i] * 60
        else:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d, h - 1]) / unit_hour <= m.gen_r_ramp[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i])) * 60  # [1/min] * [MW] * [min/hour] = [MW/hour]  # ramping constraints for generators


model.const_oper_genRampingUp = Constraint(model.N, model.I_gen, model.T, model.D, model.H, rule=const_oper_genRampingUp_rule) # Filtered to only valid G combinations and thermal generators


def const_oper_genRampingDown_rule(m, n, i, t, d, h):
    # Skip if (n, i) is not a valid generator in G
    if (n, i) not in m.G:
        return Constraint.Skip
    # Skip if i is not a thermal generator
    if i not in m.I_gen_TH:
        return Constraint.Skip
    if (t == 1) and (d == 1) and (h == 1):
        return Constraint.Skip
    elif (d == 1) and (h == 1):
        if t <= m.time_gen_construction[i]:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t - 1, m.D.last(), m.H.last()]) / unit_hour >= -m.gen_r_ramp[i] * m.gen_c_gen_init[n, i] * 60
        else:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t - 1, m.D.last(), m.H.last()]) / unit_hour >= -m.gen_r_ramp[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i])) * 60
    elif h == 1:
        if t <= m.time_gen_construction[i]:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d - 1, m.H.last()]) / unit_hour >= -m.gen_r_ramp[i] * m.gen_c_gen_init[n, i] * 60
        else:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d - 1, m.H.last()]) / unit_hour >= -m.gen_r_ramp[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i])) * 60
    else:
        if t <= m.time_gen_construction[i]:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d, h - 1]) / unit_hour >= -m.gen_r_ramp[i] * m.gen_c_gen_init[n, i] * 60
        else:
            return (m.p_gen[n, i, t, d, h] - m.p_gen[n, i, t, d, h - 1]) / unit_hour >= -m.gen_r_ramp[i] * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i])) * 60


model.const_oper_genRampingDown = Constraint(model.N, model.I_gen, model.T, model.D, model.H, rule=const_oper_genRampingDown_rule)


# transmission constraints - for all connected bus pairs (n, n')
def const_oper_transCapacityUpper_rule(m, n, n_prime, t, d, h):
    # Skip if buses are not connected
    if n_prime not in bus_connections[n]:
        return Constraint.Skip

    # Power flow between bus n and n_prime
    line_pair = (min(n, n_prime), max(n, n_prime),)  # Get undirected line pair for parameters
    power_flow = (BaseMVA / m.line_x[line_pair] * (m.theta[n, t, d, h] - m.theta[n_prime, t, d, h]))

    if t <= m.time_trans_construction:
        return power_flow <= m.line_c_trans_init[line_pair]
    else:
        return power_flow <= m.line_c_trans_init[line_pair] + sum(m.c_trans[line_pair, t_prime] for t_prime in m.T if t_prime <= t - m.time_trans_construction)


model.const_oper_transCapacityUpper = Constraint(model.N, model.N, model.T, model.D, model.H, rule=const_oper_transCapacityUpper_rule)


def const_oper_transCapacityLower_rule(m, n, n_prime, t, d, h):
    # Skip if buses are not connected
    if n_prime not in bus_connections[n]:
        return Constraint.Skip

    # Power flow between bus n and n_prime
    line_pair = (min(n, n_prime), max(n, n_prime),)  # Get undirected line pair for parameters
    power_flow = (BaseMVA / m.line_x[line_pair] * (m.theta[n, t, d, h] - m.theta[n_prime, t, d, h]))

    if t <= m.time_trans_construction:
        return power_flow >= -m.line_c_trans_init[line_pair]
    else:
        return power_flow >= -(m.line_c_trans_init[line_pair] + sum(m.c_trans[line_pair, t_prime] for t_prime in m.T if t_prime <= t - m.time_trans_construction))


model.const_oper_transCapacityLower = Constraint(model.N, model.N, model.T, model.D, model.H, rule=const_oper_transCapacityLower_rule)


# storage constraints
def const_stor_storageLevel_rule(m, n, t, d, h):
    if (t == 1) and (d == 1) and (h == 1):  # initial level should be designated
        return (m.E_stor_level[n, t, d, h] == m.E_stor_level_init[n] + m.eta_charge * m.p_stor_charge[n, t, d, h] * unit_hour - 1 / (m.eta_discharge) * m.p_stor_discharge[n, t, d, h] * unit_hour)
    elif (d == 1) and (h == 1):
        # first hour of the day (roll over from the last hour of the previous day)
        return (m.E_stor_level[n, t, d, h] == m.E_stor_level[n, t - 1, m.D.last(), m.H.last()])
    elif h == 1:
        return m.E_stor_level[n, t, d, h] == m.E_stor_level[n, t, d - 1, m.H.last()]
    else:
        return (m.E_stor_level[n, t, d, h] == m.E_stor_level[n, t, d, h - 1] + m.eta_charge * m.p_stor_charge[n, t, d, h] * unit_hour - 1 / (m.eta_discharge) * m.p_stor_discharge[n, t, d, h] * unit_hour)
  # Note: The unit of the storage level is [MWh]


model.const_stor_storageLevel = Constraint(model.N, model.T, model.D, model.H, rule=const_stor_storageLevel_rule)


def const_stor_max_storageLevel_rule(m, n, t, d, h):
    if t <= m.time_stor_construction:
        return m.E_stor_level[n, t, d, h] <= m.c_stor_init[n] * m.hr_stor_max
    else:
        return (m.E_stor_level[n, t, d, h] <= (m.c_stor_init[n] + sum(m.c_stor[n, t_prime] for t_prime in m.T if t_prime <= t - m.time_stor_construction)) * m.hr_stor_max)


model.const_stor_max_storageLevel = Constraint(model.N, model.T, model.D, model.H, rule=const_stor_max_storageLevel_rule)


def const_stor_chargeCapacity_rule(m, n, t, d, h):
    if t <= m.time_stor_construction:
        return m.p_stor_charge[n, t, d, h] <= m.c_stor_init[n]
    else:
        return m.p_stor_charge[n, t, d, h] <= (m.c_stor_init[n] + sum(m.c_stor[n, t_prime] for t_prime in m.T if t_prime <= t - m.time_stor_construction))


model.const_stor_chargeCapacity = Constraint(model.N, model.T, model.D, model.H, rule=const_stor_chargeCapacity_rule)


def const_stor_dischargeCapacity_rule(m, n, t, d, h):
    if t <= m.time_stor_construction:
        return m.p_stor_discharge[n, t, d, h] <= m.c_stor_init[n]
    else:
        return m.p_stor_discharge[n, t, d, h] <= (m.c_stor_init[n] + sum(m.c_stor[n, t_prime] for t_prime in m.T if t_prime <= t - m.time_stor_construction))


model.const_stor_dischargeCapacity = Constraint(model.N, model.T, model.D, model.H, rule=const_stor_dischargeCapacity_rule)


# investment constraints


# No nuclear investments until after 2029
def const_invest_no_nuclear_rule(m, n, i, t):
    """
    Prevent nuclear investments until 2029
    For current year <= 2029, c_gen[n,i,t] = 0 for i = Nuclear
    """

    # Skip if i is not Nuclear
    if i == "Nuclear":
        if m.time_currentYear[t] <= 2029:
            return m.c_gen[n, i, t] == 0
        else:
            return Constraint.Skip
    else:
        return Constraint.Skip


model.const_invest_nuclear_moratorium = Constraint(model.G, model.T, rule=const_invest_no_nuclear_rule)


def const_invest_genCapacity_rule(m, n, i, t):
    return (m.c_gen[n, i, t] <= m.c_gen_max[n, i])
    # Maximum capacity for each generator type at each bus


model.const_invest_genCapacity = Constraint(model.G, model.T, rule=const_invest_genCapacity_rule)


def const_invest_transCapacity_rule(m, n, n_prime, t):
    return (m.c_trans[n, n_prime, t] <= m.c_trans_max[n, n_prime])
    # Maximum capacity for each transmission line between buses


model.const_invest_transCapacity = Constraint(model.L, model.T, rule=const_invest_transCapacity_rule)


def const_invest_storCapacity_rule(m, n, t):
    return (m.c_stor[n, t] <= m.c_stor_max[n])
    # Maximum capacity for each storage at each bus


model.const_invest_storCapacity = Constraint(model.N, model.T, rule=const_invest_storCapacity_rule)

# lower value bound for investment variables are determined by the domain of the variables, which is NonNegativeReals.
# model.const_invest_storCapacity.pprint()

print("COMPLETED: defining constraints")


# ----------------------------------------------------
# Objective Function
# ----------------------------------------------------


def obj_rule(m):

    # Multi-year objective function with proper discounting
    total_cost = 0

    for t in m.T:
        current_year = m.time_currentYear[t]
        discount_factor = DF(Ir, current_year, time_financialBaseYear)

        # CAPEX for year t (only for new investments in that year)
        capex_gen_t = sum(m.alpha_CAPEX_gen[i, t] * 1e3 * m.c_gen[n, i, t] for (n, i) in m.G)  # [$] = [$/kW] * 1e+3 [kW/MW] * [MW]

        capex_trans_t = sum(m.alpha_CAPEX_trans * (m.line_mile[n, n_prime] * 1e3 * m.c_trans[n, n_prime, t]) for (n, n_prime) in m.L)  # [$] = [$/kW*mile] * [mile] * 1e+3 [kW/MW] * [MW]

        capex_stor_t = sum(m.alpha_CAPEX_stor[t] * 1e3 * m.c_stor[n, t] for n in m.N)  # [$] = [$/kW] * 1e+3 [kW/MW] * [MW]

        # Total CAPEX for year t

        capex_t = (capex_gen_t + DF(Ir, current_year, time_financialBaseYear) * capex_trans_t + capex_stor_t)  # [$]. Note: capex_gen and capex_trans params are already discounted from the parameters from ATB. Transmission should be discounted separately.

        # OPEX for year t (operational costs)
        opex_gen_variable_t = sum(
            m.weight_repDays[d]
            * unit_hour
            * sum(
                (m.VOM_gen[i, t] + m.COST_fuel[i, t] * m.HeatRate[i, t])
                * m.p_gen[n, i, t, d, h]
                for (n, i) in m.G
            )
            for d in m.D
            for h in m.H
        )  # [$] = [hr] * ([$/MWh] + [$/MMBtu] * [MMBtu/MWh]) * [MW]
        
        opex_gen_fixed_t = sum(
            m.FOM_gen[i, t] * 1e3 * m.gen_c_gen_init[n, i] * unit_year
            if t <= m.time_gen_construction[i]
            else
            m.FOM_gen[i, t] * 1e3 * (m.gen_c_gen_init[n, i] + sum(m.c_gen[n, i, t_prime] for t_prime in m.T if t_prime <= t - m.time_gen_construction[i])) * unit_year
            for (n, i) in m.G
        )  # [$] = [$/kW-yr] * 1e+3 [kW/MW] * [MW] * [yr]
        
        opex_trans_t = 0  # Currently not considered
        
        opex_stor_t = sum(
            m.FOM_stor[t] * 1e3 * m.c_stor_init[n] * unit_year
            if t <= m.time_stor_construction
            else
            m.FOM_stor[t] * 1e3 * (m.c_stor_init[n] + sum(m.c_stor[n, t_prime] for t_prime in m.T if t_prime <= t - m.time_stor_construction)) * unit_year
            for n in m.N
        )
        
        # Curtailment cost for year t
        cost_curt_gen_t = sum(
            m.alpha_curt_gen * m.curt_gen[g, t, d, h] * unit_hour * m.weight_repDays[d]
            for g in m.G
            for d in m.D
            for h in m.H
        )

        cost_curt_t = sum(
            m.alpha_curt * m.curt[n, t, d, h] * unit_hour * m.weight_repDays[d]
            for n in m.N
            for d in m.D
            for h in m.H
        )

        # Total cost for year t
        total_opex_t = opex_gen_variable_t + opex_gen_fixed_t + opex_trans_t + opex_stor_t
        annual_cost_t = capex_t + total_opex_t + cost_curt_gen_t + cost_curt_t

        # Add discounted cost to total
        total_cost += annual_cost_t

    return total_cost / 1e5  # scaling factor to reduce solution time


model.Objective = Objective(rule=obj_rule, sense=minimize)
# model.Objective.pprint()
print("COMPLETED: defining objective function")


# print(model.nvariables())
# print(model.nconstraints())
# model.pprint()

# ----------------------------------------------------
# MODEL BUILDING COMPLETION AND TIMING
# ----------------------------------------------------
model_build_end_time = time.time()
model_build_duration = model_build_end_time - model_build_start_time

print("\n" + "=" * 60)
print("MODEL BUILDING COMPLETED")
print("=" * 60)
print(f" Model Build Time: {model_build_duration:.2f} seconds ({model_build_duration/60:.2f} minutes)")
print("=" * 60 + "\n")

# ----------------------------------------------------
# Solver Configuration and Execution
# ----------------------------------------------------

print("\n" + "=" * 60)
print("SOLVING OPTIMIZATION MODEL")
print("=" * 60)

print(f"Variables: {model.nvariables():,}, Constraints: {model.nconstraints():,}")
print("\n" + "=" * 60)
print("OPTIMIZATION SCENARIO SUMMARY")
print("=" * 60)
print(f"Time Horizon: {len(model.T)} years")
print(f"Planning start year: {time_planningStartYear}")
print(f"Planning end year: {time_planningStartYear + len(model.T) - 1}")
print(f"Discount Rate (Ir): {Ir}")
print(f"Number of Representative Days: {len(model.D)}")
print(f"Number of Buses: {len(model.N)}")
print(f"Number of Buses with Data Centers: {len(model.N_DC)}")
print(f"Number of Buses with EOR facilities: {len(model.N_EOR)}")
print(f"Number of Generation Technologies: {len(model.I_gen)}")
print(f"Number of Storage Buses: {len(model.N)}")
print(f"Number of Transmission Lines: {len(model.L)}")
print("=" * 60 + "\n")

# Create Gurobi solver
try:
    import time

    solver = SolverFactory("gurobi")
    if not solver.available():
        raise Exception("Gurobi solver not available. Please install Gurobi.")

    print("Using Gurobi solver")

    # solver.options["threads"] = 0  # Use all available threads
    # solver.options["Method"] = 1  # 0: primal simplex, 1: dual simplex, 2: barrier
    # solver.options["NumericFocus"] = 3  # 0: balance, 1: feasibility, 2: optimality, 3: robustness)

    # Solve the model with timing
    print("Starting optimization...")
    start_time = time.time()
    results = solver.solve(model, tee=True)  # Set tee=True to see solver output
    end_time = time.time()

    # Calculate runtime
    runtime_seconds = end_time - start_time
    runtime_minutes = runtime_seconds / 60

    # Check results
    from pyomo.opt import SolverStatus, TerminationCondition

    if (results.solver.status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal):

        print("\nOPTIMAL SOLUTION FOUND")
        objective_value = model.Objective()
        print(f"Optimal Objective Value (Millions): ${objective_value:,.0f}")
        print(f"Solver Runtime: {runtime_seconds:.2f} seconds ({runtime_minutes:.2f} minutes)")
        print("Solution saved in model object")

    elif results.solver.termination_condition == TerminationCondition.infeasible:
        print("\nMODEL IS INFEASIBLE")
        print(f"Runtime: {runtime_seconds:.2f} seconds")

    elif results.solver.termination_condition == TerminationCondition.unbounded:
        print("\nMODEL IS UNBOUNDED")
        print(f"Runtime: {runtime_seconds:.2f} seconds")

    else:
        print(f"\nSOLVER STATUS: {results.solver.termination_condition}")
        print(f"\nRuntime: {runtime_seconds:.2f} seconds")

except Exception as e:
    print(f"\nERROR: {e}")
    # Try to report runtime even if there was an error
    try:
        if "start_time" in locals():
            error_runtime = time.time() - start_time
            print(f"Runtime before error: {error_runtime:.2f} seconds")
    except:
        pass

print("\n" + "=" * 60)
print("OPTIMIZATION COMPLETE")
print("=" * 60)

import pickle

# Save the entire model object (including results) to a .pkl file
results_dir = os.path.join(script_dir, "results")

from datetime import datetime

os.makedirs(results_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_pkl_path = os.path.join(results_dir, f"Case2_model_results_{timestamp}_1e5scaled.pkl")

try:
    with open(model_pkl_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Model and results saved to {model_pkl_path}")
except Exception as e:
    print(f"Failed to save model results to pickle: {e}")