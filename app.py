import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="KPT Bias Simulator", layout="wide")

st.title("📦 KPT Bias Simulation Engine")
st.markdown("Simulating Merchant FOR noise impact on ETA accuracy")

# ---------------------------
# SIDEBAR CONTROLS
# ---------------------------
with st.sidebar:
    st.header("Simulation Controls")

    noise_ratio = st.slider(
        "Noisy Merchant %",
        0.0,
        1.0,
        0.4,
        key="noise_slider"
    )

    n_orders = st.slider(
        "Number of Orders",
        5000,
        20000,
        15000,
        step=1000,
        key="order_slider"
    )

# ---------------------------
# SYNTHETIC DATA GENERATION
# ---------------------------

def generate_merchants(n_merchants, noise_ratio):
    merchants = pd.DataFrame({
        "merchant_id": np.arange(n_merchants),
        "base_capacity": np.random.randint(5, 20, n_merchants),
        "chef_count": np.random.randint(1, 6, n_merchants),
        "bias_factor": np.where(
            np.random.rand(n_merchants) < noise_ratio,
            np.random.uniform(0.8, 1.2, n_merchants),
            0
        ),
        "reliability_score": np.random.uniform(0.6, 1.0, n_merchants)
    })
    return merchants


def generate_orders(n_orders, merchants):
    start_time = datetime(2024, 1, 1, 8, 0, 0)

    orders = pd.DataFrame({
        "order_id": np.arange(n_orders),
        "merchant_id": np.random.choice(merchants["merchant_id"], n_orders),
        "items_count": np.random.randint(1, 6, n_orders),
        "item_complexity_score": np.random.randint(1, 6, n_orders)
    })

    orders["order_time"] = [
        start_time + timedelta(minutes=int(np.random.uniform(0, 720)))
        for _ in range(n_orders)
    ]

    return orders


def simulate_prep_times(orders, merchants):

    orders = orders.merge(merchants, on="merchant_id")

    orders["active_orders_at_time"] = np.random.poisson(5, len(orders))
    orders["rider_queue_count"] = np.random.poisson(3, len(orders))

    # ---------------------------
    # Peak Hour Feature
    # ---------------------------

    orders["hour"] = orders["order_time"].dt.hour

    # Lunch (12–15) and Dinner (18–22)
    orders["time_of_day_peak_flag"] = orders["hour"].apply(
        lambda x: 1 if (12 <= x <= 15) or (18 <= x <= 22) else 0
    )
    
    orders["true_prep_time"] = (
        5
        + 2 * orders["items_count"]
        + 3 * orders["item_complexity_score"]
        + 1.5 * orders["active_orders_at_time"]
    )

    orders["true_ready_time"] = (
        orders["order_time"]
        + pd.to_timedelta(orders["true_prep_time"], unit="m")
    )

    return orders


def simulate_merchant_for(orders):

    noise = np.random.normal(0, 3, len(orders))

    orders["merchant_FOR_time"] = (
        orders["true_ready_time"]
        + pd.to_timedelta(noise, unit="m")
        + pd.to_timedelta(
            orders["bias_factor"] * orders["rider_queue_count"], unit="m"
        )
    )

    return orders


# ---------------------------
# RUN SIMULATION
# ---------------------------

merchants = generate_merchants(300, noise_ratio)
orders = generate_orders(n_orders, merchants)
orders = simulate_prep_times(orders, merchants)
orders = simulate_merchant_for(orders)

# ---------------------------
# STEP 2: BIAS LEARNING
# ---------------------------

orders["signed_error_minutes"] = (
    (orders["merchant_FOR_time"] - orders["true_ready_time"])
    .dt.total_seconds() / 60
)

merchant_bias = (
    orders.groupby("merchant_id")["signed_error_minutes"]
    .mean()
    .reset_index()
    .rename(columns={"signed_error_minutes": "learned_bias"})
)

orders = orders.merge(merchant_bias, on="merchant_id")

orders["corrected_ready_time"] = (
    orders["merchant_FOR_time"]
    - pd.to_timedelta(orders["learned_bias"], unit="m")
)

orders["corrected_error_minutes"] = (
    (orders["corrected_ready_time"] - orders["true_ready_time"])
    .dt.total_seconds()
    .abs() / 60
)

# ---------------------------
# STEP 3: RELIABILITY SCORING
# ---------------------------

merchant_volatility = (
    orders.groupby("merchant_id")["signed_error_minutes"]
    .std()
    .reset_index()
    .rename(columns={"signed_error_minutes": "volatility"})
)

orders = orders.merge(merchant_volatility, on="merchant_id")

orders["reliability_score"] = 1 / (1 + orders["volatility"])

orders["risk_adjusted_ready_time"] = (
    orders["corrected_ready_time"]
    + pd.to_timedelta(orders["volatility"] * 0.5, unit="m")
)

orders["risk_adjusted_error_minutes"] = (
    (orders["risk_adjusted_ready_time"] - orders["true_ready_time"])
    .dt.total_seconds()
    .abs() / 60
)

# ---------------------------
# STEP 4: OPERATIONAL IMPACT
# ---------------------------

arrival_buffer_minutes = 3
delivery_time_minutes = 15
sla_buffer_minutes = 25

