import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tslearn.clustering import TimeSeriesKMeans

import os

# -----------------------------
# Configuration
# -----------------------------
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Input files
load_xlsx_path = os.path.join(script_dir, "Reconstructed_Load_2019.xlsx")
wind_xlsx_path = os.path.join(script_dir, "Reconstructed_CF_wind_2019.xlsx")
solar_xlsx_path = os.path.join(script_dir, "Reconstructed_CF_solar_2019.xlsx")

# Output directory and files
output_dir = os.path.join(script_dir, "Results Load+CF Clusters")
plot_dir = os.path.join(output_dir, "Bus_Clustering_Plots")
center_csv_path = os.path.join(output_dir, "cluster_centers_per_bus.csv")
weight_csv_path = os.path.join(output_dir, "cluster_weights.csv")

os.makedirs(output_dir, exist_ok=True)
os.makedirs(plot_dir, exist_ok=True)

# -----------------------------
# Load data for all parameters
# -----------------------------

print("Loading data...")

# Load all load buses (123 buses)
print("Loading load data...")
all_load_buses = []
for bus_id in range(1, 124):
    df = pd.read_excel(load_xlsx_path, sheet_name=f"Bus {bus_id}", index_col=0)
    # Take only the 24 hour columns (skip the first column which might be day info)
    load_data = df.iloc[:, :24].to_numpy()  # shape: [365, 24]
    all_load_buses.append(load_data)
load_data = np.stack(all_load_buses, axis=-1)  # shape: [365, 24, 123]

# Load wind CF data
print("Loading wind CF data...")
wind_sheets = pd.read_excel(wind_xlsx_path, sheet_name=None)
wind_bus_numbers = []
all_wind_buses = []
for sheet_name in sorted(wind_sheets.keys()):
    bus_num = int(sheet_name.split()[1])  # Extract bus number from "Bus X"
    wind_bus_numbers.append(bus_num)
    df = wind_sheets[sheet_name]
    if df.shape[1] > 24:  # If there's an index column
        wind_cf_data = df.iloc[:, 1:25].to_numpy()  # Take 24 hour columns
    else:
        wind_cf_data = df.iloc[:, :24].to_numpy()
    all_wind_buses.append(wind_cf_data)
wind_data = np.stack(all_wind_buses, axis=-1)  # shape: [365, 24, 37]

# Load solar CF data
print("Loading solar CF data...")
solar_sheets = pd.read_excel(solar_xlsx_path, sheet_name=None)
solar_bus_numbers = []
all_solar_buses = []
for sheet_name in sorted(solar_sheets.keys()):
    bus_num = int(sheet_name.split()[1])  # Extract bus number from "Bus X"
    solar_bus_numbers.append(bus_num)
    df = solar_sheets[sheet_name]
    if df.shape[1] > 24:  # If there's an index column
        solar_cf_data = df.iloc[:, 1:25].to_numpy()  # Take 24 hour columns
    else:
        solar_cf_data = df.iloc[:, :24].to_numpy()
    all_solar_buses.append(solar_cf_data)
solar_data = np.stack(all_solar_buses, axis=-1)  # shape: [365, 24, 35]

print(f"Load data shape: {load_data.shape}")
print(f"Wind CF data shape: {wind_data.shape}")
print(f"Solar CF data shape: {solar_data.shape}")
print(f"Wind buses: {wind_bus_numbers}")
print(f"Solar buses: {solar_bus_numbers}")

# Combine all data into single array [365, 24, 195]
# Total dimensions: 123 (load) + 37 (wind) + 35 (solar) = 195
X = np.concatenate([load_data, wind_data, solar_data], axis=-1)
print(f"Combined data shape: {X.shape}")

# -----------------------------
# Clustering (no scaling)
# -----------------------------
print("Performing clustering...")
n_clusters = 5
km = TimeSeriesKMeans(n_clusters=n_clusters, metric="euclidean", random_state=0)
labels = km.fit_predict(X)
centers = km.cluster_centers_  # shape: [n_clusters, 24, 195]

print(f"Clustering completed. Cluster centers shape: {centers.shape}")

# -----------------------------
# Save cluster centers with parameter identification
# -----------------------------
print("Saving cluster centers...")
center_data = []

# Process load data (first 123 dimensions)
for cluster_id in range(n_clusters):
    for bus_k in range(123):
        row = {"parameter": "load", "cluster": cluster_id, "bus": bus_k + 1}
        for h in range(24):
            row[f"hour_{h+1}"] = centers[cluster_id, h, bus_k]
        center_data.append(row)

# Process wind CF data (next 37 dimensions)
for cluster_id in range(n_clusters):
    for wind_idx in range(37):
        bus_num = wind_bus_numbers[wind_idx]
        row = {"parameter": "CF_wind", "cluster": cluster_id, "bus": bus_num}
        for h in range(24):
            row[f"hour_{h+1}"] = centers[cluster_id, h, 123 + wind_idx]
        center_data.append(row)

