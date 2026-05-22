# Household-Load-Profiling-Data-Pipeline


## 🧩 Core Analytical Engineering Modules

### 1. Data Processing & Structural Normalization (Python Layer)
Raw telemetry sequences often arrive with missing packets, formatting anomalies, and uncalibrated metrics. The ingestion script applies strict vector transformations using Pandas:
- **Feature Convergence:** Aggregating granular passive voltage and current fields into a composite `Total_Demand_kW` metric.
- **Null Containment:** Utilizing time-series forward-filling (`ffill()`) and numeric coercion parameters to maintain continuous arrays without creating signal gaps.
- **Relational Mapping:** Automatically structuring raw metrics into structured SQL Server schemas using an optimized `SQLAlchemy` database engine.

---

## 📈 Power Engineering Performance Metrics (DAX Core)

These core electrical engineering metrics are calculated dynamically inside the reporting engine:

| Analytical Parameter | Engineering Significance | Target / Operational Baseline |
| :--- | :--- | :--- |
| **Grid Power Factor ($PF$)** | Measures line system efficiency; separates real working power from inductive line drops. | Ideal: $\ge 0.90$ (Below $0.85$ indicates inductive losses) |
| **Peak Load Capacity** | Tracks maximum concurrent household demand to predict circuit breaker/grid stress. | Variable based on connected utility threshold. |
| **Baseline Standby Load** | Isolates continuous phantom loads (refrigerators, smart hubs, standby appliances). | Constant non-zero lower bound. |
| **Day-over-Day Delta %** | Computes immediate usage trends to flag anomalous daily consumption behaviors. | Target: $\le 0.0\%$ (Stable or decreasing) |

---

## 💡 System Insights & Actionable Analytics

By analyzing the structured relational datasets through both the **Power BI Report Canvas** and the **Streamlit Web Interface**, the following operational patterns can be derived:

1. **Power Quality Analysis (PF Tracking):** By tracking the ratio between `Global_active_power` and `Global_reactive_power`, the system maps periods of low power factor. This helps in identifying inefficient appliances that cause reactive power penalties.
2. **Peak Demand Shaving:** High-load spikes (`Peak_Load_kW`) typically correlate with specific temporal intervals (e.g., evening hours). Utilizing this data, smart homes can implement automated load-shifting (e.g., running heavy appliances like washers during off-peak windows).
3. **Standby Drain Optimization:** The baseline load profiling mechanism successfully exposes the household's minimum continuous power draw, helping users audit always-on appliances to reduce baseline grid costs.
