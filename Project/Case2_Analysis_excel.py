# ----------------------------------------------------
# Case 2 Results Analysis - Multi-Year Analysis from PKL File
# ----------------------------------------------------

import pickle
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add the current directory to Python path to import Case2_LP_multi-periods
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Add constraint rule functions as placeholders (they're not needed for analysis, just for pickle loading)
def const_oper_energyBalance_rule(*args, **kwargs):
    return None


def const_oper_loadBalanceOfDataCenter_rule(*args, **kwargs):
    return None


def const_oper_loadBalanceOfChemManu_rule(*args, **kwargs):
    return None

def const_oper_flexibleDataCenterLoad_rule(*args, **kwargs):
    return None

def const_oper_flexibleElectrifiedManufacturigLoad_rule(*args, **kwargs):
    return None

def cost_oper_annualElectrificationTarget_rule(*args, **kwargs):
    return None

def const_oper_genCapacity_thermal_min_rule(*args, **kwargs):
    return None


def const_oper_genCapacity_thermal_max_rule(*args, **kwargs):
    return None


def const_oper_genCapacity_solarwind_rule(*args, **kwargs):
    return None


def const_oper_genCapacity_hydro_rule(*args, **kwargs):
    return None


def const_oper_genCapacity_peakLoad_rule(*args, **kwargs):
    return None


def const_oper_genRampingUp_rule(*args, **kwargs):
    return None


def const_oper_genRampingDown_rule(*args, **kwargs):
    return None


def const_oper_transCapacityUpper_rule(*args, **kwargs):
    return None


def const_oper_transCapacityLower_rule(*args, **kwargs):
    return None


def const_stor_storageLevel_rule(*args, **kwargs):
    return None


def const_stor_max_storageLevel_rule(*args, **kwargs):
    return None


def const_stor_chargeCapacity_rule(*args, **kwargs):
    return None


def const_stor_dischargeCapacity_rule(*args, **kwargs):
    return None


def const_invest_no_nuclear_rule(*args, **kwargs):
    return None


def const_invest_genCapacity_rule(*args, **kwargs):
    return None


def const_invest_transCapacity_rule(*args, **kwargs):
    return None


def const_invest_storCapacity_rule(*args, **kwargs):
    return None


def obj_rule(*args, **kwargs):
    return None


print("Added placeholder constraint functions for pickle loading")


# Add necessary function definitions that were used in the original model
def time_currentYear_init(model, t):
    """Function needed for pickle loading - matches the one in Case2_LP_multi-periods.py"""
    time_planningStartYear = 2022  # From the original script
    return time_planningStartYear + t - 1


def init_E_base(model, t):
    """Function needed for pickle loading"""
    # This will be loaded from the model data, so we can return a placeholder
    return 0


def init_E_DC(model, t):
    """Function needed for pickle loading"""
    return 0


def init_E_EOR(model, t):
    """Function needed for pickle loading"""
    return 0


def init_E_total(model, t):
    """Function needed for pickle loading"""
    return 0


def init_P_peak_base(model, t):
    """Function needed for pickle loading"""
    return 0

def init_Q_OR(model, e):
    """Function needed for pickle loading"""
    return 0

def init_P_peak_DC(model, t):
    """Function needed for pickle loading"""
    return 0


def init_P_peak_EOR(model, t):
    """Function needed for pickle loading"""
    return 0


def init_P_peak_total(model, t):
    """Function needed for pickle loading"""
    return 0


def init_phi_DC(model, c):
    """Function needed for pickle loading"""
    return 0


def init_phi_EOR(model, e):
    """Function needed for pickle loading"""
    return 0


def init_D_base(model, n, t, d, h):
    """Function needed for pickle loading"""
    return 0


def init_D_DC(model, c, t, d, h):
    """Function needed for pickle loading"""
    return 0


def init_D_EOR(model, e, t, d, h):
    """Function needed for pickle loading"""
    return 0


def init_CF_RN(model, n, i, d, h):
    """Function needed for pickle loading"""
    return 0


# Additional helper functions that might be needed
def create_undirected_line_pairs(df_line):
    """Function needed for pickle loading"""
    return [], {}


def calculate_line_parameters(valid_line_pairs, line_connection_data):
    """Function needed for pickle loading"""
    return {}, {}, {}, {}, {}


def calculate_transmission_efficiency(valid_line_pairs, line_mile_dict):
    """Function needed for pickle loading"""
    return {}


def get_atb_value(display_name, core_metric_parameter, year):
    """Function needed for pickle loading"""
    return 0


def get_aeo_fuel_cost(fuel_name, year):
    """Function needed for pickle loading"""
    return 0


def DF(Ir, currentYear, baseYear):
    """Function needed for pickle loading"""
    return 1 / (1 + Ir) ** (currentYear - baseYear)


def load_model_from_pkl():
    """
    Load the Case2 model results from PKL file
    """
    # Directory where PKL files are saved (Windows path from the LP script)
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results") # If this path does not work, you can hard code the absolute path here.
    os.makedirs(results_dir, exist_ok=True)
    pkl_dir = results_dir

    # Directly open the assigned name of the file
    assigned_pkl_filename = "Case2_model_results_baseCase_2025-2031_1e5scaled.pkl"
    pkl_path = os.path.join(pkl_dir, assigned_pkl_filename)

    if not os.path.exists(pkl_path):
        print("Assigned PKL file not found in the directory")
        return None

    print(f"Loading model from: {assigned_pkl_filename}")

    try:
        with open(pkl_path, "rb") as f:
            model = pickle.load(f)
        print("Model loaded successfully")
        return model
    except AttributeError as e:
        print(f"AttributeError loading PKL file: {e}")
        print(
            "This usually means a function used in the model is not defined in this script."
        )
        print("Adding the missing function as a placeholder...")

        # Extract the function name from the error message
        if "Can't get attribute" in str(e):
            import re

            match = re.search(r"Can't get attribute '(\w+)'", str(e))
            if match:
                func_name = match.group(1)
                print(f"Missing function: {func_name}")
                # Add the missing function to globals
                globals()[func_name] = lambda *args, **kwargs: 0

                # Try loading again
                try:
                    with open(pkl_path, "rb") as f:
                        model = pickle.load(f)
                    print(
                        "Model loaded successfully after adding placeholder function"
                    )
                    return model
                except Exception as e2:
                    print(f"Still failed after adding placeholder: {e2}")
                    return None
        return None
    except Exception as e:
        print(f"Error loading PKL file: {e}")
        return None


def analyze_case2_results():
    """
    Comprehensive Case 2 results analysis with multi-year focus
    Creates Excel file with 6 tabs as specified
    """

    # Load model from PKL file
    model = load_model_from_pkl()
    if model is None:
        return

    print("\n" + "=" * 80)
    print("CASE 2 MULTI-YEAR RESULTS ANALYSIS")
    print("=" * 80)

    # Check if model was solved successfully
    try:
        first_gen = list(model.G)[0]
        if model.c_gen[first_gen, 1].value is None:
            print("Model was not solved successfully or is infeasible")
            return
    except:
        print("Error accessing model results")
        return

    # Create results directory (fixed path, same as model output)
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)

    # Generate timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = os.path.join(results_dir, f"Case2_Analysis_{timestamp}.xlsx")

    # Pre-compute bus connections for efficient transmission calculations
    bus_connections = {}
    for n in model.N:
        bus_connections[n] = []

    for n_min, n_max in model.L:
        bus_connections[n_min].append(n_max)
        bus_connections[n_max].append(n_min)

    # Get base MVA from model
    BaseMVA = 100  # This should match the value in the LP model

    print("Analyzing multi-year results...")

    with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:

        # ====================================================================
        # 1. SUMMARY TAB
        # ====================================================================
        print("Creating Summary tab...")

        summary_data = []

        # Optimization scenarios
        planning_years = list(model.T)
        calendar_years = [model.time_currentYear[t] for t in planning_years]

        summary_data.append(["Optimization Scenarios", ""])
        summary_data.append(["Time Horizon (years)", len(planning_years)])
        summary_data.append(
            ["Planning Start Year", calendar_years[0] if calendar_years else "N/A"]
        )
        summary_data.append(
            ["Planning End Year", calendar_years[-1] if calendar_years else "N/A"]
        )
        summary_data.append(["Discount Rate", 0.044])  # From LP script
        summary_data.append(["Number of Representative Days", len(model.D)])
        summary_data.append(["Number of Buses", len(model.N)])
        summary_data.append(["Number of Buses with Data Centers", len(model.N_DC)])
        summary_data.append(["Number of Buses with EOR", len(model.N_EOR)])
        summary_data.append(["Number of Generation Technologies", len(model.I_gen)])
        summary_data.append(["Number of Storage Buses", len(model.N)])
        summary_data.append(["Number of Transmission Lines", len(model.L)])

        # Construction times
        summary_data.append(["", ""])
        summary_data.append(["Construction Times", ""])
        for tech in model.I_gen:
            summary_data.append(
                [f"Generator {tech} (years)", model.time_gen_construction[tech]]
            )
        summary_data.append(
            ["Transmission (years)", model.time_trans_construction.value]
        )
        summary_data.append(["Storage (years)", model.time_stor_construction.value])

        # Total objective function
        summary_data.append(["", ""])
        summary_data.append(["Financial Results", ""])
        objective_value = model.Objective()
        summary_data.append(
            ["Total Objective Function Value (scaled)", objective_value]
        )

        # Initial capacities
        summary_data.append(["", ""])
        summary_data.append(["Initial Capacities", ""])

        # Initial generation capacity by technology
        initial_gen_capacity = {}
        for tech in model.I_gen:
            capacity = sum(model.gen_c_gen_init[n, i] for n, i in model.G if i == tech)
            initial_gen_capacity[tech] = capacity
            summary_data.append([f"Initial Gen Capacity {tech} (MW)", capacity])

        # Initial transmission capacity
        initial_trans_capacity = sum(
            model.line_c_trans_init[n, n_prime] for n, n_prime in model.L
        )
        summary_data.append(["Initial Trans Capacity (MW)", initial_trans_capacity])

        # Initial storage capacity (should be 0)
        initial_stor_capacity = sum(model.c_stor_init[n] for n in model.N)
        summary_data.append(["Initial Storage Capacity (MW)", initial_stor_capacity])

        # Final year capacities
        final_year_t = max(planning_years)
        summary_data.append(["", ""])
        summary_data.append(["Final Year Capacities", ""])

        # Final generation capacity by technology
        for tech in model.I_gen:
            final_capacity = sum(
                model.gen_c_gen_init[n, i]
                + sum(
                    model.c_gen[n, i, t].value or 0
                    for t in planning_years
                    if t <= final_year_t - model.time_gen_construction[i]
                )
                for n, i in model.G
                if i == tech
            )
            summary_data.append([f"Final Gen Capacity {tech} (MW)", final_capacity])

        # Final transmission capacity
        final_trans_capacity = sum(
            model.line_c_trans_init[n, n_prime]
            + sum(
                model.c_trans[n, n_prime, t].value or 0
                for t in planning_years
                if t <= final_year_t - model.time_trans_construction
            )
            for n, n_prime in model.L
        )
        summary_data.append(["Final Trans Capacity (MW)", final_trans_capacity])

        # Final storage capacity
        final_stor_capacity = sum(
            model.c_stor_init[n]
            + sum(
                model.c_stor[n, t].value or 0
                for t in planning_years
                if t <= final_year_t - model.time_stor_construction
            )
            for n in model.N
        )
        summary_data.append(["Final Storage Capacity (MW)", final_stor_capacity])

        # Create Summary DataFrame for basic info
        summary_df = pd.DataFrame(summary_data, columns=["Metric", "Value"])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # ====================================================================
        # MULTI-YEAR METRICS TABLE (separate sheet)
        # ====================================================================
        print("Creating Multi-Year Metrics table...")

        # Prepare multi-year data
        multiyear_data = []

        # Financial parameters from the model
        Ir = 0.044  # Discount rate from LP script
        time_financialBaseYear = 2022  # From LP script

        def DF(Ir, currentYear, baseYear):
            """Calculate discount factor"""
            return 1 / (1 + Ir) ** (currentYear - baseYear)

        for t in planning_years:
            calendar_year = model.time_currentYear[t]

            # Calculate annual generation and curtailment
            total_annual_generation = 0
            total_annual_curtailment_gen = 0
            total_annual_curtailment = 0

            for d in model.D:
                weight = model.weight_repDays[d]
                for h in model.H:
                    # Generation
                    for n, i in model.G:
                        gen_val = model.p_gen[n, i, t, d, h].value or 0
                        total_annual_generation += gen_val * weight

                        curt_gen_val = model.curt_gen[n, i, t, d, h].value or 0
                        total_annual_curtailment_gen += curt_gen_val * weight

                    # Curtailment
                    for n in model.N:
                        curt_val = model.curt[n, t, d, h].value or 0
                        total_annual_curtailment += curt_val * weight

            # Calculate total demand for curtailment rate
            total_demand = 0
            for d in model.D:
                weight = model.weight_repDays[d]
                for h in model.H:
                    for n in model.N:
                        demand = model.D_base[n, t, d, h]
                        total_demand += demand * weight

                        # Add DC and EOR loads if applicable
                        if n in model.N_DC:
                            total_demand += (model.p_DC[n, t, d, h].value or 0) * weight
                        if n in model.N_EOR:
                            total_demand += (
                                model.p_EOR[n, t, d, h].value or 0
                            ) * weight

            # Curtailment rates
            curtailment_gen_rate = (
                (total_annual_curtailment_gen / total_annual_generation * 100)
                if total_annual_generation > 0
                else 0
            )
            curtailment_rate = (
                (total_annual_curtailment / total_demand * 100)
                if total_demand > 0
                else 0
            )

            # Investment counts and capacities for this year
            total_new_gen_capacity = sum(
                model.c_gen[n, i, t].value or 0 for n, i in model.G
            )
            total_new_trans_capacity = sum(
                model.c_trans[n, n_prime, t].value or 0 for n, n_prime in model.L
            )
            total_new_stor_capacity = sum(
                model.c_stor[n, t].value or 0 for n in model.N
            )

            num_invested_gen = sum(
                1 for n, i in model.G if (model.c_gen[n, i, t].value or 0) > 1e-6
            )
            num_invested_trans = sum(
                1
                for n, n_prime in model.L
                if (model.c_trans[n, n_prime, t].value or 0) > 1e-6
            )
            num_invested_storage = sum(
                1 for n in model.N if (model.c_stor[n, t].value or 0) > 1e-6
            )

            # Calculate detailed costs for this year (following obj_rule from LP script)
            current_year = model.time_currentYear[t]
            discount_factor = DF(Ir, current_year, time_financialBaseYear)

            # CAPEX for year t
            capex_gen_t = sum(
                model.alpha_CAPEX_gen[i, t] * 1e3 * (model.c_gen[n, i, t].value or 0)
                for (n, i) in model.G
            )

            # CAPEX breakdown by generator technologies
            capex_gen_by_tech = {}
            for tech in model.I_gen:
                capex_gen_by_tech[tech] = sum(
                    model.alpha_CAPEX_gen[i, t] * 1e3 * (model.c_gen[n, i, t].value or 0)
                    for (n, i) in model.G if i == tech
                )

            capex_trans_t = sum(
                model.alpha_CAPEX_trans.value
                * (
                    model.line_mile[n, n_prime]
                    * 1e3
                    * (model.c_trans[n, n_prime, t].value or 0)
                )
                for (n, n_prime) in model.L
            )

            capex_stor_t = sum(
                model.alpha_CAPEX_stor[t] * 1e3 * (model.c_stor[n, t].value or 0)
                for n in model.N
            )

            # CAPEX subgroups
            capex_trans_discounted_t = discount_factor * capex_trans_t
            capex_t = capex_gen_t + capex_trans_discounted_t + capex_stor_t

            # OPEX for year t
            opex_gen_variable_t = sum(
                model.weight_repDays[d]
                * sum(
                    (model.VOM_gen[i, t] + model.COST_fuel[i, t] * model.HeatRate[i, t])
                    * (model.p_gen[n, i, t, d, h].value or 0)
                    for (n, i) in model.G
                )
                for d in model.D
                for h in model.H
            )

            # OPEX variable breakdown by generator technologies
            opex_gen_variable_by_tech = {}
            for tech in model.I_gen:
                opex_gen_variable_by_tech[tech] = sum(
                    model.weight_repDays[d]
                    * sum(
                        (model.VOM_gen[i, t] + model.COST_fuel[i, t] * model.HeatRate[i, t])
                        * (model.p_gen[n, i, t, d, h].value or 0)
                        for (n, i) in model.G if i == tech
                    )
                    for d in model.D
                    for h in model.H
                )

            opex_gen_fixed_t = sum(
                model.FOM_gen[i, t]
                * 1e3
                * (model.gen_c_gen_init[n, i] + (model.c_gen[n, i, t].value or 0))
                for (n, i) in model.G
            )

            # OPEX fixed breakdown by generator technologies
            opex_gen_fixed_by_tech = {}
            for tech in model.I_gen:
                opex_gen_fixed_by_tech[tech] = sum(
                    model.FOM_gen[i, t]
                    * 1e3
                    * (model.gen_c_gen_init[n, i] + (model.c_gen[n, i, t].value or 0))
                    for (n, i) in model.G if i == tech
                )

            opex_stor_t = sum(
                model.FOM_stor[t]
                * 1e3
                * (model.c_stor_init[n] + (model.c_stor[n, t].value or 0))
                for n in model.N
            )

            # OPEX subgroups
            opex_gen_t = opex_gen_variable_t + opex_gen_fixed_t
            total_opex_t = opex_gen_t + opex_stor_t

            # Curtailment costs for year t
            cost_curt_gen_t = sum(
                model.alpha_curt_gen.value
                * (model.curt_gen[g, t, d, h].value or 0)
                * model.weight_repDays[d]
                for g in model.G
                for d in model.D
                for h in model.H
            )

            cost_curt_t = sum(
                model.alpha_curt.value
                * (model.curt[n, t, d, h].value or 0)
                * model.weight_repDays[d]
                for n in model.N
                for d in model.D
                for h in model.H
            )

            annual_cost_t = capex_t + total_opex_t + cost_curt_gen_t + cost_curt_t

            # Calculate new generation capacity breakdown by fuel type for year t
            new_gen_capacity_by_fuel = {}
            for tech in model.I_gen:
                new_gen_capacity_by_fuel[f"New_Gen_Capacity_{tech}_MW"] = sum(
                    model.c_gen[n, i, t].value or 0 for n, i in model.G if i == tech
                )

            # Calculate total generation capacity by fuel type at year t (existing + new from all previous years)
            total_gen_capacity_by_fuel = {}
            for tech in model.I_gen:
                total_capacity = sum(
                    model.gen_c_gen_init[n, i]
                    + sum(
                        model.c_gen[n, i, t_prev].value or 0
                        for t_prev in planning_years
                        if t_prev <= t and t_prev <= t - model.time_gen_construction[i]
                    )
                    for n, i in model.G
                    if i == tech
                )
                total_gen_capacity_by_fuel[f"Total_Gen_Capacity_{tech}_MW"] = (
                    total_capacity
                )

            # Calculate total transmission capacity at year t (existing + new from all previous years)
            total_trans_capacity_at_t = sum(
                model.line_c_trans_init[n, n_prime]
                + sum(
                    model.c_trans[n, n_prime, t_prev].value or 0
                    for t_prev in planning_years
                    if t_prev <= t and t_prev <= t - model.time_trans_construction
                )
                for n, n_prime in model.L
            )

            # Calculate total storage capacity at year t (existing + new from all previous years)
            total_stor_capacity_at_t = sum(
                model.c_stor_init[n]
                + sum(
                    model.c_stor[n, t_prev].value or 0
                    for t_prev in planning_years
                    if t_prev <= t and t_prev <= t - model.time_stor_construction
                )
                for n in model.N
            )

            # Calculate annual capacity factor by fuel type for year t
            capacity_factor_by_fuel = {}
            for tech in model.I_gen:
                # Get total installed capacity for this technology at year t
                installed_capacity = total_gen_capacity_by_fuel[
                    f"Total_Gen_Capacity_{tech}_MW"
                ]

                if installed_capacity > 1e-6:  # Avoid division by zero
                    # Calculate annual generation for this technology
                    annual_generation_tech = 0
                    for d in model.D:
                        weight = model.weight_repDays[d]
                        for h in model.H:
                            for n, i in model.G:
                                if i == tech:
                                    gen_val = model.p_gen[n, i, t, d, h].value or 0
                                    annual_generation_tech += gen_val * weight

                    # Capacity factor = Annual Generation / (Installed Capacity * 8760 hours)
                    capacity_factor = (
                        annual_generation_tech / (installed_capacity * 8760) * 100
                    )
                    capacity_factor_by_fuel[f"Capacity_Factor_{tech}_%"] = (
                        capacity_factor
                    )
                else:
                    capacity_factor_by_fuel[f"Capacity_Factor_{tech}_%"] = 0
            

            # Prepare the data dictionary for this year
            year_data = {
                "Year": calendar_year,
                "Planning_Year_t": t,
                "E_base_MWh": model.E_base[t],
                "E_DC_MWh": model.E_DC[t],
                "E_EOR_MWh": model.E_EOR[t],
                "E_total_MWh": model.E_total[t],
                "P_peak_base_MW": model.P_peak_base[t],
                "P_peak_DC_MW": model.P_peak_DC[t],
                "P_peak_EOR_MW": model.P_peak_EOR[t],
                "P_peak_total_MW": model.P_peak_total[t],
                "Total_Annual_Generation_MWh": total_annual_generation,
                "Total_Annual_Curtailment_gen_MWh": total_annual_curtailment_gen,
                "Total_Annual_Curtailment_MWh": total_annual_curtailment,
                "Curtailment_gen_Rate_%": curtailment_gen_rate,
                "Curtailment_Rate_%": curtailment_rate,
                "Total_New_Gen_Capacity_MW": total_new_gen_capacity,
                "Total_New_Trans_Capacity_MW": total_new_trans_capacity,
                "Total_New_Storage_Capacity_MW": total_new_stor_capacity,
                "Number_Invested_Gen": num_invested_gen,
                "Number_Invested_Trans": num_invested_trans,
                "Number_Invested_Storage": num_invested_storage,
                "Total_Trans_Capacity_at_t_MW": total_trans_capacity_at_t,
                "Total_Storage_Capacity_at_t_MW": total_stor_capacity_at_t,
                # CAPEX metrics
                "CAPEX_USD": capex_t,
                "CAPEX_gen_t_USD": capex_gen_t,
                "CAPEX_trans_t_USD": capex_trans_discounted_t,
                "CAPEX_stor_t_USD": capex_stor_t,
                # OPEX metrics
                "Total_OPEX_USD": total_opex_t,
                "OPEX_gen_t_USD": opex_gen_t,
                "OPEX_gen_variable_t_USD": opex_gen_variable_t,
                "OPEX_gen_fixed_t_USD": opex_gen_fixed_t,
                "OPEX_stor_t_USD": opex_stor_t,
                # Other costs
                "Cost_Curt_Gen_USD": cost_curt_gen_t,
                "Cost_Curt_USD": cost_curt_t,
                "Annual_Cost_USD": annual_cost_t,
                # Million USD versions
                "CAPEX_Million_USD": capex_t / 1e6,
                "CAPEX_gen_t_Million_USD": capex_gen_t / 1e6,
                "CAPEX_trans_t_Million_USD": capex_trans_discounted_t / 1e6,
                "CAPEX_stor_t_Million_USD": capex_stor_t / 1e6,
                "Total_OPEX_Million_USD": total_opex_t / 1e6,
                "OPEX_gen_t_Million_USD": opex_gen_t / 1e6,
                "OPEX_gen_variable_t_Million_USD": opex_gen_variable_t / 1e6,
                "OPEX_gen_fixed_t_Million_USD": opex_gen_fixed_t / 1e6,
                "OPEX_stor_t_Million_USD": opex_stor_t / 1e6,
                "Cost_Curt_Gen_Million_USD": cost_curt_gen_t / 1e6,
                "Cost_Curt_Million_USD": cost_curt_t / 1e6,
                "Annual_Cost_Million_USD": annual_cost_t / 1e6,
            }

            # Add CAPEX breakdown by generator technologies (Million USD only)
            for tech in model.I_gen:
                year_data[f"CAPEX_gen_{tech}_t_Million_USD"] = capex_gen_by_tech[tech] / 1e6

            # Add OPEX breakdown by generator technologies (Million USD only)
            for tech in model.I_gen:
                year_data[f"OPEX_gen_variable_{tech}_t_Million_USD"] = opex_gen_variable_by_tech[tech] / 1e6
                year_data[f"OPEX_gen_fixed_{tech}_t_Million_USD"] = opex_gen_fixed_by_tech[tech] / 1e6

            # Add the fuel-specific metrics
            year_data.update(new_gen_capacity_by_fuel)
            year_data.update(total_gen_capacity_by_fuel)
            year_data.update(capacity_factor_by_fuel)

            # Add row to multi-year data
            multiyear_data.append(year_data)

        # Create Multi-Year Metrics DataFrame (transpose so years are columns)
        multiyear_df = pd.DataFrame(multiyear_data)

        # Transpose the data: metrics as rows, years as columns
        metrics_transposed = {}

        # First add the planning year row
        planning_years_row = {}
        for i, data in enumerate(multiyear_data):
            year_col = f"Year_{data['Year']}"
            planning_years_row[year_col] = data["Planning_Year_t"]
        metrics_transposed["Planning_Year_t"] = planning_years_row

        # Add all other metrics as rows
        metric_keys = [
            key
            for key in multiyear_data[0].keys()
            if key not in ["Year", "Planning_Year_t"]
        ]

        for metric_key in metric_keys:
            metric_row = {}
            for data in multiyear_data:
                year_col = f"Year_{data['Year']}"
                metric_row[year_col] = data[metric_key]
            metrics_transposed[metric_key] = metric_row

        # Convert to DataFrame with metrics as index (rows) and years as columns
        transposed_df = pd.DataFrame(metrics_transposed).T

        # Clean up column names (remove "Year_" prefix)
        transposed_df.columns = [
            col.replace("Year_", "") for col in transposed_df.columns
        ]

        # Add a column for metric names (make it the first column)
        transposed_df.insert(0, "Metric", transposed_df.index)

        transposed_df.to_excel(writer, sheet_name="Multi-Year Metrics", index=False)

        # ====================================================================
        # 2. GENERATION INVESTMENT TAB
        # ====================================================================
        print("Creating Generation Investment tab...")

        gen_investment_data = []
        for n, i in model.G:
            for t in planning_years:
                capacity = model.c_gen[n, i, t].value or 0
                if capacity > 1e-6:  # Only include non-zero investments
                    gen_investment_data.append(
                        {
                            "Bus Number": n,
                            "Gen Technology": i,
                            "Year": model.time_currentYear[t],
                            "Investment (MW)": capacity,
                        }
                    )

        gen_investment_df = pd.DataFrame(gen_investment_data)
        gen_investment_df.to_excel(
            writer, sheet_name="Generation Investment", index=False
        )

        # ====================================================================
        # 3. TRANSMISSION INVESTMENT TAB
        # ====================================================================
        print("Creating Transmission Investment tab...")

        trans_investment_data = []
        for n, n_prime in model.L:
            for t in planning_years:
                capacity = model.c_trans[n, n_prime, t].value or 0
                if capacity > 1e-6:  # Only include non-zero investments
                    trans_investment_data.append(
                        {
                            "From Bus": n,
                            "To Bus": n_prime,
                            "Year": model.time_currentYear[t],
                            "Investment (MW)": capacity,
                        }
                    )

        trans_investment_df = pd.DataFrame(trans_investment_data)
        trans_investment_df.to_excel(
            writer, sheet_name="Transmission Investment", index=False
        )

        # ====================================================================
        # 4. STORAGE INVESTMENT TAB
        # ====================================================================
        print("Creating Storage Investment tab...")

        storage_investment_data = []
        for n in model.N:
            for t in planning_years:
                capacity = model.c_stor[n, t].value or 0
                if capacity > 1e-6:  # Only include non-zero investments
                    storage_investment_data.append(
                        {
                            "Bus": n,
                            "Year": model.time_currentYear[t],
                            "Investment (MW)": capacity,
                        }
                    )

        storage_investment_df = pd.DataFrame(storage_investment_data)
        storage_investment_df.to_excel(
            writer, sheet_name="Storage Investment", index=False
        )

        # ====================================================================
        # 5. CURTAILMENT DETAIL TAB
        # ====================================================================
        print("Creating Curtailment Detail tab...")

        curtailment_detail_data = []
        for n in model.N:
            for t in planning_years:
                calendar_year = model.time_currentYear[t]

                # Calculate annual values
                annual_generation = 0
                annual_curtailment_gen = 0
                annual_load_demand = 0
                annual_curtailment = 0

                for d in model.D:
                    weight = model.weight_repDays[d]
                    for h in model.H:
                        # Generation at this bus
                        for n_gen, i in model.G:
                            if n_gen == n:
                                gen_val = model.p_gen[n_gen, i, t, d, h].value or 0
                                annual_generation += gen_val * weight

                                curt_gen_val = (
                                    model.curt_gen[n_gen, i, t, d, h].value or 0
                                )
                                annual_curtailment_gen += curt_gen_val * weight

                        # Load demand at this bus
                        demand = model.D_base[n, t, d, h]
                        annual_load_demand += demand * weight

                        # Add DC and EOR loads if applicable
                        if n in model.N_DC: # changed from N_DC to N
                            dc_load = model.p_DC[n, t, d, h].value or 0
                            annual_load_demand += dc_load * weight
                        if n in model.N_EOR:
                            eor_load = model.p_EOR[n, t, d, h].value or 0
                            annual_load_demand += eor_load * weight

                        # Curtailment at this bus
                        curt_val = model.curt[n, t, d, h].value or 0
                        annual_curtailment += curt_val * weight

                curtailment_detail_data.append(
                    {
                        "Bus": n,
                        "Year": calendar_year,
                        "Annual Generation (MWh)": annual_generation,
                        "Annual Curtailment_gen (MWh)": annual_curtailment_gen,
                        "Annual Load Demand (MWh)": annual_load_demand,
                        "Annual Curtailment (MWh)": annual_curtailment,
                    }
                )

        curtailment_detail_df = pd.DataFrame(curtailment_detail_data)
        curtailment_detail_df.to_excel(
            writer, sheet_name="Curtailment Detail", index=False
        )

        # ====================================================================
        # 6. ENERGY BALANCE TAB
        # ====================================================================
        print("Creating Energy Balance tab...")

        energy_balance_data = []

        # This will be a large dataset, so we might want to sample or limit it
        print(
            "Energy Balance tab will be very large. Processing all n,t,d,h combinations..."
        )

        for n in model.N:
            for t in planning_years:
                for d in model.D:
                    for h in model.H:
                        # Calculate all energy balance components
                        p_gen_sum = sum(
                            model.p_gen[n_gen, i, t, d, h].value or 0
                            for n_gen, i in model.G
                            if n_gen == n
                        )

                        curt_gen_sum = sum(
                            model.curt_gen[n_gen, i, t, d, h].value or 0
                            for n_gen, i in model.G
                            if n_gen == n
                        )

                        p_stor_discharge = model.p_stor_discharge[n, t, d, h].value or 0
                        p_stor_charge = model.p_stor_charge[n, t, d, h].value or 0

                        # Calculate net transmission flow
                        p_transmission_net_sum = sum(
                            BaseMVA
                            / model.line_x[min(n, n_prime), max(n, n_prime)]
                            * (
                                (model.theta[n, t, d, h].value or 0)
                                - (model.theta[n_prime, t, d, h].value or 0)
                            )
                            for n_prime in bus_connections[n]
                        )

                        d_base = model.D_base[n, t, d, h]
                        p_dc = (
                            model.p_DC[n, t, d, h].value or 0 if n in model.N_DC else 0 # changed from N_DC to N
                        )
                        p_eor = (
                            model.p_EOR[n, t, d, h].value or 0
                            if n in model.N_EOR
                            else 0
                        )
                        curt = model.curt[n, t, d, h].value or 0

                        # Calculate balance
                        lhs_total = (
                            p_gen_sum
                            - curt_gen_sum
                            + p_stor_discharge
                            - p_stor_charge
                            - p_transmission_net_sum
                        )
                        rhs_total = d_base + p_dc + p_eor - curt
                        balance_error = lhs_total - rhs_total

                        energy_balance_data.append(
                            {
                                "Bus": n,
                                "Year": model.time_currentYear[t],
                                "Day": d,
                                "Hour": h,
                                "P_Gen_Sum": p_gen_sum,
                                "Curt_Gen": -curt_gen_sum,  # Negative as specified
                                "P_Stor_Discharge": p_stor_discharge,
                                "P_Stor_Charge": -p_stor_charge,  # Negative as specified
                                "P_Transmission_Net_Sum": -p_transmission_net_sum,  # Negative as specified
                                "D_Base": d_base,
                                "P_DC": p_dc,
                                "P_EOR": p_eor,
                                "Curt": -curt,  # Negative as specified
                                "LHS_Total": lhs_total,
                                "RHS_Total": rhs_total,
                                "Balance_Error": balance_error,
                            }
                        )

        energy_balance_df = pd.DataFrame(energy_balance_data)
        energy_balance_df.to_excel(writer, sheet_name="Energy Balance", index=False)

    print(f"\nAnalysis complete! Results saved to:")
    print(f"{excel_filename}")
    print(f"\nExcel file contains {7} tabs:")
    print("  1. Summary - Optimization scenarios and capacity summaries")
    print(
        "  2. Multi-Year Metrics - Year-by-year energy, demand, costs, and investments"
    )
    print("  3. Generation Investment - c_gen[n,i,t] investments")
    print("  4. Transmission Investment - c_trans[n,n',t] investments")
    print("  5. Storage Investment - c_stor[n,t] investments")
    print("  6. Curtailment Detail - Annual curtailment by bus and year")
    print("  7. Energy Balance - Detailed power balance for all n,t,d,h")


    

    print("\n" + "=" * 80)
    print("CASE 2 ANALYSIS COMPLETED")
    print("=" * 80)


# Run the analysis
if __name__ == "__main__":
    analyze_case2_results()
