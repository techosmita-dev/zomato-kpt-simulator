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
        ["late_marking", "early_marking", "rider_trigger", "manual_variation"],
        size=num_orders,
        p=[0.35, 0.25, 0.25, 0.15]
    )

    bias = np.zeros(num_orders)

    # Overestimation
    bias[bias_type == "late_marking"] = np.random.uniform(3, 8)

    # Underestimation
    bias[bias_type == "early_marking"] = -np.random.uniform(2, 6)

    # Rider triggered random variation
    bias[bias_type == "rider_trigger"] = np.random.normal(0, 5)

    # Small manual fluctuations
    bias[bias_type == "manual_variation"] = np.random.normal(0, 2)

    return true_kpt + bias

baseline_kpt = simulate_biased_for(true_kpt)

# -----------------------------
# 4️⃣ SMART SIGNAL ENRICHMENT
# -----------------------------

def improved_signal_model(true_kpt):
    kitchen_load = num_orders / (num_chefs + num_equipments)
    
    congestion_penalty = 0.1 * np.log1p(kitchen_load)
    dine_in_penalty = 0.05 * (dine_in_load / 50)

    # Small symmetric noise (less than baseline)
    smart_noise = np.random.normal(0, 1.5, num_orders)

    return true_kpt + congestion_penalty + dine_in_penalty + smart_noise

improved_kpt = improved_signal_model(true_kpt)

# -----------------------------
# 5️⃣ METRIC COMPUTATION
# -----------------------------

def compute_metrics(predicted, actual):
    # Simulate rider travel time (real-world dispatch buffer)
    travel_time = np.random.normal(5, 1.5, len(predicted))  # avg 5 min travel
    
    # Platform dispatches rider BEFORE predicted ready time
    rider_dispatch_time = predicted - travel_time
    
    actual_ready_time = actual
    
    # Rider wait if arrives before food is ready
    wait_times = np.maximum(0, actual_ready_time - rider_dispatch_time)
    
    # Late arrival if rider reaches after food ready
    late_times = np.maximum(0, rider_dispatch_time - actual_ready_time)
    
    absolute_error = np.abs(predicted - actual)

    return {
        "avg_wait": np.mean(wait_times),
        "p50_error": np.percentile(absolute_error, 50),
        "p90_error": np.percentile(absolute_error, 90),
        "late_arrival_avg": np.mean(late_times),
        "idle_proxy": np.mean(wait_times)
    }

baseline_metrics = compute_metrics(baseline_kpt, true_kpt)
improved_metrics = compute_metrics(improved_kpt, true_kpt)

# -----------------------------
# 6️⃣ IMPROVEMENT %
# -----------------------------

def format_delta(value):
    if value is None:
        return ("N/A", "off")
    
    if value > 0:
        return (f"-{value:.1f}%", "inverse")  # green (improvement)
    elif value < 0:
        return (f"+{abs(value):.1f}%", "normal")  # red (worse)
    else:
        return ("0%", "off")

def pct(b, i, threshold=0.5):
    if b < threshold:
        return None
    
    improvement = ((b - i) / b) * 100
    return round(improvement, 2)

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

    wait_delta, wait_color = format_delta(wait_pct)
    p50_delta, p50_color = format_delta(p50_pct)
    p90_delta, p90_color = format_delta(p90_pct)
    idle_delta, idle_color = format_delta(idle_pct)

    st.metric("Avg Wait", round(improved_metrics["avg_wait"], 2),
              wait_delta, delta_color=wait_color)

    st.metric("P50 Error", round(improved_metrics["p50_error"], 2),
              p50_delta, delta_color=p50_color)

    st.metric("P90 Error", round(improved_metrics["p90_error"], 2),
              p90_delta, delta_color=p90_color)

    st.metric("Idle Proxy", round(improved_metrics["idle_proxy"], 2),
              idle_delta, delta_color=idle_color)
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

summary_text = f"""
SmartKPT Performance Gains:

• Rider Wait Time: {wait_delta}
• P50 ETA Error: {p50_delta}
• P90 ETA Error: {p90_delta}
• Rider Idle Time: {idle_delta}

Signal Improvements Introduced:
- Kitchen congestion modeling
- Equipment pressure signals
- Chef capacity constraints
- Live dine-in rush integration
- Bias reduction in merchant FOR marking
"""

st.success(summary_text)