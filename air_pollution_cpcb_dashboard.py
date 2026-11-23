import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Smart Air Pollution Monitoring Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Smart Air Pollution Monitoring Dashboard")
st.caption("CPCB air-quality data analytics and long-term environmental trend visualization")

@st.cache_data
def load_data():
    path = "29Aug DA.csv"
    df = pd.read_csv(path, encoding="cp1252", low_memory=False)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    for col in ["so2", "no2", "rspm", "spm", "pm2_5"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = load_data()

pollutants = {
    "SO₂": "so2",
    "NO₂": "no2",
    "PM10 (RSPM)": "rspm",
    "SPM": "spm",
    "PM2.5": "pm2_5"
}

# ---------------- Sidebar filters ----------------
st.sidebar.header("🔎 Dashboard Filters")

states = sorted(df["state"].dropna().unique())
state = st.sidebar.selectbox("State", ["All States"] + states)

filtered = df.copy()
if state != "All States":
    filtered = filtered[filtered["state"] == state]

locations = sorted(filtered["location"].dropna().unique())
location = st.sidebar.selectbox("Location", ["All Locations"] + locations)

if location != "All Locations":
    filtered = filtered[filtered["location"] == location]

min_date = filtered["date"].min()
max_date = filtered["date"].max()

if pd.notna(min_date) and pd.notna(max_date):
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered = filtered[(filtered["date"] >= start) & (filtered["date"] <= end)]

pollutant_name = st.sidebar.selectbox("Pollutant for trend", list(pollutants.keys()))
pollutant_col = pollutants[pollutant_name]

# ---------------- KPI cards ----------------
st.subheader("📊 Current Dataset Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Records", f"{len(filtered):,}")
c2.metric("Monitoring Locations", f"{filtered['location'].nunique():,}")
c3.metric("States", f"{filtered['state'].nunique():,}")
c4.metric("Data From", str(filtered["date"].min().date()) if filtered["date"].notna().any() else "N/A")

# ---------------- Main charts ----------------
left, right = st.columns(2)

with left:
    st.subheader(f"📈 {pollutant_name} Long-Term Trend")
    trend_data = filtered.dropna(subset=[pollutant_col, "date"]).copy()
    trend = (
        trend_data.groupby(trend_data["date"].dt.year)[pollutant_col]
        .mean()
        .reset_index(name="Average")
        .rename(columns={"date": "Year"})
    )
    if not trend.empty:
        trend["Year"] = trend["Year"].astype(int)
        fig = px.line(
            trend, x="Year", y="Average", markers=True,
            labels={"Average": f"Average {pollutant_name}"}
        )
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for this selection.")

with right:
    st.subheader("🧪 Average Pollutant Levels")
    avg = filtered[list(pollutants.values())].mean().reset_index()
    avg.columns = ["Pollutant", "Average"]
    avg["Pollutant"] = avg["Pollutant"].map({v: k for k, v in pollutants.items()})
    avg = avg.dropna()
    if not avg.empty:
        fig = px.bar(
            avg, x="Pollutant", y="Average", text_auto=".1f",
            labels={"Average": "Average concentration"}
        )
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

# ---------------- State comparison ----------------
st.subheader("🗺️ State-wise Pollution Comparison")

state_pollution = (
    filtered.groupby("state")[pollutant_col]
    .mean()
    .dropna()
    .sort_values(ascending=False)
    .head(15)
    .reset_index()
)

if not state_pollution.empty:
    fig = px.bar(
        state_pollution,
        x=pollutant_col,
        y="state",
        orientation="h",
        text_auto=".1f",
        labels={pollutant_col: f"Average {pollutant_name}", "state": "State"}
    )
    fig.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Data quality ----------------
st.subheader("🧹 Data Quality")

q1, q2, q3 = st.columns(3)
q1.metric("Missing PM2.5", f"{filtered['pm2_5'].isna().mean()*100:.1f}%")
q2.metric("Missing PM10/RSPM", f"{filtered['rspm'].isna().mean()*100:.1f}%")
q3.metric("Missing NO₂", f"{filtered['no2'].isna().mean()*100:.1f}%")

# ---------------- Recent records ----------------
st.subheader("📋 Sample Records")
display_cols = [
    "date", "state", "location", "so2", "no2", "rspm", "spm", "pm2_5"
]
st.dataframe(
    filtered[display_cols].sort_values("date", ascending=False).head(100),
    use_container_width=True,
    hide_index=True
)

# ---------------- Download ----------------
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Filtered Data",
    data=csv,
    file_name="filtered_air_pollution_data.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("Project: Smart Air Pollution Monitoring Through Automated CPCB Data Analytics and Long-Term Environmental Trend Visualization")
