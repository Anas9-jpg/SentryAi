import math
import time
import folium
from geopy.distance import geodesic
from streamlit_folium import st_folium
import streamlit as st

# ============================================================
# SentryAI
# AI Early Warning & Trajectory Risk Assessment
# Automatic Simulation Version
# ============================================================

st.set_page_config(
    page_title="SentryAI - Early Warning System",
    layout="wide"
)


# ============================================================
# Session State
# ============================================================

if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False

if "simulation_step" not in st.session_state:
    st.session_state.simulation_step = 0

if "last_alert_type" not in st.session_state:
    st.session_state.last_alert_type = None


# ============================================================
# Main Header
# ============================================================

st.title("🛡️ SentryAI")
st.subheader("AI Early Warning & Trajectory Risk Assessment")
st.caption(
    "Target trajectory analysis and proximity prediction for critical infrastructure"
)

st.markdown("---")


# ============================================================
# Facility Configuration
# ============================================================

FACILITY_LOCATION = [24.5534, 39.7051]

# Coverage Zones (meters)
SENSOR_COVERAGE_M = 5000
WARNING_RADIUS_M = 1000
CRITICAL_RADIUS_M = 300


# ============================================================
# Control Panel
# ============================================================

st.sidebar.header("⚙️ Simulation Control")

threat_type = st.sidebar.selectbox(
    "Target Type:",
    ["Drone", "Vehicle", "Pedestrian"],
)


# ============================================================
# Speed Settings
# ============================================================

speed_map_kmh = {
    "Drone": 72.0,
    "Vehicle": 54.0,
    "Pedestrian": 7.2,
}

speed_kmh = speed_map_kmh[threat_type]
speed_m_s = speed_kmh / 3.6


# ============================================================
# Automatic Simulation Controls
# ============================================================

st.sidebar.markdown("---")
st.sidebar.subheader("🎮 Automatic Simulation")

run_simulation = st.sidebar.button(
    "▶️ Run Simulation",
    use_container_width=True,
    type="primary"
)

reset_simulation = st.sidebar.button(
    "🔄 Reset Simulation",
    use_container_width=True
)

if reset_simulation:
    st.session_state.simulation_running = False
    st.session_state.simulation_step = 0
    st.session_state.last_alert_type = None
    st.rerun()

if run_simulation:
    st.session_state.simulation_running = True
    st.session_state.simulation_step = 0
    st.session_state.last_alert_type = None


# ============================================================
# Simulation Speed
# ============================================================

simulation_speed = st.sidebar.select_slider(
    "⏱️ Step Interval",
    options=[1, 2, 3, 4, 5],
    value=2,
    format_func=lambda x: f"{x} seconds"
)


# ============================================================
# Simulated Path Coordinates
# Starts Outside 5 km Coverage
# ============================================================

simulated_path = [
    [24.5950, 39.7500],  # Step 0: Outside 5 km coverage
    [24.5800, 39.7350],  # Step 1: Entering 5 km Sensor Coverage
    [24.5680, 39.7200],  # Step 2: Approaching Warning Zone
    [24.5580, 39.7100],  # Step 3: Entering Warning Zone
    [24.5550, 39.7070],  # Step 4: Entering Critical Zone
    [24.5538, 39.7055],  # Step 5: Reaching Facility Center
]


# ============================================================
# Current Simulation Step
# ============================================================

step = st.session_state.simulation_step

target_location = simulated_path[step]


# ============================================================
# Path Segment Calculations
# ============================================================

segment_distances = []

for i in range(len(simulated_path) - 1):

    distance = geodesic(
        simulated_path[i],
        simulated_path[i + 1]
    ).meters

    segment_distances.append(distance)


segment_times = []

for distance in segment_distances:

    segment_time = (
        distance / speed_m_s
        if speed_m_s > 0
        else 0
    )

    segment_times.append(segment_time)


cumulative_time = [0.0]

for segment_time in segment_times:

    cumulative_time.append(
        cumulative_time[-1] + segment_time
    )


# ============================================================
# Current Distance
# ============================================================

distance_meters = geodesic(
    FACILITY_LOCATION,
    target_location
).meters


# ============================================================
# Bearing & Angle Calculations
# ============================================================

