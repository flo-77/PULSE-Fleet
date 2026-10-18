import time
import uuid

import rclpy
from rclpy.node import Node
from pulse_fleet_interfaces.msg import RobotState


class StateManager(Node):
    def __init__(self):
        super().__init__('state_manager')

        self.declare_parameter('robot_id', 'robot_1')
        self.robot_id = self.get_parameter('robot_id').value

        self.position_x = 0.0
        self.position_y = 0.0
        self.battery_percentage = 100.0
        self.operating_status = 'IDLE'

        self.current_task_id = ''
        self.sequence_number = 0

        self.session_id = str(uuid.uuid4())

        self.state_publisher = self.create_publisher(
            RobotState,
            '/fleet/robot_states',
            10
        )

        self.heartbeat_timer = self.create_timer(
            1.0,
            self.publish_heartbeat
        )

        self.state_subscriber = self.create_subscription(
            RobotState,
            '/fleet/robot_states',
            self.handle_peer_state,
            10
        )

        self.peer_states = {}
        self.peer_last_seen = {}
        self.stale_peers = set()

        self.declare_parameter('peer_timeout', 3.0)
        self.peer_timeout = self.get_parameter('peer_timeout').value

        self.peer_monitor_timer = self.create_timer(
            1.0,
            self.check_peer_freshness
        )

    def publish_heartbeat(self):
        msg = RobotState()

        msg.robot_id = self.robot_id
        msg.session_id = self.session_id

        self.sequence_number += 1
        msg.sequence_number = self.sequence_number

        msg.position_x = self.position_x
        msg.position_y = self.position_y
        msg.battery_percentage = self.battery_percentage
        msg.operating_status = self.operating_status
        msg.current_task_id = self.current_task_id

        msg.update_type = RobotState.HEARTBEAT

        msg.header.stamp = self.get_clock().now().to_msg()

        self.state_publisher.publish(msg)

    def handle_peer_state(self, msg):
        if msg.robot_id == self.robot_id:
            return
     
        previous = self.peer_states.get(msg.robot_id)

        if previous is not None:
            if previous.session_id == msg.session_id:
                if msg.sequence_number <= previous.sequence_number:
                    return   
            else:
                if self.is_peer_fresh(msg.robot_id):
                    return

        self.peer_states[msg.robot_id] = msg
        self.peer_last_seen[msg.robot_id] = time.monotonic()

        if msg.robot_id in self.stale_peers:
            self.stale_peers.remove(msg.robot_id)
            self.get_logger().info(
                f"Peer {msg.robot_id} is FRESH again"
            )

        self.get_logger().info(f"Received state from {msg.robot_id}")

    def is_peer_fresh(self, robot_id):
        last_seen = self.peer_last_seen.get(robot_id)

        if last_seen is None:
            return False
        
        elapsed_time = time.monotonic() - last_seen
        return elapsed_time <= self.peer_timeout
    
    def check_peer_freshness(self):
        for robot_id in self.peer_states:
            if not self.is_peer_fresh(robot_id):
                if robot_id not in self.stale_peers:
                    self.stale_peers.add(robot_id)
                    self.get_logger().warning(
                        f"Peer {robot_id} is STALE"
                    )

def main(args=None):
    rclpy.init(args=args)
    node = StateManager()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()







