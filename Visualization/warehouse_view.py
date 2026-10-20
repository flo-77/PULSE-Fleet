import time
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

FLEET_STATE_FILE = Path(__file__).parent / "fleet_state.json"
ROBOT_TIMEOUT = 3.0

def load_fleet_states():
    try:
        with FLEET_STATE_FILE.open("r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

fig, ax = plt.subplots(figsize=(10, 7))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)

warehouse_boundary = Rectangle(
    (0, 0),
    20,
    14,
    linewidth=2,
    edgecolor='black',
    facecolor='whitesmoke'
)

ax.add_patch(warehouse_boundary)

shelf_1 = Rectangle(
    (3, 3),
    1.5,
    8,
    facecolor='slategray',
    edgecolor='black'
)

ax.add_patch(shelf_1)

for x in [7, 11, 15]:
    shelf = Rectangle(
        (x, 3),
        1.5,
        8,
        facecolor='slategray',
        edgecolor='black'
    )
    ax.add_patch(shelf)

robot_1 = ax.plot(
    2, 2,
    marker='o',
    markersize=14,
    color='royalblue',
    label='Robot 1'
)[0]

robot_2 = ax.plot(
    6, 2,
    marker='o',
    markersize=14,
    color='forestgreen',
    label='Robot 2'
)[0]

robot_3 = ax.plot(
    10, 2,
    marker='o',
    markersize=14,
    color='darkorange',
    label='Robot 3'
)[0]

ax.set_title(
    "PULSE-Fleet | Autonomous Warehouse",
    fontsize=16,
    fontweight='bold'
)

ax.set_xlabel("X Position (meters)")
ax.set_ylabel("Y Position (meters)")

ax.legend(loc='upper right')

fleet_states = load_fleet_states()

robot_1_state = fleet_states.get("robot_1", {})
robot_1_offline = (
    time.time() - robot_1_state.get("last_seen", 0)
    > ROBOT_TIMEOUT
)

robot_1_status = robot_1_state.get("operating_status", "UNKNOWN")
robot_1_battery = robot_1_state.get("battery_percentage", 0.0)

robot_1_label = ax.text(
    2, 1.3,
    f"R1: {robot_1_status} | {robot_1_battery:.0f}%",
    fontsize=9,
    ha="center",
    color="royalblue"
)

robot_2_label = ax.text(
    6, 1.3,
    "R2: WAITING",
    fontsize=9,
    ha="center",
    color="forestgreen"
)

robot_3_label = ax.text(
    10, 1.3,
    "R3: WAITING",
    fontsize=9,
    ha="center",
    color="darkorange"
)

def update_visualization():
    fleet_states = load_fleet_states()
    robot_state = fleet_states.get("robot_1", {})

    robot_1_offline = (
        time.time() - robot_state.get("last_seen", 0)
        > ROBOT_TIMEOUT
    )

    status = robot_state.get("operating_status", "UNKNOWN")
    battery = robot_state.get("battery_percentage", 0.0)

    if robot_1_offline:
        robot_1_label.set_text("R1: OFFLINE")
    else:
        robot_1_label.set_text(f"R1: {status} | {battery:.0f}%")

    robot_2_state = fleet_states.get("robot_2", {})

    robot_2_offline = (
        time.time() - robot_2_state.get("last_seen", 0)
        > ROBOT_TIMEOUT
    )

    robot_2_status = robot_2_state.get("operating_status", "UNKNOWN")
    robot_2_battery = robot_2_state.get("battery_percentage", 0.0)

    if robot_2_offline:
        robot_2_label.set_text("R2: OFFLINE")
    else:
        robot_2_label.set_text(
            f"R2: {robot_2_status} | {robot_2_battery:.0f}%"
        )

    robot_3_state = fleet_states.get("robot_3", {})

    robot_3_offline = (
        time.time() - robot_3_state.get("last_seen", 0)
        > ROBOT_TIMEOUT
    )

    robot_3_status = robot_3_state.get("operating_status", "UNKNOWN")
    robot_3_battery = robot_3_state.get("battery_percentage", 0.0)

    if robot_3_offline:
        robot_3_label.set_text("R3: OFFLINE")
    else:
        robot_3_label.set_text(
            f"R3: {robot_3_status} | {robot_3_battery:.0f}%"
        )

    fig.canvas.draw_idle()

timer = fig.canvas.new_timer(interval=1000)
timer.add_callback(update_visualization)
timer.start()

plt.show()

