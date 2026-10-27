
# PULSE-Fleet
### Decentralized Autonomous Warehouse Robot Fleet Management

PULSE-Fleet is an ongoing robotics software engineering project focused on decentralized coordination, distributed task allocation, and autonomous navigation for multiple autonomous mobile robots (AMRs) operating in a shared warehouse.

The project is developed using **ROS 2 Jazzy, Python, and Docker**, with an emphasis on fault-tolerant multi-robot communication and scalable software architecture.

**Current milestone:** Three independent ROS 2 State Managers communicate successfully, and a live warehouse dashboard monitors their status, battery levels, disconnections, and recovery.

---

## 1. Project Objectives

- Enable robots to coordinate without a centralized fleet controller.
- Implement decentralized communication and peer-state monitoring.
- Develop distributed task allocation using auction-based algorithms.
- Support autonomous navigation and coordinated task execution.
- Detect robot communication failures and recovery.
- Visualize multi-robot operations in 2D and, eventually, 3D.
- Evaluate the reliability and performance of decentralized fleet coordination.

---

## 2. System Architecture

Each robot is designed to operate three primary ROS 2 nodes.

### 2.1 State Manager — Implemented

The State Manager publishes the robot's own state and maintains information about other robots.

Implemented capabilities:

- Periodic heartbeats at approximately 1 Hz.
- Event-driven state updates.
- Peer-state monitoring.
- Stale-peer detection after approximately 3 seconds.
- Sequence numbers for message ordering.
- Session identifiers to distinguish robot restarts.
- Peer recovery when communication resumes.
- Independent operation across three robot instances.

### 2.2 Auction Agent — V1 Implemented and Tested

The Auction Agent enables decentralized task allocation in PULSE-Fleet using ROS 2 communication. Each robot independently receives warehouse tasks, calculates its bidding cost, exchanges bids with other robots, and determines the lowest-cost candidate without relying on a central auction server.

**Implemented capabilities (24 October 2026):**

- Shared warehouse task announcements through `/fleet/task_announcements`.
- Custom ROS 2 messages: `TaskAnnouncement.msg` and `TaskBid.msg`.
- Independent distance-based bid calculation using Euclidean distance.
- Bid publication and reception through `/fleet/task_bids`.
- Local bid storage organized by task ID and robot ID.
- Configurable auction collection window (default: 2 seconds).
- Independent minimum-cost winner selection with deterministic robot-ID tie-breaking.

**Bidding algorithm**

Each robot calculates the straight-line distance between its current position and the task destination:

\[
C_i = \sqrt{(x_g-x_i)^2+(y_g-y_i)^2}
\]

Where:

- \(C_i\) is Robot \(i\)'s bidding cost in meters.
- \((x_i,y_i)\) is the robot's position.
- \((x_g,y_g)\) is the task destination.

The robot with the lowest submitted cost is selected. Equal costs are resolved using robot IDs.

**Verified two-robot test — `task_007`**

Task destination: `(12.0, 8.0)` meters.

| Robot | Starting position | Calculated bid |
|---|---|---|
| robot_1 | (2.0, 2.0) | 11.6619 m |
| robot_2 | (10.0, 2.0) | 6.3246 m |

Both Auction Agents independently reported:

`Auction task_007 completed. Winner: robot_2, Cost: 6.32`

This demonstrates successful task announcement, bid exchange, bid storage, and basic decentralized winner computation.

**Current limitations and planned improvements**

- Task awards, acknowledgments, duplicate protection, and initial local conflict handling are implemented in V2; distributed consensus, durable commitments, and automatic task reassignment remain future work.

### 2.2.1 Auction Agent V2 — Task Awards, Acknowledgments and Validation

**Implemented and tested: 27 October 2026**

Extended the decentralized Auction Agent with task award publication, winner acknowledgments, duplicate-message protection, and local award validation.

**New ROS 2 interfaces**

- `TaskAward.msg` — communicates the selected winner, winning cost, announcing robot, task ID, and timestamp.
- `TaskAcknowledgment.msg` — communicates the acknowledging robot, task ID, acceptance status, and timestamp.

