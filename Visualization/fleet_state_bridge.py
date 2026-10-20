import time
import json
from pathlib import Path

import rclpy
from rclpy.node import Node
from pulse_fleet_interfaces.msg import RobotState

class FleetStateBridge(Node):

    def __init__(self):
        super().__init__('fleet_state_bridge')

        self.robot_states = {}
        self.output_path = Path(
            '/workspace/visualization/fleet_state.json'
        )


        self.subscription = self.create_subscription(
            RobotState,
            '/fleet/robot_states',
            self.state_callback,
            10
        )

    def state_callback(self, msg):

        self.robot_states[msg.robot_id] = {
            "robot_id": msg.robot_id,
            "last_seen": time.time(),
            "position_x": msg.position_x,
            "position_y": msg.position_y,
            "battery_percentage": msg.battery_percentage,
            "operating_status": msg.operating_status,
            "session_id": msg.session_id,
            "sequence_number": msg.sequence_number
        }

        with self.output_path.open('w') as file:
            json.dump(self.robot_states, file, indent=4)

        self.get_logger().info(
            f"Received state from {msg.robot_id}: "
            f"status={msg.operating_status}, "
            f"battery={msg.battery_percentage:.1f}%"
        )

def main():
    rclpy.init()

    node = FleetStateBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