def calculate_bearing(point_a, point_b):

    lat1 = math.radians(point_a[0])
    lat2 = math.radians(point_b[0])

    delta_longitude = math.radians(
        point_b[1] - point_a[1]
    )

    y = (
        math.sin(delta_longitude)
        * math.cos(lat2)
    )

    x = (
        math.cos(lat1)
        * math.sin(lat2)
        -
        math.sin(lat1)
        * math.cos(lat2)
        * math.cos(delta_longitude)
    )

    bearing = math.degrees(
        math.atan2(y, x)
    )

    return (bearing + 360) % 360


if step < len(simulated_path) - 1:

    next_location = simulated_path[step + 1]

    movement_bearing = calculate_bearing(
        target_location,
        next_location
    )

else:

    movement_bearing = calculate_bearing(
        simulated_path[-2],
        simulated_path[-1]
    )


facility_bearing = calculate_bearing(
    target_location,
    FACILITY_LOCATION
)


angle_difference = abs(
    movement_bearing - facility_bearing
)

if angle_difference > 180:

    angle_difference = 360 - angle_difference


# ============================================================
# Closing Speed
# ============================================================

angle_radians = math.radians(
    angle_difference
)

closing_speed_m_s = (
    speed_m_s
    * math.cos(angle_radians)
)

closing_speed_kmh = (
    closing_speed_m_s * 3.6
)


# ============================================================
# Accurate ETA Calculation
# ============================================================

if closing_speed_m_s > 0:

    eta_to_facility_seconds = (
        distance_meters
        / closing_speed_m_s
    )

else:

    eta_to_facility_seconds = float("inf")


# ETA to Critical Zone

distance_to_critical_zone = max(
    distance_meters - CRITICAL_RADIUS_M,
    0
)


if closing_speed_m_s > 0:

    critical_breach_seconds = (
        distance_to_critical_zone
        / closing_speed_m_s
    )

else:

    critical_breach_seconds = float("inf")


# ============================================================
# Format Time Function
# ============================================================

def format_time(seconds):

    if not math.isfinite(seconds):

        return "N/A"

    total_seconds = max(
        0,
        int(round(seconds))
    )

    minutes = total_seconds // 60

    remaining_seconds = (
        total_seconds % 60
    )

    if minutes > 0:

        return (
            f"{minutes}m "
            f"{remaining_seconds}s"
        )

    return f"{remaining_seconds}s"


eta_text = format_time(
    eta_to_facility_seconds
)

critical_eta_text = format_time(
    critical_breach_seconds
)


# ============================================================
# 60s Predictive Analysis
# ============================================================

prediction_seconds = 60

if closing_speed_m_s > 0:

    predicted_distance = max(
        distance_meters
        -
        (
            closing_speed_m_s
            * prediction_seconds
        ),
        0
    )

    predicted_label = (
        f"Distance in "
        f"{prediction_seconds}s"
    )

    predicted_distance_display = (
        f"{predicted_distance:,.0f} m"
    )

    will_impact_before_window = (
        eta_to_facility_seconds
        <= prediction_seconds
    )

else:

    predicted_label = (
        f"Distance in "
        f"{prediction_seconds}s"
    )

    predicted_distance_display = (
        f"{distance_meters:,.0f} m"
    )

    will_impact_before_window = False


# ============================================================
# Zone-Based Status & Alert Logic
# ============================================================

# ------------------------------------------------------------
# 1. Outside Sensor Coverage
# ------------------------------------------------------------

if distance_meters > SENSOR_COVERAGE_M:

    threat_status = "SAFE 🟢"

    status_color = "green"

    risk_score = 0

    risk_level = (
        "Safe — Target is outside coverage zone"
    )

    action_recommendation = (
        "No threat detected within 5km perimeter. "
        "System in standby mode."
    )

    alert_type = "safe"


# ------------------------------------------------------------
# 2. Sensor Coverage
# ------------------------------------------------------------

elif distance_meters > WARNING_RADIUS_M:

    zone_fraction = 1 - (
        (
            distance_meters
            - WARNING_RADIUS_M
        )
        /
        (
            SENSOR_COVERAGE_M
            - WARNING_RADIUS_M
        )
    )

    base_score = 30 * zone_fraction

    risk_score = min(
        40,
        base_score
        +
        (
            10
            if angle_difference <= 45
            else 0
        )
    )

    threat_status = "MONITORING 🔵"

    status_color = "blue"

    risk_level = (
        "Detected — Target entered "
        "5km sensor perimeter"
    )

    action_recommendation = (
        "Target detected on radar. "
        "Active trajectory tracking in progress."
    )

    alert_type = "info"