**New communication topics**

| Topic | Purpose |
|---|---|
| `/fleet/task_awards` | Publish auction winner decisions |
| `/fleet/task_acknowledgments` | Publish winning robot's acceptance |

**Implemented capabilities**

- Task award publication after local auction evaluation.
- Winning robot acknowledgment using `TaskAcknowledgment`.
- Duplicate-award protection using `acknowledged_tasks`.
- Duplicate-task-announcement protection using `seen_tasks`.
- Local auction winner tracking using `auction_results`.
- Conflicting-award detection and rejection when the received winner differs from the locally calculated winner.
- Early-arriving award storage using `pending_awards`.
- Replay and validation of queued awards after local auction evaluation.

**Verified integration tests**

| Test | Result |
|---|---|
| Task awards published by two independent Auction Agents | Passed |
| Winning robot acknowledgment — `task_010` | Passed |
| Duplicate acknowledgment protection — `task_011` | Passed |
| Duplicate task announcement protection — `task_012` | Passed |
| Normal auction with award validation — `task_013` | Passed |
| Conflicting award rejected by Robot 1 — `task_013` | Passed |
| Early award queued before auction completion — `task_014` | Passed |
| Pending award replay and acknowledgment — `task_014` | Passed |

**Verified auction example**

For a warehouse task at `(12.0, 8.0)`:

- `robot_1` at `(2.0, 2.0)` calculates a bid of approximately `11.66 m`.
- `robot_2` at `(10.0, 2.0)` calculates a bid of approximately `6.32 m`.
- Both agents select `robot_2`.
- The winning robot acknowledges the task once, even when duplicate awards arrive.

**Current limitations**

- Local winner validation is not a distributed consensus protocol.
- Different robots may calculate different winners if bids are delayed or lost.
- Duplicate protection and auction results are stored in memory and do not survive agent restarts.
- Task execution, completion feedback, timeout-based reassignment, and recovery from failed assignments are not yet implemented.
- Award validation currently checks awards addressed to the receiving robot; it does not establish fleet-wide agreement.
- Automated integration tests and fault-injection testing remain future work.

**Next priorities:** Reliable task commitment and failure recovery, followed by Navigation Controller integration and multi-robot simulation.

### 2.3 Navigation Controller — Planned

The Navigation Controller will handle robot movement and navigation.

Planned capabilities:

- Route and travel-cost estimation.
- Goal assignment and execution.
- Path planning and obstacle avoidance.
- Navigation feedback.
- Robot position updates.
- Integration with the Auction Agent for bid-cost estimation.

---

## 3. State Manager Communication Architecture

PULSE-Fleet uses a decentralized ROS 2 publish/subscribe architecture.

Each robot publishes its own state and subscribes to state messages from other robots through the shared topic:

`/fleet/robot_states`

![PULSE-Fleet State Manager Communication Architecture](State%20Manager%20Architecture.png)

*Figure 1. State Manager communication architecture showing three independent robot nodes exchanging state information through the shared ROS 2 topic. Heartbeats, session identifiers, sequence numbers, and timeout detection support peer monitoring and recovery.*

The shared topic provides communication infrastructure but does not act as a centralized fleet controller.

---

## 4. Custom ROS 2 Interface

The project defines a custom `RobotState.msg` interface.

```text
string robot_id
string session_id
uint64 sequence_number
float64 position_x
float64 position_y
float64 battery_percentage
string operating_status
string current_task_id
std_msgs/Header header

uint8 HEARTBEAT=0
uint8 STATE_CHANGE=1
uint8 update_type
```

The message contains robot identity, session information, state sequence, position, battery percentage, operating status, task assignment, timestamp, and update type.

Two update types are supported:

- `HEARTBEAT`: periodic state publication.
- `STATE_CHANGE`: immediate publication when relevant state changes.

---

## 5. Live Warehouse Visualization — Implemented

A lightweight 2D visualization has been developed using Python and Matplotlib.

The visualization includes:

- A warehouse layout measuring 20 × 14 meters.
- Four storage shelving sections.
- Three color-coded AMR markers.
- Live operating-status monitoring.
- Battery-percentage display.
- Automatic refresh approximately every second.
- Communication timeout detection.
- Automatic restoration of status after reconnection.

