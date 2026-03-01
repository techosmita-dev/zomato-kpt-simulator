import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("KPT Bias Simulation")

noise_ratio = st.slider("Noisy Merchant %", 0.0, 1.0, 0.4)

st.write("Simulation running...")

# (Your simulation code here)

st.success("Deployment works!")