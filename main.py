import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "Data" / "employee_data_1000.csv"


def parse_tenure_years(value: str) -> float:
    """Convert 'X years and Y months' into fractional years."""
    match = re.search(r"(\d+)\s*years?\s*and\s*(\d+)\s*months?", str(value), re.I)
    if not match:
        return 0.0
    years, months = int(match.group(1)), int(match.group(2))
    return round(years + months / 12, 2)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["Joining Date"] = pd.to_datetime(df["Joining Date"], errors="coerce")
    df["TenureYears"] = df["YearsOfService"].apply(parse_tenure_years)
    df["TenureBucket"] = pd.cut(
        df["TenureYears"],
        bins=[-0.01, 1, 3, 5, 10, 15, 100],
        labels=["0–1 yrs", "1–3 yrs", "3–5 yrs", "5–10 yrs", "10–15 yrs", "15+ yrs"],
    )
    df["PerformanceBand"] = pd.cut(
        df["Performance Score"],
        bins=[0, 4, 6, 8, 10],
        labels=["Needs Improvement (≤4)", "Average (4–6)", "Good (6–8)", "Excellent (8–10)"],
        include_lowest=True,
    )
    return df


def format_inr(value: float) -> str:
    return f"₹{value:,.0f}"


st.set_page_config(
    page_title="Company Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Company Employee Dashboard")
st.caption("Insights from 1,000 employee records")

df = load_data()

with st.sidebar:
    st.header("Filters")
    departments = sorted(df["Department"].dropna().unique())
    selected_depts = st.multiselect(
        "Department",
        options=departments,
        default=departments,
    )
    exp_min, exp_max = int(df["Experience"].min()), int(df["Experience"].max())
    experience_range = st.slider(
        "Experience (years)",
        min_value=exp_min,
        max_value=exp_max,
        value=(exp_min, exp_max),
    )

filtered = df[
    df["Department"].isin(selected_depts)
    & df["Experience"].between(experience_range[0], experience_range[1])
]

if filtered.empty:
    st.warning("No employees match the selected filters.")
    st.stop()

# --- KPI row ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Employees", f"{len(filtered):,}")
kpi2.metric("Avg Salary", format_inr(filtered["Salary"].mean()))
kpi3.metric("Avg Experience", f"{filtered['Experience'].mean():.1f} yrs")
kpi4.metric("Avg Performance", f"{filtered['Performance Score'].mean():.1f}")

st.divider()

# --- 1. Average salary by department ---
st.subheader("1. Average Salary by Department")
avg_salary = (
    filtered.groupby("Department", as_index=False)["Salary"]
    .mean()
    .sort_values("Salary", ascending=False)
)
avg_salary["Avg Salary Label"] = avg_salary["Salary"].map(format_inr)

salary_chart = (
    alt.Chart(avg_salary)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("Department:N", sort="-y", title="Department"),
        y=alt.Y("Salary:Q", title="Average Salary (₹)"),
        color=alt.Color("Department:N", legend=None),
        tooltip=[
            alt.Tooltip("Department:N"),
            alt.Tooltip("Salary:Q", title="Avg Salary", format=",.0f"),
        ],
    )
    .properties(height=360)
)
st.altair_chart(salary_chart, use_container_width=True)

# --- 2. Employee distribution by department ---
st.subheader("2. Employee Distribution by Department")
dept_counts = (
    filtered.groupby("Department", as_index=False)
    .size()
    .rename(columns={"size": "Employees"})
    .sort_values("Employees", ascending=False)
)

col_dist, col_table = st.columns([2, 1])
with col_dist:
    dist_chart = (
        alt.Chart(dept_counts)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("Employees:Q"),
            color=alt.Color("Department:N", legend=alt.Legend(title="Department")),
            tooltip=[
                alt.Tooltip("Department:N"),
                alt.Tooltip("Employees:Q"),
            ],
        )
        .properties(height=360)
    )
    st.altair_chart(dist_chart, use_container_width=True)

