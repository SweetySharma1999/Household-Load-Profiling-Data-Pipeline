import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================================
# STEP 1: KAGGLE DATASET LOADING & CLEANING (Python)
# =====================================================================
print("--- Step 1: Loading & Preprocessing Kaggle Dataset ---")

kaggle_file_path = "kaggle_smart_home.csv"

try:
    # 1.1 CSV File ko read karna
    df = pd.read_csv(kaggle_file_path)
    print(f"Original Columns found: {list(df.columns[:5])}...")

    # 1.2 Kaggle data me invalid values (jaise '?', ' ', 'N/A') ko handle karna
    # Unhe numeric me badalna aur errors='coerce' use karke text entries ko NaN (Null) banana
    target_columns = ['Global_active_power', 'Global_reactive_power', 'Voltage']
    for col in target_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Missing values wali rows ko permanently drop karna
    df = df.dropna()

    # 1.3 Time column identify karna aur handle karna (Dayfirst warning resolved)
    time_col = 'Timestamp' if 'Timestamp' in df.columns else ('Date' if 'Date' in df.columns else df.columns[0])
    df[time_col] = pd.to_datetime(df[time_col], dayfirst=True)

    # 1.4 Total demand feature engineering logic mapping (Ab yeh pure numeric float hoga)
    if 'Total_Demand_kW' not in df.columns:
        if 'Global_active_power' in df.columns:
            df['Total_Demand_kW'] = df['Global_active_power']
        else:
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            df['Total_Demand_kW'] = df[numeric_cols].sum(axis=1)

    print("Success! Kaggle data numeric validation and processing complete.")

except FileNotFoundError:
    print(f"Error: '{kaggle_file_path}' file nahi mili! Check file path.")
    exit()

# =====================================================================
# STEP 2: DATABASE ARCHITECTURE & SQL SERVER EXPORT
# =====================================================================
print("\n--- Step 2: Connecting to SQL Server Database ---")

SERVER_NAME = "."
ORIGINAL_DB = "master"
TARGET_DB = "SmartHomeKaggleDB"

connection_string_master = f"mssql+pyodbc://@{SERVER_NAME}/{ORIGINAL_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
connection_string_target = f"mssql+pyodbc://@{SERVER_NAME}/{TARGET_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

engine_master = create_engine(connection_string_master, isolation_level="AUTOCOMMIT")
with engine_master.connect() as conn:
    conn.execute(text(f"""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{TARGET_DB}')
        BEGIN
            CREATE DATABASE [{TARGET_DB}];
        END
    """))
print(f"Database setup verified: '{TARGET_DB}' ready.")

engine_target = create_engine(connection_string_target)
table_name = "KaggleEnergyLog"

# Pura processed table relational system me save karna
df.to_sql(table_name, con=engine_target, if_exists='replace', index=False)
print(f"Success! Properly typed Kaggle data uploaded to SQL Server table: '{table_name}'\n")

# =====================================================================
# STEP 3: DATA ANALYTICS VIA SQL QUERIES
# =====================================================================
print("--- Step 3: Running Analytics Queries on Kaggle Table ---")

with engine_target.connect() as conn:
    sum_query = text(f"SELECT SUM(Total_Demand_kW) FROM {table_name}")
    total_energy = conn.execute(sum_query).scalar()
    print(f"[METRIC] Total Energy Recorded in Dataset: {total_energy:.2f} kWh")

    peak_query = text(f"SELECT TOP 1 [{time_col}], Total_Demand_kW FROM {table_name} ORDER BY Total_Demand_kW DESC")
    peak_result = conn.execute(peak_query).fetchone()

    if peak_result:
        print(f"[INSIGHT] Peak Load Timestamp Identified: {peak_result[0]} with {peak_result[1]:.2f} kW")

# =====================================================================
# STEP 4: DATA VISUALIZATION PROFILING (Exploratory Data Analysis)
# =====================================================================
print("\n--- Step 4: Generating Exploratory Data Analysis (EDA) Charts ---")

sns.set_theme(style="whitegrid")
plt.figure(figsize=(15, 6))

# Plot 1: Household Electrical Load Curve
plt.subplot(1, 2, 1)
df_snapshot = df.head(100)
plt.plot(df_snapshot[time_col], df_snapshot['Total_Demand_kW'], color='mediumblue', linewidth=2, marker='o')
plt.title("Household Electrical Load Curve (Telemetry Preview)", fontsize=12, fontweight='bold')
plt.xlabel("Timeline / Temporal Logs", fontsize=10)
plt.ylabel("Total Active Demand (kW)", fontsize=10)
plt.xticks(rotation=45)

# Plot 2: Electrical Parameter Feature Analysis Breakdown (Seaborn Warning Resolved)
plt.subplot(1, 2, 2)
available_features = [col for col in target_columns if col in df.columns]

if available_features:
    avg_values = df[available_features].mean()
    # hue assign karke legend=False kiya taaki warning na aaye
    sns.barplot(x=avg_values.index, y=avg_values.values, hue=avg_values.index, palette="magma", legend=False)
    plt.title("Electrical Metrics Mean Intensity Profiling", fontsize=12, fontweight='bold')
    plt.ylabel("Mean Operational Intensity Values", fontsize=10)
    plt.xlabel("Electrical Parameters", fontsize=10)

plt.tight_layout()
plt.show()

print("\n[PIPELINE COMPLETE] Pipeline running successfully and dashboard visuals rendered!")