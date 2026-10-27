import math
import rclpy
from rclpy.node import Node
from pulse_fleet_interfaces.msg import (TaskAnnouncement, TaskBid, TaskAward, TaskAcknowledgment,
)

class AuctionAgent(Node):
    def __init__(self):
        super().__init__('auction_agent')
        self.declare_parameter('robot_id', 'robot_1')
        self.robot_id = self.get_parameter('robot_id').value
        self.received_bids = {}
        self.acknowledged_tasks = set()
        self.seen_tasks = set()
        self.auction_results = {}
        self.pending_awards = {}
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
        self.award_publisher = self.create_publisher(
            TaskAward, 
            '/fleet/task_awards', 
            10
        )
        
        self.ack_publisher = self.create_publisher(
            TaskAcknowledgment, 
            '/fleet/task_acknowledgments', 
            10
        )
        self.award_subscription = self.create_subscription(
            TaskAward,
            '/fleet/task_awards',
            self.award_callback,
            10
        )
        
        self.bid_subscription = self.create_subscription(
            TaskBid,
            '/fleet/task_bids',
            self.bid_callback,
            10
        )

    def task_callback(self, msg):
        if msg.task_id in self.seen_tasks:
            self.get_logger().info(
                f"[{self.robot_id}] Duplicate task {msg.task_id} ignored."
            )
            return

        self.seen_tasks.add(msg.task_id)
        
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
    
    def award_callback(self, msg):
        if msg.winner_id != self.robot_id:
            return
        if msg.task_id not in self.auction_results:
            self.pending_awards.setdefault(msg.task_id, []).append(msg)

            self.get_logger().info(
                f"[{self.robot_id}] Award for {msg.task_id} queued. "
                "Waiting for local auction result."
            )
            return
        
        expected_winner = self.auction_results[msg.task_id]

        if msg.winner_id != expected_winner:
            self.get_logger().warning(
                f"[{self.robot_id}] Conflicting award for {msg.task_id}: "
                f"received winner {msg.winner_id}, "
                f"expected {expected_winner}. Rejecting award."
            )
            return
        if msg.task_id in self.acknowledged_tasks:
                self.get_logger().info(
                f"[{self.robot_id}] Task {msg.task_id} already acknowledged. Ignoring duplicate award."
                )
                return

        self.acknowledged_tasks.add(msg.task_id)

        self.get_logger().info(
        f"[{self.robot_id}] Received award for task {msg.task_id}"
    )

        acknowledgment = TaskAcknowledgment()
        acknowledgment.task_id = msg.task_id
        acknowledgment.robot_id = self.robot_id
        acknowledgment.accepted = True
        acknowledgment.timestamp = self.get_clock().now().to_msg()

        self.ack_publisher.publish(acknowledgment)

        self.get_logger().info(
        f"[{self.robot_id}] Accepted task {msg.task_id}"
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

        self.auction_results[task_id] = winner_id

        pending_awards = self.pending_awards.pop(task_id, [])

        for pending_award in pending_awards:
            self.award_callback(pending_award)

        self.get_logger().info(
            f"[{self.robot_id}] Stored auction result for {task_id}: {winner_id}"
        )
        award = TaskAward()
        award.task_id = task_id
        award.winner_id = winner_id
        award.winning_cost = float(winning_cost)
        award.announcer_id = self.robot_id
        award.timestamp = self.get_clock().now().to_msg()

        self.award_publisher.publish(award)

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