# ------------------------------------------------------------
# 3. Warning Zone
# ------------------------------------------------------------

elif distance_meters > CRITICAL_RADIUS_M:

    zone_fraction = 1 - (
        (
            distance_meters
            - CRITICAL_RADIUS_M
        )
        /
        (
            WARNING_RADIUS_M
            - CRITICAL_RADIUS_M
        )
    )

    risk_score = (
        40
        +
        30 * zone_fraction
    )

    threat_status = "WARNING 🟡"

    status_color = "orange"

    risk_level = (
        "Warning — Target breached "
        "1000m Warning Zone!"
    )

    action_recommendation = (
        "WARNING: Target approaching rapidly. "
        "Notify security personnel and prepare response."
    )

    alert_type = "warning"


# ------------------------------------------------------------
# 4. Critical Zone
# ------------------------------------------------------------

else:

    threat_status = "CRITICAL 🔴"

    status_color = "red"

    risk_score = 100

    risk_level = (
        "CRITICAL THREAT — Target breached "
        "300m Critical Perimeter!"
    )

    action_recommendation = (
        "CRITICAL ALERT: Target inside critical perimeter! "
        "Initiate immediate countermeasures!"
    )

    alert_type = "error"


# ============================================================
# Main Top Metrics
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "System Status",
        threat_status
    )


with col2:

    st.metric(
        "Distance",
        f"{distance_meters:,.1f} m"
    )


with col3:

    st.metric(
        "ETA to Center",
        eta_text
    )


with col4:

    st.metric(
        "Risk Score",
        f"{risk_score:.0f}/100"
    )


# ============================================================
# Simulation Progress
# ============================================================

st.markdown("---")

progress_value = (
    step /
    (len(simulated_path) - 1)
)

st.write(
    f"**Simulation Progress:** "
    f"Step {step + 1} / {len(simulated_path)}"
)

st.progress(
    progress_value
)


if st.session_state.simulation_running:

    st.info(
        "▶️ Simulation Running — "
        "SentryAI is automatically analyzing the target trajectory..."
    )

else:

    if step == len(simulated_path) - 1:

        st.success(
            "✅ Simulation Completed — "
            "Target reached the final trajectory point."
        )

    else:

        st.caption(
            "Press ▶️ Run Simulation to start the automatic trajectory simulation."
        )


# ============================================================
# Visual Status Alert Banners & Toasts
# ============================================================

status_changed = (
    st.session_state.last_alert_type
    != alert_type
)

st.session_state.last_alert_type = alert_type


if alert_type == "safe":

    st.success(
        "🟢 STATUS NORMAL: "
        "Perimeter Clear — No Threat Detected"
    )

    if status_changed:

        st.toast(
            "🟢 Area Secure: "
            "Target outside coverage zone.",
            icon="✅"
        )


elif alert_type == "info":

    st.info(
        f"🔵 TARGET DETECTED: "
        f"Target detected at "
        f"{distance_meters:,.0f}m — "
        f"Tracking Trajectory..."
    )

    if status_changed:

        st.toast(
            f"🔵 TARGET DETECTED: "
            f"Distance {distance_meters:,.0f}m — "
            f"Tracking...",
            icon="📡"
        )


elif alert_type == "warning":

    st.warning(
        f"⚠️ WARNING ALERT: "
        f"Target entered 1km Warning Zone! "
        f"(Distance: {distance_meters:,.0f}m | "
        f"ETA to Critical: {critical_eta_text})"
    )

    if status_changed:

        st.toast(
            f"⚠️ WARNING: "
            f"Target breached 1km Zone! "
            f"(ETA: {critical_eta_text})",
            icon="⚠️"
        )


elif alert_type == "error":

    st.error(
        f"🚨 CRITICAL ALARM: "
        f"Target breached 300m Critical Zone! "
        f"(Distance: {distance_meters:,.0f}m)"
    )

    if status_changed:

        st.toast(
            f"🚨 CRITICAL ALARM: "
            f"Target in 300m Perimeter! "
            f"({distance_meters:,.0f}m)",
            icon="🚨"
        )