### Current Warehouse Visualization

![PULSE-Fleet Live Warehouse Visualization](Figure_1.png)

*Figure 2. PULSE-Fleet warehouse visualization showing three AMRs and four shelving sections. At the moment captured, Robot 1 is BUSY, Robot 2 is IDLE, and Robot 3 is BUSY, with all three reporting 100% battery. Operating statuses and battery readings are obtained from ROS 2 state messages through the fleet-state bridge. Robot positions are currently illustrative; autonomous movement and live position tracking have not yet been implemented.*

### Visualization Architecture

```text
Robot 1 State Manager ──┐
                       │
Robot 2 State Manager ──┼──> /fleet/robot_states
                       │              │
Robot 3 State Manager ──┘              ▼
                              FleetStateBridge
                                       │
                                       ▼
                                fleet_state.json
                                       │
                                       ▼
                              Matplotlib Dashboard
                                       │
                                       ▼
                          Live Fleet Status Monitoring
```

The `FleetStateBridge` subscribes to the ROS 2 fleet-state topic and writes the latest robot information into a shared JSON file.

The Matplotlib visualization reads this file and updates the dashboard automatically.

This architecture allows the ROS 2 application to run inside Docker while the graphical visualization runs directly on macOS.

---

## 6. Robot Offline Detection and Recovery

Each robot's latest received state message is timestamped by the fleet-state bridge.

The visualization calculates:

```text
Time Since Last Message = Current Time - Last Seen Time
```

If a robot has not published a message for more than approximately 3 seconds, the dashboard displays:

`OFFLINE`

When the robot resumes communication, the dashboard automatically displays its newly reported operating status.

### Verified Test

A communication-failure test was performed with Robot 2.

1. All three robots initially communicated normally.
2. Robot 2's State Manager was stopped.
3. Robot 2 was displayed as `OFFLINE`.
4. Robots 1 and 3 remained online.
5. Robot 2's State Manager was restarted.
6. Communication resumed and its status reappeared automatically.

**Result: Passed.**

This demonstrates independent communication-failure detection and recovery in the monitoring system.

It does not yet demonstrate automatic task reassignment, which is planned for the Auction Agent.

---

## 7. Technology Stack

| Technology | Purpose |
|---|---|
| ROS 2 Jazzy | Distributed robotics middleware |
| Python | Application and coordination logic |
| rclpy | ROS 2 Python client library |
| Custom ROS 2 messages | Robot-state communication |
| Docker | Containerized ROS 2 development |
| Matplotlib | Live 2D warehouse visualization |
| JSON | Data exchange between ROS 2 and visualization |
| Git | Version control |
| GitHub | Source-code hosting and documentation |
| macOS | Host development environment |

---

## 8. Current Development Status

### Phase 1 — ROS 2 Foundations and State Communication

**Completed**

- ROS 2 Jazzy development environment.
- Docker-based ROS 2 workspace.
- Custom `RobotState.msg` interface.
- State Manager Python package.
- Three independent State Manager instances.
- Shared ROS 2 state topic.
- Periodic heartbeat publication.
- Event-driven state updates.
- Sequence numbers and session identification.
- Peer-state monitoring.
- Stale-peer detection and recovery.

### Phase 2 — Fleet Monitoring and Visualization

**Completed**

- Basic 2D warehouse layout.
- Three robot markers.
- ROS 2-to-JSON state bridge.
- Live operating-status monitoring.
- Live battery-percentage monitoring.
- Independent robot offline detection.
- Automatic dashboard recovery after reconnection.

**Future improvements**

- Dynamic robot-position updates.
- More informative offline indicators.
- Atomic JSON file updates.
- Automated monitoring tests.
- Performance and reliability measurements.

### Phase 3 — Distributed Task Allocation

**Status: Auction Agent V1 and V2 implemented and manually tested — 27 October 2026**

**Completed**

