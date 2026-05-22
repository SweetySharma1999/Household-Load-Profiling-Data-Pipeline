import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# =====================================================================
# STEP 1: AUTOMATED DATASET GENERATION (Python)
# =====================================================================
print("--- Step 1: Generating Smart Home Appliance Dataset ---")

# 1.1 Generate continuous hourly timestamps for a full day
hours = pd.date_range(start="2026-05-20 00:00:00", end="2026-05-20 23:00:00", freq="h")

# 1.2 Simulate real-world engineering power consumption characteristics (in kW)
data = {
    "Timestamp": hours,
    # AC consumes 1.5 kW; mostly active during hot afternoons (12 PM - 5 PM) and nights (9 PM - 11 PM)
    "AC_Usage_kW": [1.5 if 12 <= h.hour <= 17 or 21 <= h.hour <= 23 else 0.0 for h in hours],
    # Refrigerator is a continuous baseline load fluctuating slightly around 0.2 kW
    "Refrigerator_kW": np.random.uniform(0.18, 0.22, len(hours)),
    # Geyser consumes a high peak load of 2.0 kW, primarily active during morning hours (7 AM - 8 AM)
    "Geyser_kW": [2.0 if 7 <= h.hour <= 8 else 0.0 for h in hours],
    # Lights and Fans spike in the evening (6 PM - 11 PM)
    "Lights_Fans_kW": [0.35 if 18 <= h.hour <= 23 else 0.05 for h in hours]
}

# 1.3 Construct DataFrame and calculate the total demand line load curve
df = pd.DataFrame(data)
df["Total_Demand_kW"] = df.iloc[:, 1:].sum(axis=1)

# 1.4 Save the raw telemetry file to your local system folder
csv_filename = "smart_home_energy_data.csv"
df.to_csv(csv_filename, index=False)
print(f"Success! Unstructured data compiled and saved as '{csv_filename}'\n")

# =====================================================================
# STEP 2: DATABASE ARCHITECTURE & IMPORT MANAGEMENT (SQL Server)
# =====================================================================
print("--- Step 2: Establishing SQL Server Database Connections ---")

# 2.1 Define SQL Server Local Connection Configurations
# Note: "." or "localhost" targets your main active local SQL Instance
SERVER_NAME = "."
ORIGINAL_DB = "master"
TARGET_DB = "SmartHomeDB"

# Setup database driver URLs
connection_string_master = f"mssql+pyodbc://@{SERVER_NAME}/{ORIGINAL_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
connection_string_target = f"mssql+pyodbc://@{SERVER_NAME}/{TARGET_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

# 2.2 Automatically create the target Database if it doesn't exist
engine_master = create_engine(connection_string_master, isolation_level="AUTOCOMMIT")
with engine_master.connect() as conn:
    # SQL Command to safely initialize database architecture
    conn.execute(text(f"""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{TARGET_DB}')
        BEGIN
            CREATE DATABASE [{TARGET_DB}];
        END
    """))
print(f"Database configuration validated: Database '{TARGET_DB}' is ready.")

# 2.3 Establish secure connection pipe to the freshly built SmartHomeDB
engine_target = create_engine(connection_string_target)

# 2.4 Pipe and push the local Pandas dataset directly up into SQL Server as a table
table_name = "EnergyLog"
df.to_sql(table_name, con=engine_target, if_exists='replace', index=False)
print(f"Success! Engineered data exported safely into SQL Table: '{table_name}'\n")

# =====================================================================
# STEP 3: DATABASE TELEMETRY PRODUCTION EXTRACTION (Analytics Queries)
# =====================================================================
print("--- Step 3: Performing Data Analytics Queries via SQL Server ---")

# Pull and verify the structural data straight back out of your relational table
with engine_target.connect() as conn:
    # Query 1: Extract overall daily operational summary statistics
    summary_query = text(f"SELECT SUM(Total_Demand_kW) AS Total_kWh FROM {table_name}")
    total_consumption = conn.execute(summary_query).scalar()
    print(f"[METRIC] Total Household Energy Consumed (24-Hours): {total_consumption:.2f} kWh")

    # Query 2: SQL conditional parameters parsing to pinpoint Critical Peak Demand hours
    peak_query = text(f"""
        SELECT TOP 1 Timestamp, Total_Demand_kW 
        FROM {table_name} 
        ORDER BY Total_Demand_kW DESC
    """)
    peak_result = conn.execute(peak_query).fetchone()
    print(f"[INSIGHT] Peak Grid Load Window Identified at {peak_result[0]} with a Load of: {peak_result[1]:.2f} kW")

    # Query 3: Individualized breakdown of electrical systems footprint metrics
    breakdown_query = text(f"""
        SELECT 
            SUM(AC_Usage_kW) AS Total_AC,
            SUM(Refrigerator_kW) AS Total_Fridge,
            SUM(Geyser_kW) AS Total_Geyser,
            SUM(Lights_Fans_kW) AS Total_Lights
        FROM {table_name}
    """)
    shares = conn.execute(breakdown_query).fetchone()

print("\n--- Final Subsystem Footprint Matrix Shares ---")
print(f"-> Air Conditioner Load share : {shares[0]:.2f} kWh ({(shares[0] / total_consumption) * 100:.1f}%)")
print(f"-> Refrigerator Base share    : {shares[1]:.2f} kWh ({(shares[1] / total_consumption) * 100:.1f}%)")
print(f"-> Water Geyser Thermal share : {shares[2]:.2f} kWh ({(shares[2] / total_consumption) * 100:.1f}%)")
print(f"-> Lighting & Ventilation     : {shares[3]:.2f} kWh ({(shares[3] / total_consumption) * 100:.1f}%)")
print("\n[PIPELINE COMPLETE] Your database pipeline is fully operational!")