# ============================================================
# Target Kinematics
# ============================================================

st.markdown("---")

st.subheader("📊 Target Kinematics")


kin1, kin2, kin3, kin4 = st.columns(4)


with kin1:

    st.write(
        f"**Current Speed:** "
        f"{speed_kmh:.1f} km/h"
    )


with kin2:

    st.write(
        f"**Closing Speed:** "
        f"{closing_speed_kmh:.1f} km/h"
    )


with kin3:

    st.write(
        f"**Heading:** "
        f"{movement_bearing:.1f}°"
    )


with kin4:

    st.write(
        f"**Approach Angle:** "
        f"{angle_difference:.1f}°"
    )


# ============================================================
# Predictive Analysis
# ============================================================

st.markdown("---")

st.subheader("🔮 Predictive Analysis")


pred1, pred2, pred3 = st.columns(3)


with pred1:

    st.metric(
        predicted_label,
        predicted_distance_display
    )

    if will_impact_before_window:

        st.caption(
            f"⚠️ Facility reached in "
            f"{int(round(eta_to_facility_seconds))}s "
            f"(before the "
            f"{prediction_seconds}s window ends)"
        )


with pred2:

    st.metric(
        f"ETA to Critical Zone "
        f"({int(CRITICAL_RADIUS_M)}m)",
        critical_eta_text
    )


with pred3:

    st.metric(
        "Simulation Time",
        f"{cumulative_time[step]:.1f} s"
    )


# Risk Progress Bar

st.progress(
    min(
        max(
            int(risk_score),
            0
        ),
        100
    )
)


# ============================================================
# Map & Assessment Column
# ============================================================

st.markdown("---")


# ============================================================
# Map Zoom
# ============================================================

_zoom_by_radius = [
    (2000, 14),
    (5000, 13),
    (10000, 12),
    (20000, 11),
    (50000, 10),
]


map_zoom = next(
    (
        z
        for r, z in _zoom_by_radius
        if SENSOR_COVERAGE_M <= r
    ),
    9
)


# ============================================================
# Create Map
# ============================================================

m = folium.Map(
    location=FACILITY_LOCATION,
    zoom_start=map_zoom,
    tiles="OpenStreetMap"
)


# ============================================================
# Sensor Coverage
# ============================================================

folium.Circle(
    location=FACILITY_LOCATION,
    radius=SENSOR_COVERAGE_M,
    color="blue",
    fill=False,
    weight=2,
    popup="Sensor Coverage — 5 km (Simulation)",
).add_to(m)


# ============================================================
# Warning Zone
# ============================================================

folium.Circle(
    location=FACILITY_LOCATION,
    radius=WARNING_RADIUS_M,
    color="orange",
    fill=True,
    fill_opacity=0.10,
    popup="Warning Zone — 1000 m",
).add_to(m)


# ============================================================
# Critical Zone
# ============================================================

folium.Circle(
    location=FACILITY_LOCATION,
    radius=CRITICAL_RADIUS_M,
    color="red",
    fill=True,
    fill_opacity=0.15,
    popup="Critical Zone — 300 m",
).add_to(m)


# ============================================================
# Facility Marker
# ============================================================

folium.Marker(
    FACILITY_LOCATION,
    popup="<b>SentryAI Protected Facility</b>",
    icon=folium.Icon(
        color="blue",
        icon="shield",
        prefix="fa"
    ),
).add_to(m)


# ============================================================
# Observed Trajectory
# ============================================================

folium.PolyLine(
    simulated_path,
    color="darkblue",
    weight=4,
    opacity=0.8,
    popup="Observed Target Trajectory",
).add_to(m)


# ============================================================
# Trajectory Points
# ============================================================

for i, point in enumerate(simulated_path):

    # Make current point visually larger
    if i == step:

        folium.CircleMarker(
            location=point,
            radius=8,
            color="red",
            fill=True,
            fill_opacity=1,
            popup=f"Current Position — Step {i + 1}",
        ).add_to(m)

    else:

        folium.CircleMarker(
            location=point,
            radius=5,
            color="black",
            fill=True,
            fill_opacity=1,
            popup=f"Trajectory Point {i + 1}",
        ).add_to(m)


