# 🍽️ SmartKPT — Signal-Enriched Kitchen Intelligence

SmartKPT is a simulation-driven prototype designed to improve **Kitchen Prep Time (KPT) prediction** for food delivery platforms by strengthening upstream kitchen signals instead of replacing the core prediction model.

It focuses on reducing:

- 🚴 Rider wait time  
- 📉 P50 / P90 ETA error  
- ⏳ Rider idle time  
- 🔄 Dispatch instability  

---

## 🚨 Problem Statement

Kitchen Prep Time prediction heavily relies on merchant-marked **Food Order Ready (FOR)** signals.

However, these signals are often:

- Influenced by rider-triggered marking  
- Affected by manual inconsistencies  
- Blind to dine-in and competitor order load  
- Unaware of chef or equipment bottlenecks  

This leads to:

Inaccurate KPT → Early Rider Dispatch → Rider Waiting → Idle Time → ETA Revisions → Customer Dissatisfaction → Increased Platform Cost

At marketplace scale, even small prediction errors compound significantly.

---

## 💡 Solution Overview

SmartKPT improves upstream signal quality through a **Signal Enrichment Layer** that enhances prediction inputs before they reach the model.

Instead of retraining the core KPT model, it introduces:

### 🔹 1. Kitchen Load Modeling
Active Orders / (Chefs + Equipments)

### 🔹 2. Chef Availability Signal
Shift-based staff strength integration.

### 🔹 3. Equipment Utilization Signal
Captures fryers, burners, ovens, and prep station capacity.

### 🔹 4. Live Dine-In Load Modeling
Models congestion beyond platform-visible orders.

### 🔹 5. Log-Based Congestion Penalty
Non-linear overload adjustment under stress conditions.

### 🔹 6. Bias Correction Layer
Reduces rider-triggered and late-marking patterns from merchant FOR signals.

---

## 🧪 Simulation Framework

Since no real dataset was provided, a controlled simulation environment was built using:

- Batch-based order inflow
- Capacity-constrained queue modeling
- Merchant bias patterns
- Rider dispatch timing logic
- Percentile-based ETA error evaluation

The Streamlit app allows real-time configuration of:

- Number of incoming orders  
- Average dish time  
- Chef count  
- Equipment count  
- Dine-in load  
- Peak hour intensity  

---

## 📊 Evaluation Metrics

SmartKPT is evaluated using:

- Average Rider Wait Time  
- P50 ETA Error  
- P90 ETA Error  
- Rider Idle Time Proxy  

Under high-load conditions, SmartKPT demonstrates:

- Reduced ETA variance  
- Lower tail-risk error (P90)  
- Better dispatch alignment  
- Improved system stability  

---

## 🏗 Architecture Flow

Enriched Kitchen Signals  
→ Bias Correction  
→ KPT Prediction  
→ Rider Assignment  
→ Stable ETA  

The architecture is modular and backward-compatible with existing prediction systems.

---

## 📈 Scalability Strategy (300K+ Merchants)

### Tier 1 — Small Restaurants
- Manual staff input
- Lightweight congestion estimation

### Tier 2 — Mid-Scale Restaurants
- Real-time chef scheduling integration
- Equipment tagging

### Tier 3 — Large Chains
- Smart kitchen sensors
- Equipment telemetry integration

---

## 🖥 Live Demo

Streamlit Simulator:  
👉 https://kptsimulator.streamlit.app/

---

## 📦 Repository Structure

```
smartKPT/
│
├── app.py                 # Streamlit simulation dashboard
├── simulation_logic.py    # Core KPT and bias modeling
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Run Locally

Clone the repository:

```
git clone https://github.com/techosmita-dev/zomato-kpt-simulator.git
cd zomato-kpt-simulator
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the app:

```
streamlit run app.py
```

---

## 🎯 Why This Approach Is Different

Most solutions focus on building better prediction models.

SmartKPT focuses on:

- Improving input signal quality  
- Modeling human marking behavior  
- Incorporating cross-channel kitchen congestion  
- Providing scalable, implementation-ready architecture  

It is operationally grounded and deployable without major retraining.

---

## 📌 Key Takeaways

- Small upstream signal improvements create large downstream impact  
- Congestion-aware dispatch reduces rider idle cost  
- Bias correction stabilizes ETA distribution  
- Scalable architecture across heterogeneous merchant ecosystem  

---

## 👩‍💻 Author

Techosmita  
GitHub: https://github.com/techosmita-dev