with col_table:
    st.dataframe(
        dept_counts.assign(Share=lambda d: (d["Employees"] / d["Employees"].sum() * 100).round(1).astype(str) + "%"),
        hide_index=True,
        use_container_width=True,
    )

# --- 3. Salary vs Experience ---
st.subheader("3. Salary vs Experience")
scatter = (
    alt.Chart(filtered)
    .mark_circle(size=60, opacity=0.65)
    .encode(
        x=alt.X("Experience:Q", title="Experience (years)"),
        y=alt.Y("Salary:Q", title="Salary (₹)"),
        color=alt.Color("Department:N", title="Department"),
        tooltip=[
            alt.Tooltip("Employee ID:N"),
            alt.Tooltip("Department:N"),
            alt.Tooltip("Job Role:N"),
            alt.Tooltip("Experience:Q"),
            alt.Tooltip("Salary:Q", format=",.0f"),
            alt.Tooltip("Performance Score:Q"),
        ],
    )
    .properties(height=400)
)
trend = (
    alt.Chart(filtered)
    .transform_regression("Experience", "Salary")
    .mark_line(color="#222222", strokeDash=[6, 4])
    .encode(x="Experience:Q", y="Salary:Q")
)
st.altair_chart(scatter + trend, use_container_width=True)
st.caption("Dashed line shows the overall salary–experience trend.")

# --- 4. Employee tenure ---
st.subheader("4. Employee Tenure")
tenure_counts = (
    filtered.groupby("TenureBucket", observed=False, as_index=False)
    .size()
    .rename(columns={"size": "Employees"})
)

tenure_chart = (
    alt.Chart(tenure_counts)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#2E86AB")
    .encode(
        x=alt.X("TenureBucket:N", title="Tenure", sort=list(tenure_counts["TenureBucket"])),
        y=alt.Y("Employees:Q", title="Number of Employees"),
        tooltip=[
            alt.Tooltip("TenureBucket:N", title="Tenure"),
            alt.Tooltip("Employees:Q"),
        ],
    )
    .properties(height=360)
)

t1, t2 = st.columns([3, 1])
with t1:
    st.altair_chart(tenure_chart, use_container_width=True)
with t2:
    st.metric("Avg Tenure", f"{filtered['TenureYears'].mean():.1f} yrs")
    st.metric("Median Tenure", f"{filtered['TenureYears'].median():.1f} yrs")
    st.metric("Longest Tenure", f"{filtered['TenureYears'].max():.1f} yrs")

# --- 5. Performance distribution ---
st.subheader("5. Performance Distribution")
perf_hist = (
    alt.Chart(filtered)
    .mark_bar(color="#1B998B")
    .encode(
        x=alt.X("Performance Score:Q", bin=alt.Bin(maxbins=20), title="Performance Score"),
        y=alt.Y("count():Q", title="Number of Employees"),
        tooltip=[
            alt.Tooltip("Performance Score:Q", bin=alt.Bin(maxbins=20), title="Score Range"),
            alt.Tooltip("count():Q", title="Employees"),
        ],
    )
    .properties(height=360)
)

band_counts = (
    filtered.groupby("PerformanceBand", observed=False, as_index=False)
    .size()
    .rename(columns={"size": "Employees"})
)

p1, p2 = st.columns([2, 1])
with p1:
    st.altair_chart(perf_hist, use_container_width=True)
with p2:
    st.write("Performance bands")
    st.dataframe(band_counts, hide_index=True, use_container_width=True)
    st.metric("Top Performers (≥8)", int((filtered["Performance Score"] >= 8).sum()))
    st.metric("Below Average (<6)", int((filtered["Performance Score"] < 6).sum()))

with st.expander("Preview filtered data"):
    st.dataframe(
        filtered[
            [
                "Employee ID",
                "Department",
                "Job Role",
                "Salary",
                "Experience",
                "YearsOfService",
                "Performance Score",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
