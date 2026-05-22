import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import plotly.express as px

# Set up page configurations (MUST BE THE FIRST STREAMLIT COMMAND)
st.set_page_config(page_title="Household Load Profiling Dashboard", layout="wide")

# =====================================================================
# DATABASE CONNECTION
# =====================================================================
SERVER_NAME = "."
TARGET_DB = "SmartHomeKaggleDB"
connection_string = f"mssql+pyodbc://@{SERVER_NAME}/{TARGET_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"


@st.cache_data(ttl=600)  # Caches data for 10 minutes to stay fast
def load_data_from_sql():
    engine = create_engine(connection_string)
    query = "SELECT * FROM KaggleEnergyLog"
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Auto-detect timestamp column
    time_col = 'Timestamp' if 'Timestamp' in df.columns else ('Date' if 'Date' in df.columns else df.columns[0])
    df[time_col] = pd.to_datetime(df[time_col])
    return df, time_col


try:
    df, time_col = load_data_from_sql()

    # =====================================================================
    # WEB APP HEADER & SIDEBAR
    # =====================================================================
    st.title("⚡ Household Load Profiling & Energy Analytics")
    st.markdown("Live telemetry analysis tracking grid load curves, power quality, and subsystem footprints.")
    st.divider()  # Fixed the st.hr() error here

    # Sidebar Filters
    st.sidebar.header("📊 Filter System Data")
    df = df.sort_values(by=time_col)
    min_date = df[time_col].min().date()
    max_date = df[time_col].max().date()

    selected_date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date,
                                                max_value=max_date)

    # Filter DataFrame based on selection
    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        df_filtered = df[(df[time_col].dt.date >= start_date) & (df[time_col].dt.date <= end_date)]
    else:
        df_filtered = df

    # =====================================================================
    # STEP 3: ADVANCED ENGINEERING METRICS ENGINE
    # =====================================================================
    # 1. Total Consumption
    total_consumption = df_filtered['Total_Demand_kW'].sum()

    # 2. Power Factor Calculation
    active_power = df_filtered['Global_active_power'].sum() if 'Global_active_power' in df_filtered.columns else 1
    reactive_power = df_filtered['Global_reactive_power'].sum() if 'Global_reactive_power' in df_filtered.columns else 0
    apparent_power = np.sqrt(active_power ** 2 + reactive_power ** 2)
    power_factor = active_power / apparent_power if apparent_power > 0 else 1.0

    # 3. Cost Estimate (INR @ 7 Rs/Unit)
    estimated_cost = total_consumption * 7

    # Display Metrics in Top Row Columns
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⚡ Total Consumed", f"{total_consumption:,.2f} kWh")
    col2.metric("📈 Peak Demand", f"{df_filtered['Total_Demand_kW'].max():.2f} kW")
    col3.metric("🎯 Power Factor (PF)", f"{power_factor:.3f}")
    col4.metric("💰 Estimated Cost", f"₹ {estimated_cost:,.2f}")

    st.write("")

    # =====================================================================
    # STEP 4: INTERACTIVE VISUALIZATIONS
    # =====================================================================
    chart_col1, chart_col2 = st.columns([2, 1])

    with chart_col1:
        st.subheader("📋 Household Electrical Load Curve")
        # Taking a 200-row preview for faster plotting
        fig_line = px.line(df_filtered.head(200), x=time_col, y='Total_Demand_kW',
                           labels={time_col: 'Timeline Logs', 'Total_Demand_kW': 'Demand Load (kW)'},
                           template="plotly_white")
        fig_line.update_traces(line_color="mediumblue")
        st.plotly_chart(fig_line, use_container_width=True)

    with chart_col2:
        st.subheader("🛡️ Power Quality Split")
        if 'Global_active_power' in df_filtered.columns and 'Global_reactive_power' in df_filtered.columns:
            avg_active = df_filtered['Global_active_power'].mean()
            avg_reactive = df_filtered['Global_reactive_power'].mean()

            fig_pie = px.pie(names=['Useful Active Power', 'Wastage Reactive Power'],
                             values=[avg_active, avg_reactive],
                             color_discrete_sequence=px.colors.sequential.Magma)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Active/Reactive column matrices not found for profiling split.")

    # Show Data Table Snapshot at bottom
    st.subheader("📂 Relational Database Records View")
    st.dataframe(df_filtered.head(50), use_container_width=True)

except Exception as e:
    st.error(f"❌ Error connecting to database or parsing file: {e}")
    st.info("💡 Ensure your pipeline script has already executed and Microsoft SQL Server is active.")