- [x] Create custom `TaskAnnouncement.msg` and `TaskBid.msg` interfaces.
- [x] Implement the Auction Agent ROS 2 package.
- [x] Implement decentralized task announcements.
- [x] Calculate distance-based bidding costs.
- [x] Exchange and store bids between robots.
- [x] Implement deterministic minimum-cost winner selection.
- [x] Create `TaskAward.msg` and `TaskAcknowledgment.msg`.
- [x] Publish task awards and winning robot acknowledgments.
- [x] Prevent duplicate task announcements and acknowledgments.
- [x] Track locally calculated auction results.
- [x] Detect and reject locally conflicting awards.
- [x] Queue and replay early-arriving awards.
- [x] Manually validate the two-robot auction workflow.

**Remaining**

- [ ] Establish reliable fleet-wide agreement on task assignments.
- [ ] Implement task execution status and completion feedback.
- [ ] Implement task timeout, failure detection, and reassignment.
- [ ] Persist task state across robot restarts.
- [ ] Add automated integration and fault-injection tests.
- [ ] Integrate auction decisions with autonomous navigation.

### Phase 4 — Autonomous Navigation

**Planned**

- Robot motion simulation.
- Route planning and cost estimation.
- Navigation Controller integration.
- Obstacle avoidance.
- Simultaneous task execution.
- Coordination between navigation and auctions.

### Phase 5 — 3D Warehouse Demonstration

**Planned**

- Lightweight 3D warehouse simulation.
- Three simulated AMRs.
- Autonomous task execution.
- Fleet monitoring and coordination.
- A 30–45-second recorded demonstration.

---

## 9. Development Roadmap

- [x] Configure ROS 2 Jazzy and Docker.
- [x] Create the ROS 2 workspace.
- [x] Implement custom robot-state messages.
- [x] Develop the State Manager.
- [x] Launch three communicating State Manager instances.
- [x] Implement heartbeat and event-driven updates.
- [x] Implement peer monitoring and recovery.
- [x] Create the 2D warehouse visualization.
- [x] Connect live ROS 2 state data to the dashboard.
- [x] Verify robot disconnection and recovery.
- [x] Implement distributed task announcements.
- [x] Implement auction-based bidding.
- [x] Implement deterministic winner selection.
- [x] Implement task awards and acknowledgments.
- [x] Implement duplicate-announcement and duplicate-acknowledgment protection.
- [x] Implement local conflicting-award detection.
- [x] Implement early-award queuing and replay.
- [x] Validate Auction Agent V2 with two robot instances.
- [ ] Implement reliable fleet-wide task commitment.
- [ ] Implement task completion feedback and failure recovery.
- [ ] Implement automatic task reassignment.
- [ ] Integrate navigation and robot movement.
- [ ] Build the 3D warehouse simulation.
- [ ] Record the final demonstration.
- [ ] Conduct systematic performance evaluation.

---

## 10. Testing and Validation

### Auction Agent V2 — Integration Tests (27 October 2026)

The following tests were performed manually using two independent ROS 2 Auction Agent instances running inside Docker.

| Test | Task ID | Result |
|---|---|---|
| Decentralized bidding and winner selection | `task_008` | Passed |
| Task award publication by both agents | `task_009` | Passed |
| Task acknowledgment publication | `task_010` | Passed |
| Duplicate acknowledgment protection | `task_011` | Passed |
| Duplicate task announcement protection | `task_012` | Passed |
| Normal auction with local award validation | `task_013` | Passed |
| Conflicting award rejection | `task_013` | Passed |
| Early-arriving award queuing | `task_014` | Passed |
| Pending award replay and acknowledgment | `task_014` | Passed |

**Test configuration**

- Robot 1 position: `(2.0, 2.0)` meters.
- Robot 2 position: `(10.0, 2.0)` meters.
- Task destination: `(12.0, 8.0)` meters.
- Expected winner: `robot_2`.
- Winning bid: approximately `6.3246` meters.

**Observations**

Both robots independently selected `robot_2` during the normal auction tests. Duplicate task announcements were ignored, and repeated awards did not produce repeated acknowledgments. A deliberately conflicting award was rejected by Robot 1. An award received before the local auction completed was queued and subsequently processed.

**Validation scope**