# ============================================================
# Current Target Marker
# ============================================================

folium.Marker(
    target_location,
    popup=f"""
    <b>{threat_type}</b><br>
    Step: {step + 1}<br>
    Distance: {distance_meters:,.1f} m<br>
    Speed: {speed_kmh:.1f} km/h<br>
    Closing Speed: {closing_speed_kmh:.1f} km/h<br>
    Heading: {movement_bearing:.1f}°<br>
    Risk Score: {risk_score:.0f}/100
    """,
    icon=folium.Icon(
        color=status_color,
        icon="crosshairs",
        prefix="fa"
    ),
).add_to(m)


# ============================================================
# Map & Information
# ============================================================

col_map, col_info = st.columns([2, 1])


with col_map:

    st_folium(
        m,
        width=750,
        height=500,
        returned_objects=[]
    )


with col_info:

    st.subheader(
        "📋 SentryAI Assessment"
    )

    st.write(
        f"**Target:** {threat_type}"
    )

    st.write(
        f"**Status:** {threat_status}"
    )

    st.write(
        f"**Risk Score:** "
        f"{risk_score:.0f}/100"
    )

    st.write(
        f"**Distance:** "
        f"{distance_meters:,.1f} m"
    )

    st.write(
        f"**Speed:** "
        f"{speed_kmh:.1f} km/h"
    )

    st.write(
        f"**Closing Speed:** "
        f"{closing_speed_kmh:.1f} km/h"
    )

    st.write(
        f"**Approach Angle:** "
        f"{angle_difference:.1f}°"
    )

    st.write(
        f"**ETA to Center:** "
        f"{eta_text}"
    )

    st.write(
        f"**ETA to Critical Zone "
        f"({int(CRITICAL_RADIUS_M)}m):** "
        f"{critical_eta_text}"
    )

    st.write(
        f"**Risk Assessment:** "
        f"{risk_level}"
    )

    st.info(
        f"**Decision Support:**\n\n"
        f"{action_recommendation}"
    )


    # ========================================================
    # ETA Calculation Breakdown
    # ========================================================

    with st.expander(
        "🔎 ETA Calculation Breakdown"
    ):

        st.write(
            f"Approach Speed: "
            f"{closing_speed_kmh:.2f} km/h"
        )

        st.write(
            f"Approach Speed: "
            f"{closing_speed_m_s:.2f} m/s"
        )

        st.write(
            f"Current Distance: "
            f"{distance_meters:.1f} m"
        )

        st.write(
            f"Distance to Critical Zone: "
            f"{distance_to_critical_zone:.1f} m"
        )

        st.code(
            f"""
ETA Center =
{distance_meters:.1f} ÷ {closing_speed_m_s:.2f}
= {eta_to_facility_seconds:.1f} seconds

ETA Critical Zone =
{distance_to_critical_zone:.1f} ÷ {closing_speed_m_s:.2f}
= {critical_breach_seconds:.1f} seconds
"""
        )


# ============================================================
# How SentryAI Works
# ============================================================

st.markdown("---")

st.subheader(
    "🧠 How SentryAI Works"
)

st.markdown(
    """
    **1. Detect** → Receive target stream data from connected sensors.  
    **2. Track** → Track position, velocity, and movement bearing.  
    **3. Analyze** → Evaluate distance, closing speed, and approach angle.  
    **4. Predict** → Forecast future target position and critical zone breach.  
    **5. Assess** → Compute dynamic threat risk score.  
    **6. Alert** → Provide actionable operator decision support.  
    """
)


# ============================================================
# Footer
# ============================================================

st.markdown("---")

st.caption(
    "Prototype Simulation — Current metrics are calculated from "
    "simulated coordinates and speed. Future builds will integrate "
    "Radar / Camera / Thermal Sensor feeds."
)


# ============================================================
# AUTOMATIC SIMULATION ENGINE
# ============================================================

if st.session_state.simulation_running:

    if st.session_state.simulation_step < len(simulated_path) - 1:

        time.sleep(simulation_speed)

        st.session_state.simulation_step += 1

        st.rerun()

    else:

        st.session_state.simulation_running = False
