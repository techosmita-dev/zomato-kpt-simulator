import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🍽️ SmartKPT 2.0 — Advanced Kitchen Signal Simulation")

# -----------------------------
# 1️⃣ CONFIGURATION
# -----------------------------

st.sidebar.header("Restaurant Configuration")

num_orders = st.sidebar.slider("Incoming Orders (Batch Size)", 20, 300, 100)
avg_dish_time = st.sidebar.slider("Avg Dish Time (min)", 5, 30, 15)
num_chefs = st.sidebar.slider("Number of Chefs", 1, 10, 3)
num_equipments = st.sidebar.slider("Active Equipments", 1, 10, 3)
dine_in_load = st.sidebar.slider("Live Dine-in Customers", 0, 100, 20)
rush_multiplier = st.sidebar.slider("Peak Hour Intensity", 1.0, 2.0, 1.2)

# -----------------------------
# 2️⃣ TRUE PREP TIME SIMULATION
# -----------------------------

np.random.seed(42)

def simulate_true_kpt():
    base_time = np.random.normal(avg_dish_time, 3, num_orders)
    capacity_factor = (num_chefs + num_equipments)

    queue_delay = np.maximum(0, (num_orders / capacity_factor) - 5)

    rush_factor = 1 + (dine_in_load / 100) * rush_multiplier

    return np.maximum(5, base_time + queue_delay) * rush_factor

true_kpt = simulate_true_kpt()

# -----------------------------
# 3️⃣ MERCHANT FOR BIAS MODEL
# -----------------------------

def simulate_biased_for(true_kpt):
    bias_type = np.random.choice(
        ["late_marking", "rider_arrival_trigger", "manual_delay"],
        size=num_orders,
        p=[0.4, 0.4, 0.2]
    )

    bias = np.zeros(num_orders)

    bias[bias_type == "late_marking"] = np.random.uniform(3, 8)
    bias[bias_type == "rider_arrival_trigger"] = np.random.uniform(5, 12)
    bias[bias_type == "manual_delay"] = np.random.uniform(2, 5)

    return true_kpt + bias

baseline_kpt = simulate_biased_for(true_kpt)

# -----------------------------
# 4️⃣ SMART SIGNAL ENRICHMENT
# -----------------------------

def improved_signal_model(true_kpt):
    kitchen_load = num_orders / (num_chefs + num_equipments)
    congestion_penalty = np.log1p(kitchen_load)

    equipment_pressure = np.random.normal(0.5, 0.2, num_orders)

    return true_kpt + (0.2 * congestion_penalty) + equipment_pressure

improved_kpt = improved_signal_model(true_kpt)

# -----------------------------
# 5️⃣ METRIC COMPUTATION
# -----------------------------

def compute_metrics(predicted, actual):
    rider_arrival = predicted * 0.9
    wait_times = np.maximum(0, actual - rider_arrival)

    return {
        "avg_wait": np.mean(wait_times),
        "p50_error": np.median(np.abs(predicted - actual)),
        "p90_error": np.percentile(np.abs(predicted - actual), 90),
        "idle_proxy": np.mean(wait_times) * 0.6
    }

baseline_metrics = compute_metrics(baseline_kpt, true_kpt)
improved_metrics = compute_metrics(improved_kpt, true_kpt)

# -----------------------------
# 6️⃣ IMPROVEMENT %
# -----------------------------

def pct(b, i):
    return ((b - i) / b) * 100 if b != 0 else 0

wait_pct = pct(baseline_metrics["avg_wait"], improved_metrics["avg_wait"])
p50_pct = pct(baseline_metrics["p50_error"], improved_metrics["p50_error"])
p90_pct = pct(baseline_metrics["p90_error"], improved_metrics["p90_error"])
idle_pct = pct(baseline_metrics["idle_proxy"], improved_metrics["idle_proxy"])

# -----------------------------
# 7️⃣ DISPLAY RESULTS
# -----------------------------

st.subheader("📊 Performance Comparison")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔴 Baseline")
    for k, v in baseline_metrics.items():
        st.metric(k, round(v, 2))

with col2:
    st.markdown("### 🟢 SmartKPT")
    st.metric("Avg Wait", round(improved_metrics["avg_wait"], 2), f"-{wait_pct:.1f}%")
    st.metric("P50 Error", round(improved_metrics["p50_error"], 2), f"-{p50_pct:.1f}%")
    st.metric("P90 Error", round(improved_metrics["p90_error"], 2), f"-{p90_pct:.1f}%")
    st.metric("Idle Proxy", round(improved_metrics["idle_proxy"], 2), f"-{idle_pct:.1f}%")

# -----------------------------
# 8️⃣ ERROR DISTRIBUTION
# -----------------------------

st.subheader("📈 Error Distribution Comparison")

fig, ax = plt.subplots()
ax.hist(np.abs(baseline_kpt - true_kpt), bins=30, alpha=0.5, label="Baseline")
ax.hist(np.abs(improved_kpt - true_kpt), bins=30, alpha=0.5, label="Improved")
ax.legend()
st.pyplot(fig)

# -----------------------------
# 9️⃣ EXECUTIVE SUMMARY
# -----------------------------

st.success(f"""
SmartKPT reduces:
• Rider Wait Time by {wait_pct:.1f}%
• P50 ETA Error by {p50_pct:.1f}%
• P90 ETA Error by {p90_pct:.1f}%
• Rider Idle Time by {idle_pct:.1f}%

By eliminating merchant bias and incorporating:
- Kitchen congestion modeling
- Equipment pressure signals
- Chef capacity constraints
- External dine-in rush load
""")