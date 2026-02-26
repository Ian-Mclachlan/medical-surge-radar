# Updated for FIFA 2026 Surge Planning
import streamlit as st
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Regional Medical Surge Radar", layout="wide")

# --- CORE LOGIC & SIMULATION VARIABLES ---
# In production, these variables will be fed by your Arbon/Baird equations and NotebookLM data.
BASELINE_ED_CAPACITY = 80 # The absolute number of transports the regional ED grid can handle before critical failure.
CRITICAL_NEDOCS_THRESHOLD = 140 # Score representing "Disaster" level overcrowding.

# --- SIDEBAR: DYNAMIC INPUTS ---
st.sidebar.header("Scenario Parameters")
attendance = st.sidebar.slider("Attendance Volume", min_value=10000, max_value=150000, value=65000, step=5000)
temp = st.sidebar.slider("Temperature (°F)", min_value=60, max_value=120, value=85, step=1)
humidity = st.sidebar.slider("Humidity (%)", min_value=10, max_value=100, value=60, step=5)
venue_type = st.sidebar.radio("Venue Type", ["Stadium (Bounded)", "Fan Zone (Unbounded)"])

# --- CALCULATIONS (Epidemiologically Validated Proxy) ---
# Based on Arbon/Baird Mass Gathering Medicine models

# 1. Patient Presentation Rate (PPR)
# Base PPR for standard bounded events is typically ~15 per 10,000 attendees
base_ppr_per_10k = 15.0 

# 2. Environmental & Venue Multipliers
# Heat heavily drives casualty rates. Combining Temp & Humidity proxies the Heat Index
heat_index_multiplier = 1.0 + max(0, (temp - 85) * 0.05) + max(0, (humidity - 60) * 0.01)

# Unbounded fan zones have higher substance use, mobility, and less crowd control
venue_multiplier = 2.0 if venue_type == "Fan Zone (Unbounded)" else 1.0

# 3. Total Patient Generation
total_patients = int((attendance / 10000) * base_ppr_per_10k * heat_index_multiplier * venue_multiplier)

# 4. Asset Distribution (Transport to Hospital Rate - TTHR)
# Mass gathering literature dictates ~15-20% of presentations require ED transport
onsite_treat = int(total_patients * 0.65)         # 65% treated/released at Main First Aid
acs_telehealth = int(total_patients * 0.15)       # 15% deflected to Alternate Care Sites
ed_transports = total_patients - onsite_treat - acs_telehealth # Remaining 20% hit the grid

# 5. Dynamic NEDOCS Simulation
# NEDOCS scales based on incoming transports relative to the grid's baseline capacity.
# If transports hit 100% of baseline capacity (80 patients), NEDOCS increases by 60 points.
surge_burden = (ed_transports / BASELINE_ED_CAPACITY) * 60
nedocs_score = int(80 + surge_burden) # Assuming 80 is the normal, resting operational baseline


nedocs_score = min(nedocs_score, 200) # Cap at 200

# --- DASHBOARD HEADER ---
st.title("FIFA 2026: Medical Surge Radar")
st.markdown("### Operational Threat Level & Asset Distribution")

# --- SYSTEM WARNING ALERTS ---
# This is the psychological trigger: screaming at the user when 5% away from disaster
warning_threshold = CRITICAL_NEDOCS_THRESHOLD * 0.95

# --- SYSTEM WARNING ALERTS & BREAKING POINTS ---
# Prioritized logic to prevent conflicting UI messages

if temp >= 98:
    st.error("""
        🚨 **CRITICAL OVERRIDE: Heat-Casualty Threshold Exceeded.** Sustained temperatures at or above 98°F indicate imminent physical capacity collapse across local Emergency Departments. Initiate regional deflection protocols immediately.
    """)
elif nedocs_score >= CRITICAL_NEDOCS_THRESHOLD:
    st.error(f"🚨 **SYSTEM FAILURE IMMINENT:** NEDOCS Score {nedocs_score}. Acute care grid saturated. Implement Tier 4 Diversion immediately.")
elif nedocs_score >= warning_threshold:
    st.warning("⚠️ **CRITICAL WARNING:** System is < 5% away from operational breaking point. Prepare Alternate Care Site overflow.")
else:
    st.success("✅ System Operating Within Conventional Capacity Constraints.")

st.markdown("---")

# --- VISUALIZATIONS ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("Regional NEDOCS Threat Level")
    # Dynamic Gauge Chart
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = nedocs_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "NEDOCS Score", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [None, 200], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 80], 'color': "green"},
                {'range': [80, 100], 'color': "yellow"},
                {'range': [100, 140], 'color': "orange"},
                {'range': [140, 200], 'color': "red"}],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': CRITICAL_NEDOCS_THRESHOLD}
        }
    ))
    fig_gauge.update_layout(height=400)
    st.plotly_chart(fig_gauge, use_container_width=True)

with col2:
    st.subheader("Asset Distribution Waterfall")
    # Waterfall Chart showing how the patient load is leveled across assets
    fig_waterfall = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["absolute", "relative", "relative", "relative"],
        x = ["Total Generated", "On-Site (STIP)", "ACS / Telehealth", "ED Transports"],
        textposition = "outside",
        text = [str(total_patients), f"-{onsite_treat}", f"-{acs_telehealth}", str(ed_transports)],
        y = [total_patients, -onsite_treat, -acs_telehealth, ed_transports],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#1f77b4"}},
        totals = {"marker":{"color":"#d62728"}}
    ))
    fig_waterfall.update_layout(
        title = "Patient Flow & Deflection Strategy",
        showlegend = False,
        height=400,
        yaxis_title="Patient Volume"
    )

    st.plotly_chart(fig_waterfall, use_container_width=True)