def compute_operational_metrics(eta_column_name):
    rider_arrival = (
        orders[eta_column_name]
        - pd.to_timedelta(arrival_buffer_minutes, unit="m")
    )

    rider_wait = (
        (orders["true_ready_time"] - rider_arrival)
        .dt.total_seconds() / 60
    ).clip(lower=0)

    customer_eta = (
        orders[eta_column_name]
        + pd.to_timedelta(delivery_time_minutes, unit="m")
    )

    sla_deadline = (
        orders["true_ready_time"]
        + pd.to_timedelta(sla_buffer_minutes, unit="m")
    )

    sla_breach = customer_eta > sla_deadline

    return rider_wait.mean(), sla_breach.mean() * 100


raw_wait, raw_sla = compute_operational_metrics("merchant_FOR_time")
corrected_wait, corrected_sla = compute_operational_metrics("corrected_ready_time")
risk_wait, risk_sla = compute_operational_metrics("risk_adjusted_ready_time")

# ---------------------------
# STEP 5: COST SIMULATION
# ---------------------------

cost_per_wait_minute = 5
cost_per_sla_breach = 40
daily_orders_scale = 100000

def compute_cost(avg_wait, sla_percent):
    rider_cost = avg_wait * cost_per_wait_minute
    sla_cost = (sla_percent / 100) * cost_per_sla_breach
    cost_per_order = rider_cost + sla_cost
    daily_cost = cost_per_order * daily_orders_scale
    monthly_cost = daily_cost * 30
    return cost_per_order, monthly_cost


raw_cost_per_order, raw_monthly = compute_cost(raw_wait, raw_sla)
corrected_cost_per_order, corrected_monthly = compute_cost(corrected_wait, corrected_sla)
risk_cost_per_order, risk_monthly = compute_cost(risk_wait, risk_sla)

# ---------------------------
# DASHBOARD METRICS
# ---------------------------

st.subheader("📊 Core Accuracy Metrics")

p90_before = np.percentile(orders["signed_error_minutes"].abs(), 90)
p90_after = np.percentile(orders["corrected_error_minutes"], 90)
p90_risk = np.percentile(orders["risk_adjusted_error_minutes"], 90)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Orders", len(orders))
col2.metric("P90 Raw", round(p90_before, 2))
col3.metric("P90 Bias Corrected", round(p90_after, 2))
col4.metric("P90 Risk Adjusted", round(p90_risk, 2))

# ---------------------------
# OPERATIONAL IMPACT
# ---------------------------

st.subheader("🚴 Operational Impact")

col1, col2, col3 = st.columns(3)
col1.metric("Raw Avg Rider Wait", round(raw_wait, 2))
col2.metric("Corrected Avg Rider Wait", round(corrected_wait, 2))
col3.metric("Risk Adjusted Avg Rider Wait", round(risk_wait, 2))

st.markdown("---")

col4, col5, col6 = st.columns(3)
col4.metric("Raw SLA Breach %", round(raw_sla, 2))
col5.metric("Corrected SLA Breach %", round(corrected_sla, 2))
col6.metric("Risk Adjusted SLA Breach %", round(risk_sla, 2))

# ---------------------------
# COST IMPACT DASHBOARD
# ---------------------------

st.markdown("---")
st.subheader("💰 Monthly Cost Impact")

col1, col2, col3 = st.columns(3)

col1.metric("Raw Monthly Cost", f"${raw_monthly:,.0f}")
col2.metric(
    "Bias Corrected Monthly Cost",
    f"${corrected_monthly:,.0f}",
    delta=f"${corrected_monthly - raw_monthly:,.0f}"
)
col3.metric(
    "Risk Adjusted Monthly Cost",
    f"${risk_monthly:,.0f}",
    delta=f"${risk_monthly - raw_monthly:,.0f}"
)

savings_vs_raw = raw_monthly - corrected_monthly
risk_savings_vs_raw = raw_monthly - risk_monthly

st.markdown("### 📈 Estimated Savings")
st.write(f"Bias Correction saves: **${savings_vs_raw:,.0f} per month**")
st.write(f"Risk Adjusted System saves: **${risk_savings_vs_raw:,.0f} per month**")

# ---------------------------
# ERROR DISTRIBUTION
# ---------------------------

st.subheader("ETA Error Distribution Comparison")

fig, ax = plt.subplots()
ax.hist(orders["signed_error_minutes"].abs(), bins=50, alpha=0.4, label="Raw")
ax.hist(orders["corrected_error_minutes"], bins=50, alpha=0.4, label="Corrected")
ax.hist(orders["risk_adjusted_error_minutes"], bins=50, alpha=0.4, label="Risk Adjusted")
ax.set_xlabel("ETA Error (minutes)")
ax.set_ylabel("Order Count")
ax.legend()

st.pyplot(fig)

st.markdown("## 🔍 STEP 1 DATA AUDIT")

expected_columns = [
    # Order-level
    "order_id",
    "merchant_id",
    "order_time",
    "items_count",
    "item_complexity_score",
    "true_prep_time",
    
    # Merchant-level
    "base_capacity",
    "chef_count",
    "bias_factor",
    "reliability_score",
    
    # Dynamic
    "active_orders_at_time",
    "rider_queue_count",
    "time_of_day_peak_flag"
]

missing_cols = [col for col in expected_columns if col not in orders.columns]

if len(missing_cols) == 0:
    st.success("✅ All required STEP 1 columns exist.")
else:
    st.error("❌ Missing Columns:")
    st.write(missing_cols)

null_counts = orders[expected_columns].isnull().sum()
st.write("### Null Values Check")
st.write(null_counts)

st.write("### Sample Data Preview")
st.dataframe(orders[expected_columns].head())

st.write("### Orders Shape")
st.write(orders.shape)