import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# st.title("KPT Bias Simulation")

# noise_ratio = st.slider("Noisy Merchant %", 0.0, 1.0, 0.4)

# st.write("Simulation running...")

# # (Your simulation code here)

# st.success("Deployment works!")

def generate_merchants(n_merchants, noise_ratio):
    merchants = pd.DataFrame({
        "merchant_id": np.arange(n_merchants),
        "base_capacity": np.random.randint(5, 20, n_merchants),  # max parallel orders
        "chef_count": np.random.randint(1, 6, n_merchants),
        "bias_factor": np.where(
            np.random.rand(n_merchants) < noise_ratio,
            np.random.uniform(0.8, 1.2, n_merchants),  # noisy merchants
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

    # Simulate time across the day
    orders["order_time"] = [
        start_time + timedelta(minutes=int(np.random.uniform(0, 720)))
        for _ in range(n_orders)
    ]

    return orders

def simulate_prep_times(orders, merchants):

    orders = orders.merge(merchants, on="merchant_id")

    # Congestion proxy: random dynamic load
    orders["active_orders_at_time"] = np.random.poisson(5, len(orders))
    orders["rider_queue_count"] = np.random.poisson(3, len(orders))

    # True prep time formula
    orders["true_prep_time"] = (
        5
        + 2 * orders["items_count"]
        + 3 * orders["item_complexity_score"]
        + 1.5 * orders["active_orders_at_time"]
    )

    # True ready time
    orders["true_ready_time"] = (
        orders["order_time"]
        + pd.to_timedelta(orders["true_prep_time"], unit="m")
    )

    return orders

def simulate_merchant_for(orders):

    noise = np.random.normal(0, 3, len(orders))  # random error

    orders["merchant_FOR_time"] = (
        orders["true_ready_time"]
        + pd.to_timedelta(noise, unit="m")
        + pd.to_timedelta(
            orders["bias_factor"] * orders["rider_queue_count"], unit="m"
        )
    )

    return orders

noise_ratio = st.slider("Noisy Merchant %", 0.0, 1.0, 0.4)

merchants = generate_merchants(300, noise_ratio)
orders = generate_orders(15000, merchants)
orders = simulate_prep_times(orders, merchants)
orders = simulate_merchant_for(orders)

st.write("Generated Orders:", len(orders))