# Process solar CF data (last 35 dimensions)
for cluster_id in range(n_clusters):
    for solar_idx in range(35):
        bus_num = solar_bus_numbers[solar_idx]
        row = {"parameter": "CF_solar", "cluster": cluster_id, "bus": bus_num}
        for h in range(24):
            row[f"hour_{h+1}"] = centers[cluster_id, h, 123 + 37 + solar_idx]
        center_data.append(row)

df_centers = pd.DataFrame(center_data)
df_centers.to_csv(center_csv_path, index=False)

# -----------------------------
# Save cluster weights (fraction of year)
# -----------------------------
print("Saving cluster weights...")
weights = np.bincount(labels, minlength=n_clusters) / len(labels)
df_weights = pd.DataFrame(
    {
        "cluster": list(range(n_clusters)),
        "weight": weights,
        "days": weights * len(labels),
    }
)
df_weights.to_csv(weight_csv_path, index=False)

# -----------------------------
# Save plots for load buses
# -----------------------------
print("Generating load plots...")
for bus_k in range(123):
    bus_series = load_data[:, :, bus_k]  # [365, 24]

    plt.figure(figsize=(10, 6))
    for i, ts in enumerate(bus_series):
        plt.plot(ts, color=f"C{labels[i]}", alpha=0.3)
    for i in range(n_clusters):
        center_bus = centers[i, :, bus_k]
        plt.plot(center_bus, color=f"C{i}", linewidth=3, label=f"Cluster {i} center")

    plt.title(f"Load - Bus {bus_k + 1} (Clustered on Load + CF_wind + CF_solar)")
    plt.xlabel("Hour")
    plt.ylabel(f"Load (Bus {bus_k + 1})")
    plt.legend()
    plt.tight_layout()

    plot_path = os.path.join(plot_dir, f"load_bus_{bus_k + 1:03d}_cluster.png")
    plt.savefig(plot_path)
    plt.close()

# -----------------------------
# Save plots for wind CF buses
# -----------------------------
print("Generating wind CF plots...")
for wind_idx in range(37):
    bus_num = wind_bus_numbers[wind_idx]
    bus_series = wind_data[:, :, wind_idx]  # [365, 24]

    plt.figure(figsize=(10, 6))
    for i, ts in enumerate(bus_series):
        plt.plot(ts, color=f"C{labels[i]}", alpha=0.3)
    for i in range(n_clusters):
        center_bus = centers[i, :, 123 + wind_idx]
        plt.plot(center_bus, color=f"C{i}", linewidth=3, label=f"Cluster {i} center")

    plt.title(f"Wind CF - Bus {bus_num} (Clustered on Load + CF_wind + CF_solar)")
    plt.xlabel("Hour")
    plt.ylabel(f"Wind CF (Bus {bus_num})")
    plt.legend()
    plt.tight_layout()

    plot_path = os.path.join(plot_dir, f"wind_CF_bus_{bus_num:03d}_cluster.png")
    plt.savefig(plot_path)
    plt.close()

# -----------------------------
# Save plots for solar CF buses
# -----------------------------
print("Generating solar CF plots...")
for solar_idx in range(35):
    bus_num = solar_bus_numbers[solar_idx]
    bus_series = solar_data[:, :, solar_idx]  # [365, 24]

    plt.figure(figsize=(10, 6))
    for i, ts in enumerate(bus_series):
        plt.plot(ts, color=f"C{labels[i]}", alpha=0.3)
    for i in range(n_clusters):
        center_bus = centers[i, :, 123 + 37 + solar_idx]
        plt.plot(center_bus, color=f"C{i}", linewidth=3, label=f"Cluster {i} center")

    plt.title(f"Solar CF - Bus {bus_num} (Clustered on Load + CF_wind + CF_solar)")
    plt.xlabel("Hour")
    plt.ylabel(f"Solar CF (Bus {bus_num})")
    plt.legend()
    plt.tight_layout()

    plot_path = os.path.join(plot_dir, f"solar_CF_bus_{bus_num:03d}_cluster.png")
    plt.savefig(plot_path)
    plt.close()

print(f"✅ All cluster plots saved to: {plot_dir}")
print(f"✅ Cluster center CSV saved to: {center_csv_path}")
print(f"✅ Cluster weight CSV saved to: {weight_csv_path}")
print(f"\nClustering Summary:")
print(f"- Total dimensions: {X.shape[2]} (123 load + 37 wind + 35 solar)")
print(f"- Number of clusters: {n_clusters}")
print(f"- Data shape: {X.shape}")
print(f"- Generated {123 + 37 + 35} plots total")
