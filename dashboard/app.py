from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import DEFAULT_CONFIG, MqttConfig
from backend.mqtt_bridge import MqttBridge, topic
from backend.scenario_runner import SimulationRuntime
from backend.vehicle_simulator import SCENARIOS
from board_design.simulation.five_node_network_sim import simulate as simulate_five_node_network


st.set_page_config(page_title="ReLight-X Command Center", page_icon="RX", layout="wide")


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
              radial-gradient(circle at 12% 12%, rgba(34, 211, 238, 0.13), transparent 34%),
              linear-gradient(135deg, #061018 0%, #090d14 46%, #111827 100%);
            color: #e5f8ff;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(8, 13, 22, 0.98), rgba(10, 20, 32, 0.96));
            border-right: 1px solid rgba(125, 211, 252, 0.24);
        }
        .rx-card {
            border: 1px solid rgba(125, 211, 252, 0.26);
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(8, 47, 73, 0.45));
            border-radius: 8px;
            padding: 14px 16px;
            min-height: 96px;
            box-shadow: 0 0 28px rgba(14, 165, 233, 0.13);
        }
        .rx-label { color: #93c5fd; font-size: 0.78rem; text-transform: uppercase; letter-spacing: .04em; }
        .rx-value {
            color: #f8fafc;
            font-size: clamp(1.15rem, 1.8vw, 1.75rem);
            font-weight: 700;
            margin-top: 4px;
            overflow-wrap: anywhere;
            line-height: 1.15;
        }
        .rx-ok { color: #67e8f9; font-weight: 700; }
        .rx-bad { color: #fb7185; font-weight: 700; }
        .rx-warn { color: #facc15; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def service_status(host: str, port: int, timeout: float = 0.25) -> tuple[str, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "connected", "rx-ok"
    except OSError:
        return "offline", "rx-bad"


def card(label: str, value: str, detail: str = "") -> None:
    st.markdown(
        f"""
        <div class="rx-card">
          <div class="rx-label">{label}</div>
          <div class="rx-value">{value}</div>
          <div>{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def reset_runtime(scenario: str) -> None:
    previous = st.session_state.get("runtime")
    if previous is not None:
        previous.close()
    st.session_state.runtime = SimulationRuntime(scenario_name=scenario)
    st.session_state.scenario = scenario
    st.session_state.state = st.session_state.runtime.export_state()


def ensure_runtime() -> SimulationRuntime:
    scenario = st.sidebar.selectbox("Scenario", sorted(SCENARIOS), index=sorted(SCENARIOS).index("normal_car_direction_a"))
    if "runtime" not in st.session_state or st.session_state.get("scenario") != scenario:
        reset_runtime(scenario)
    return st.session_state.runtime


def step_runtime(runtime: SimulationRuntime, count: int) -> None:
    for _ in range(count):
        st.session_state.state = runtime.step()


def luminaires_df(state: dict) -> pd.DataFrame:
    lum = pd.DataFrame(state["luminaires"])
    poles = pd.DataFrame(state["poles"])[["pole_id", "position_x", "position_y", "position_z", "zone_id"]]
    df = lum.merge(poles, on="pole_id", how="left")
    df["map_y"] = df["direction"].map({"A": 7.4, "B": -7.4})
    df["brightness_pct"] = df["current_brightness"] * 100.0
    df["zone_direction"] = df["direction"] + "-" + df["zone_id"]
    return df


def zones_df(state: dict) -> pd.DataFrame:
    return pd.DataFrame(state["zones"])


def render_command_center(state: dict) -> None:
    energy = state.get("energy", {})
    system = state["system"]
    vehicles = pd.DataFrame(state["vehicles"])
    mqtt_state, mqtt_class = service_status("127.0.0.1", 1883)
    unity_state = "manual/live scene" if mqtt_state == "connected" else "standalone/offline"
    board_state = "hil ready" if mqtt_state == "connected" else "sim only"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Control mode", system["active_mode"], f"Emergency: {'yes' if system['emergency_active'] else 'no'}")
    with c2:
        card("Energy saved", f"{energy.get('energy_saved_pct', 0):.1f}%", f"{energy.get('co2_saved_kg', 0):.3f} kg CO2")
    with c3:
        card("MQTT broker", mqtt_state, f'<span class="{mqtt_class}">localhost:1883</span>')
    with c4:
        card("Twin/board link", unity_state, f"Board path: {board_state}")

    df = luminaires_df(state)
    fig = go.Figure()
    for direction, direction_df in df.groupby("direction"):
        fig.add_trace(
            go.Scatter3d(
                x=direction_df["position_x"],
                y=direction_df["map_y"],
                z=direction_df["brightness_pct"] / 8.0,
                mode="markers+lines",
                name=f"Luminaires {direction}",
                marker={
                    "size": direction_df["brightness_pct"] / 8.0,
                    "color": direction_df["brightness_pct"],
                    "colorscale": "Turbo",
                    "cmin": 30,
                    "cmax": 100,
                    "opacity": 0.92,
                },
                line={"width": 3},
                text=direction_df["luminaire_id"],
                hovertemplate="%{text}<br>brightness=%{marker.color:.1f}%<extra></extra>",
            )
        )
    if not vehicles.empty:
        vehicles["map_y"] = vehicles["lane_id"].map({"A1": 2.1, "A2": 5.8, "A3": 9.5, "B1": -2.1, "B2": -5.8, "B3": -9.5})
        vehicles["z"] = 2.2
        fig.add_trace(
            go.Scatter3d(
                x=vehicles["position_along_road"],
                y=vehicles["map_y"],
                z=vehicles["z"],
                mode="markers",
                name="Vehicles",
                marker={"size": 8, "color": vehicles["emergency_status"].map({True: "#ff2d55", False: "#38bdf8"})},
                text=vehicles["vehicle_id"] + " / " + vehicles["type"],
                hovertemplate="%{text}<br>x=%{x:.1f}m<extra></extra>",
            )
        )
    fig.update_layout(
        template="plotly_dark",
        height=610,
        margin={"l": 0, "r": 0, "t": 28, "b": 0},
        scene={
            "xaxis_title": "road position (m)",
            "yaxis_title": "lane side",
            "zaxis_title": "light output",
            "bgcolor": "rgba(2,6,23,0.20)",
            "camera": {"eye": {"x": 1.55, "y": -1.55, "z": 0.85}},
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        st.subheader("Process Pipeline")
        st.markdown(
            """
            `mmWave detection` -> `vehicle direction` -> `nearest pole` -> `sequential wave` -> `emergency override` -> `energy/health/passport telemetry`
            """
        )
        if system["active_faults"]:
            st.error(f"Active fault path: {system['active_faults']}")
        else:
            st.success("No active simulated faults in the current run.")
    with col_b:
        st.subheader("Connection Matrix")
        st.markdown(
            f"""
            - Backend runtime: <span class="rx-ok">running inside dashboard</span>
            - MQTT broker: <span class="{mqtt_class}">{mqtt_state}</span>
            - Unity digital twin: <span class="{'rx-ok' if mqtt_state == 'connected' else 'rx-warn'}">{unity_state}</span>
            - ESP32/Wokwi board: <span class="{'rx-ok' if mqtt_state == 'connected' else 'rx-warn'}">{board_state}</span>
            """,
            unsafe_allow_html=True,
        )


def render_overview(state: dict) -> None:
    energy = state.get("energy", {})
    system = state["system"]
    vehicles = state["vehicles"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active mode", system["active_mode"])
    c2.metric("Vehicles", len(vehicles))
    c3.metric("Adaptive kWh", f"{energy.get('actual_kwh', 0):.4f}")
    c4.metric("Energy saved", f"{energy.get('energy_saved_pct', 0):.1f}%")
    c5.metric("CO2 saved", f"{energy.get('co2_saved_kg', 0):.3f} kg")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        df = luminaires_df(state)
        fig = px.scatter(
            df,
            x="position_x",
            y="map_y",
            color="brightness_pct",
            symbol="direction",
            hover_data=["luminaire_id", "health_score", "fault_status", "rex_status"],
            color_continuous_scale="YlOrRd",
            range_color=[30, 100],
            height=380,
        )
        fig.update_layout(yaxis_title="Direction side", xaxis_title="Road position (m)")
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.subheader("Active Vehicles")
        st.dataframe(pd.DataFrame(vehicles), use_container_width=True, hide_index=True)
        st.subheader("Faults")
        st.json(system["active_faults"] or [{"status": "no active simulated faults"}])


def render_highway_map(state: dict) -> None:
    df = luminaires_df(state)
    st.subheader("6-Lane Highway Digital Twin State")
    fig = px.scatter(
        df,
        x="position_x",
        y="map_y",
        color="brightness_pct",
        size="brightness_pct",
        facet_row="direction",
        hover_data=["luminaire_id", "pole_id", "fault_status", "driver_temperature", "rex_status"],
        color_continuous_scale="Viridis",
        range_color=[30, 100],
        height=560,
    )
    fig.update_layout(xaxis_title="Road position (m)")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        df[["luminaire_id", "direction", "current_brightness", "target_brightness", "fault_status", "health_score", "rex_status"]],
        use_container_width=True,
        hide_index=True,
    )


def render_energy(state: dict) -> None:
    energy = state.get("energy", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Always-on baseline", f"{energy.get('baseline_kwh', 0):.4f} kWh")
    c2.metric("Adaptive mode", f"{energy.get('actual_kwh', 0):.4f} kWh")
    c3.metric("Saved", f"{energy.get('energy_saved_kwh', 0):.4f} kWh")
    per_zone = pd.DataFrame(
        [{"zone_id": key, "kwh": value} for key, value in energy.get("per_zone_kwh", {}).items()]
    )
    per_direction = pd.DataFrame(
        [{"direction": key, "kwh": value} for key, value in energy.get("per_direction_kwh", {}).items()]
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Per-Zone Energy")
        if not per_zone.empty:
            st.bar_chart(per_zone, x="zone_id", y="kwh")
    with col_b:
        st.subheader("Per-Direction Energy")
        if not per_direction.empty:
            st.bar_chart(per_direction, x="direction", y="kwh")


def render_health(state: dict) -> None:
    df = luminaires_df(state)
    sensors = pd.DataFrame(state["sensors"])
    st.subheader("Luminaire Health")
    st.dataframe(
        df.sort_values("health_score")[
            [
                "luminaire_id",
                "direction",
                "health_score",
                "driver_temperature",
                "current_consumption",
                "operating_hours",
                "fault_count",
                "fault_status",
                "rex_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Sensor Nodes")
    st.dataframe(sensors, use_container_width=True, hide_index=True)


def render_passport(state: dict) -> None:
    passports = {passport["luminaire_id"]: passport for passport in state["passports"]}
    selected = st.selectbox("Luminaire", sorted(passports))
    passport = passports[selected]
    c1, c2, c3 = st.columns(3)
    c1.metric("Health", f"{passport['health_score']:.1f}")
    c2.metric("RUL", f"{passport['remaining_useful_life_estimate']:.0f} h")
    c3.metric("Re-X", passport["rex_decision"])
    st.json(passport)


def render_board_test() -> None:
    st.subheader("Hardware-in-the-Loop Board Test")
    board_id = st.text_input("Board ID", "board-001")
    luminaire_id = st.text_input("Luminaire ID", "P001-A")
    brightness = st.slider("Brightness command", min_value=0, max_value=100, value=70, step=5) / 100.0
    host = st.text_input("MQTT host", "localhost")
    port = st.number_input("MQTT port", min_value=1, max_value=65535, value=1883)
    payload = {
        "board_id": board_id,
        "luminaire_id": luminaire_id,
        "brightness": brightness,
        "source": "streamlit_board_test",
        "safe_fallback_brightness": DEFAULT_CONFIG.safe_fallback_brightness,
    }
    command_topic = topic(DEFAULT_CONFIG.mqtt.base_topic, "board", board_id, "command")
    luminaire_topic = topic(DEFAULT_CONFIG.mqtt.base_topic, "luminaire", luminaire_id, "command")
    st.code(json.dumps({"topic": command_topic, "payload": payload}, indent=2), language="json")
    if st.button("Publish MQTT Command"):
        mqtt_config = MqttConfig(host=host, port=int(port), enabled=True, client_id="relightx-dashboard")
        bridge = MqttBridge(mqtt_config)
        if bridge.connect():
            bridge.publish_json(command_topic, payload)
            bridge.publish_json(luminaire_topic, payload)
            bridge.stop()
            st.success("Command published.")
        else:
            st.warning("MQTT broker not connected; payload is shown above for manual/HIL testing.")


def render_board_network() -> None:
    st.subheader("Five-Node Board Network")
    st.caption("STM32 pole nodes with wireless gateway plus RS485/CAN footprints. Values are simulated for architecture validation.")

    steps = st.slider("Simulation steps", min_value=10, max_value=60, value=30, step=5)
    result = simulate_five_node_network(steps=steps, dt_s=1.0)
    record_labels = [f"{record['time_s']:04.1f}s / vehicle {record['vehicle_x_m']:05.1f}m" for record in result["records"]]
    selected_label = st.select_slider("Network time", options=record_labels, value=record_labels[min(len(record_labels) - 1, 12)])
    record = result["records"][record_labels.index(selected_label)]
    nodes = pd.DataFrame(record["nodes"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Board nodes", f"{len(nodes)}")
    c2.metric("Wireless online", f"{record['gateway']['wireless_nodes_online']}/5")
    c3.metric("Active faults", f"{len(record['gateway']['active_faults'])}")
    c4.metric("Vehicle position", f"{record['vehicle_x_m']:.1f} m")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=nodes["x_m"],
            y=nodes["target_brightness"] * 100.0,
            mode="lines+markers+text",
            text=nodes["node_id"],
            textposition="top center",
            marker={
                "size": 18,
                "color": nodes["target_brightness"] * 100.0,
                "colorscale": "YlOrRd",
                "cmin": 30,
                "cmax": 100,
            },
            line={"width": 4, "color": "rgba(56,189,248,0.55)"},
            hovertemplate="%{text}<br>x=%{x:.1f}m<br>brightness=%{y:.0f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[record["vehicle_x_m"]],
            y=[108],
            mode="markers+text",
            text=["vehicle"],
            textposition="bottom center",
            marker={"size": 16, "color": "#38bdf8", "symbol": "diamond"},
            name="Vehicle",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=360,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        xaxis_title="Pole position (m)",
        yaxis_title="Target brightness (%)",
        yaxis_range=[20, 115],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,6,23,0.35)",
    )
    st.plotly_chart(fig, use_container_width=True)

    display = nodes[
        [
            "node_id",
            "pole_id",
            "luminaire_id",
            "vehicle_detected",
            "ambient_lux",
            "driver_temp_c",
            "current_ma",
            "target_brightness",
            "wireless_rssi_dbm",
            "rs485_ok",
            "can_ok",
            "fault",
            "event",
        ]
    ].copy()
    display["target_brightness"] = (display["target_brightness"] * 100.0).round(0).astype(int).astype(str) + "%"
    st.dataframe(display, use_container_width=True, hide_index=True)

    map_path = ROOT / "board_design" / "five_node_board_map.csv"
    if map_path.exists():
        st.subheader("Board Map")
        st.dataframe(pd.read_csv(map_path), use_container_width=True, hide_index=True)


apply_theme()
runtime = ensure_runtime()

st.sidebar.divider()
if st.sidebar.button("Step 1 second"):
    step_runtime(runtime, 1)
if st.sidebar.button("Run 10 seconds"):
    step_runtime(runtime, 10)
if st.sidebar.button("Run 60 seconds"):
    step_runtime(runtime, 60)
if st.sidebar.button("Reset scenario"):
    reset_runtime(st.session_state.scenario)

page = st.sidebar.radio(
    "Page",
    ["Command Center", "Overview", "Highway Map", "Energy", "Health", "Digital Passport", "Board Network", "Board Test"],
)

state = st.session_state.state
st.title("ReLight-X: Emergency-Aware Adaptive Highway Lighting")
st.caption(f"Scenario: {state['scenario']} | Simulation time: {state['time_s']:.1f} s | Data are simulated for a research prototype.")

if page == "Command Center":
    render_command_center(state)
elif page == "Overview":
    render_overview(state)
elif page == "Highway Map":
    render_highway_map(state)
elif page == "Energy":
    render_energy(state)
elif page == "Health":
    render_health(state)
elif page == "Digital Passport":
    render_passport(state)
elif page == "Board Network":
    render_board_network()
else:
    render_board_test()
