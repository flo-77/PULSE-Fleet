# PULSE-Fleet
### Decentralized Autonomous Warehouse Robot Fleet Management

PULSE-Fleet is an ongoing robotics software project exploring decentralized coordination, task allocation, and navigation for autonomous mobile robots operating in a shared warehouse environment.

The system is being developed using ROS 2 Jazzy and Python.

## Project Objectives

- Enable robots to communicate directly without a centralized fleet controller.
- Develop distributed task allocation using auction-based algorithms.
- Implement real-time robot state sharing and peer monitoring.
- Support autonomous warehouse navigation and task execution.
- Visualize multi-robot operations in a simulated warehouse.

## System Architecture

Each robot will operate three primary ROS 2 nodes:

### 1. State Manager
Publishes robot status and maintains information about other robots.

Planned capabilities:
- Periodic heartbeats at 1 Hz
- Event-driven state updates
- Peer-state monitoring
- Stale-peer detection after 3 seconds
- Sequence numbers and session identification

### 2. Auction Agent
Coordinates decentralized task allocation through distributed bidding and deterministic winner selection.

### 3. Navigation Controller
Handles route estimation, navigation planning, and motion execution.

## Technology Stack

- ROS 2 Jazzy
- Python (rclpy)
- Custom ROS 2 interfaces
- Docker
- Git and GitHub
- Lightweight 2D warehouse visualization (planned)

## Current Development Status

**Phase 1 — ROS 2 Foundations**

Completed:
- ROS 2 development environment configured
- ROS 2 workspace created
- Custom RobotState.msg designed
- Interface package successfully built and verified
- State Manager Python package initialized

In progress:
- Basic State Manager implementation

## Development Roadmap

1. Basic robot state publisher
2. Warehouse visualization with three robots
3. Initial robot movement along predefined routes
4. Decentralized peer-state communication
5. Distributed auction-based task allocation
6. Autonomous navigation and coordinated execution
7. System testing, evaluation, and optimization

## Project Status

PULSE-Fleet is under active development. Features described in the roadmap are planned unless explicitly marked as completed.
## State Manager Communication Architecture

PULSE-Fleet is designed as a decentralized multi-robot system using ROS 2. Each robot operates its own State Manager node and exchanges state information through a shared publish/subscribe topic.

![PULSE-Fleet State Manager Communication Architecture](State%20Manager%20Communication%20Architecture.png)


*Figure 1. State Manager communication architecture showing three robot nodes connected through the shared `/fleet/robot_states` topic. Each State Manager publishes its own state and monitors peer communication using heartbeats, session identifiers, sequence numbers, and timeout detection.*

## Author

Florian Muanda

Robotics and AI Engineer