import math
import rclpy
from rclpy.node import Node
from pulse_fleet_interfaces.msg import TaskAnnouncement, TaskBid

class AuctionAgent(Node):
    def __init__(self):
        super().__init__('auction_agent')
        self.declare_parameter('robot_id', 'robot_1')
        self.robot_id = self.get_parameter('robot_id').value
        self.received_bids = {}
        self.declare_parameter('auction_duration', 2.0)
        self.auction_duration = self.get_parameter('auction_duration').value
        self.auction_timers = {}
        self.declare_parameter('position_x', 0.0)
        self.declare_parameter('position_y', 0.0)

        self.position_x = self.get_parameter('position_x').value
        self.position_y = self.get_parameter('position_y').value
        
        self.task_subscription = self.create_subscription(
            TaskAnnouncement,
            '/fleet/task_announcements',
            self.task_callback,
            10
        )
        self.bid_publisher = self.create_publisher(
            TaskBid,
            '/fleet/task_bids',
            10
        )
        self.bid_subscription = self.create_subscription(
            TaskBid,
            '/fleet/task_bids',
            self.bid_callback,
            10
        )

    def task_callback(self, msg):
        self.get_logger().info(
            f"[{self.robot_id}] Received task {msg.task_id} "
            f"at destination ({msg.goal_x:.1f}, {msg.goal_y:.1f})"
        )

        distance = math.hypot(
        msg.goal_x - self.position_x,
        msg.goal_y - self.position_y
        )

        self.get_logger().info(
        f"[{self.robot_id}] Distance to task {msg.task_id}: "
        f"{distance:.2f} meters"
        )
        bid = TaskBid()
        bid.task_id = msg.task_id
        bid.robot_id = self.robot_id
        bid.bid_cost = float(distance)
        bid.timestamp = self.get_clock().now().to_msg()

        self.bid_publisher.publish(bid)
        if msg.task_id not in self.auction_timers:
                timer = self.create_timer(
                self.auction_duration,
                lambda task_id=msg.task_id: self.evaluate_auction(task_id)
            )
        self.auction_timers[msg.task_id] = timer
       
    def bid_callback(self, msg):
        self.get_logger().info(
            f"[{self.robot_id}] Received bid from {msg.robot_id} "
            f"for task {msg.task_id}: {msg.bid_cost:.2f}"
        )
        if msg.task_id not in self.received_bids:
            self.received_bids[msg.task_id] = {}

        self.received_bids[msg.task_id][msg.robot_id] = msg.bid_cost
        self.get_logger().info(
            f"[{self.robot_id}] Stored bids for {msg.task_id}: "
            f"{self.received_bids[msg.task_id]}"
        )
    def evaluate_auction(self, task_id):
        # Stop the timer after its first execution
        timer = self.auction_timers.pop(task_id, None)
        if timer is not None:
            timer.cancel()

        # Retrieve the bids collected for this task
        bids = self.received_bids.get(task_id, {})

        if not bids:
            self.get_logger().warning(
                f"[{self.robot_id}] No bids received for {task_id}"
            )
            return

        # Select the lowest cost; use robot ID to break ties
        winner_id, winning_cost = min(
            bids.items(),
            key=lambda item: (item[1], item[0])
        )

        self.get_logger().info(
            f"[{self.robot_id}] Auction {task_id} completed. "
            f"Winner: {winner_id}, Cost: {winning_cost:.2f}"
        )
        
def main(args=None):
    rclpy.init(args=args)
    node = AuctionAgent()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