These tests demonstrate the behavior of the implemented two-robot workflow under the tested conditions. They do not establish distributed consensus, reliable task execution, automatic reassignment, or robustness under network failures.

Automated regression tests, larger fleet experiments, and systematic fault-injection testing remain future work.

---

## 11. Latest Development Milestone

**27 October 2026 — Auction Agent V2: Reliable Message Handling and Local Award Validation**

Extended PULSE-Fleet's decentralized Auction Agent with task awards, acknowledgments, duplicate-message protection, and local award consistency checks.

**Key achievements**

- Introduced `TaskAward.msg` and `TaskAcknowledgment.msg`.
- Implemented task award publication and winner acknowledgment.
- Prevented repeated task announcements from generating duplicate bids.
- Prevented repeated awards from generating duplicate acknowledgments.
- Implemented local auction-result tracking and conflicting-award rejection.
- Implemented early-award queuing and replay after auction evaluation.
- Successfully tested the updated workflow with two independent ROS 2 Auction Agent instances.

**Validation results**

The integration tests confirmed that `robot_2` was selected for the warehouse task at `(12.0, 8.0)` and acknowledged its award. Duplicate announcements and acknowledgments were suppressed, a deliberately conflicting award was rejected, and an early-arriving award was queued and subsequently processed.

**Engineering status**

Auction Agent V2's planned functionality has been implemented and manually tested under the two-robot test configuration.

Fleet-wide consensus, persistent task commitments, automatic failure recovery, task reassignment, and autonomous navigation remain future development priorities.

---

## 12. Next Development Tasks

Following the successful implementation and manual validation of Auction Agent V2 on 27 October 2026, development will focus on reliable task commitments, fault tolerance, and autonomous navigation.

**Upcoming engineering priorities**

1. **Reliable task commitment:** Establish a fleet-wide mechanism for agreeing on task assignments, beyond local auction-result validation.
2. **Task execution lifecycle:** Introduce task states such as `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, and `FAILED`.
3. **Failure detection and reassignment:** Detect unsuccessful task execution and redistribute tasks when robots become unavailable.
4. **Persistent task tracking:** Preserve important assignment information across robot restarts.
5. **Navigation integration:** Connect the Auction Agent with the Navigation Controller and ROS 2 Nav2.
6. **Automated testing:** Introduce regression tests, conflicting-bid scenarios, communication-delay simulations, and fault-injection tests.
7. **Multi-robot simulation:** Extend validation to three or more robots and develop a 3D warehouse environment.

**Next major milestone:** Transition from decentralized task allocation to reliable autonomous task execution.

---

## 13. Project Limitations

PULSE-Fleet is an active robotics software engineering project. The State Manager, live warehouse visualization, and Auction Agent V1/V2 have been implemented and manually tested.

**Current limitations**

- Autonomous robot navigation and physical robot movement are not yet implemented.
- Auction bid costs use Euclidean distance rather than obstacle-aware navigation paths.
- Robot positions are configured through ROS 2 parameters rather than live localization.
- Local auction-result validation does not guarantee fleet-wide agreement or distributed consensus.
- Different robots may select different winners if bids are delayed, lost, or received inconsistently.
- Task assignment acknowledgments do not yet trigger autonomous task execution.
- Automatic task reassignment following robot failure is not implemented.
- Duplicate protection and auction results are maintained in memory and are lost when an agent restarts.
- Early-award queues do not yet have expiration or cleanup mechanisms.
- Multi-robot collision avoidance and 3D warehouse simulation are not yet implemented.
- Automated regression testing, fault-injection testing, and performance benchmarking remain future work.

**Current validation scope**

The Auction Agent V2 has been manually tested using two independent robot instances communicating through ROS 2 topics.

The current implementation demonstrates decentralized bidding, winner selection, award publication, acknowledgment, duplicate-message handling, and local award validation. It does not yet demonstrate fault-tolerant autonomous fleet operation.

---

## 14. Author

**Florian Muanda**

Robotics and AI Engineer

GitHub: https://github.com/flo-77

Portfolio: https://florian-muanda.netlify.app

---

**Project Status:** Active development.
