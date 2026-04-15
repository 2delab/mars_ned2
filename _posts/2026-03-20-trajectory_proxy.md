---
layout: single
title: "The Trajectory Proxy"
header:
  teaser: /assets/images/posts/trajectory_proxy.png
date: 2026-03-20
classes: wide
author_profile: false
---

# The Trajectory Proxy: Bridging MoveIt2 and Hardware Controllers

MoveIt2 generates trajectories for a unified 12-DOF robot with prefixed joint names. The Niryo NED2 hardware expects two separate 6-DOF trajectory commands, delivered to independent action servers, with unprefixed joint names. The `TrajectoryProxy` is the node that bridges this gap: it splits, strips, and dispatches planned trajectories to the correct hardware controllers.


---

## Why MoveIt2's Built-In Execution Cannot Handle This

The natural approach is to call `execute()` directly through MoveIt2 and let `TrajectoryExecutionManager` handle dispatch:

```python
moveit_py_dual.execute(plan_result.trajectory, controllers=[])
```

`controllers=[]` tells `TrajectoryExecutionManager` to select controllers automatically by matching the trajectory's joint list against registered entries in `moveit_controllers.yaml`. For a standard single-robot setup, this works correctly: the trajectory's joint names match the controller's configured joint names and the dispatch succeeds.

For MARS, it fails at two points.

**First:** the hardware action servers are at namespaced paths:
```
/arm_1/joint_trajectory_controller/follow_joint_trajectory
/arm_2/joint_trajectory_controller/follow_joint_trajectory
```
`TrajectoryExecutionManager` resolves controller names to action server endpoints. Namespaced paths require explicit registration in `moveit_controllers.yaml`. This is configurable, but it only solves the routing problem.

**Second, and not configurable:** the trajectory joint names are prefixed (`arm_1_joint_1`, `arm_1_joint_2`, …) because that is what MoveIt2 produces from its unified 12-DOF model. The Niryo hardware action server at `/arm_1/joint_trajectory_controller/follow_joint_trajectory` expects unprefixed names (`joint_1`, `joint_2`, …) It will reject any goal where the joint names do not match exactly. `TrajectoryExecutionManager` has no prefix-stripping step. There is no configuration knob that adds one.

The `TrajectoryProxy` node performs the single transformation as `TrajectoryExecutionManager` cannot strip the prefix before forwarding.

---

## What the Proxy Does

```
MoveIt2 executor
      │
      │  RobotTrajectory (12-DOF, prefixed joint names)
      ▼
TrajectoryProxy
      │
      ├── _extract_arm('arm_1')   → 6-DOF trajectory, prefix stripped
      ├── _extract_arm('arm_2')   → 6-DOF trajectory, prefix stripped
      │
      ├── dispatch → /arm_1/joint_trajectory_controller/follow_joint_trajectory
      └── dispatch → /arm_2/joint_trajectory_controller/follow_joint_trajectory
```

The extraction is index-based: find all positions in the joint name list that start with the arm's prefix, slice the waypoint position arrays at those indices, strip the prefix from the names. The trajectory shape (number of waypoints, timestamps, velocity profiles) is preserved exactly.

---

## Implementation

```python
# src/mars_ned2_bringup/mars_ned2_bringup/trajectory_proxy.py

import rclpy
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class TrajectoryProxy:
    def __init__(self, node):
        self.node = node
        self.arm_1_client = ActionClient(
            node,
            FollowJointTrajectory,
            '/arm_1/joint_trajectory_controller/follow_joint_trajectory'
        )
        self.arm_2_client = ActionClient(
            node,
            FollowJointTrajectory,
            '/arm_2/joint_trajectory_controller/follow_joint_trajectory'
        )

    def execute(self, robot_trajectory, mode='sync'):
        arm_1_traj = self._extract_arm(robot_trajectory, 'arm_1')
        arm_2_traj = self._extract_arm(robot_trajectory, 'arm_2')

        if mode == 'sync':
            # Send both goals; serialises acceptance handshake, not execution
            future_1 = self.arm_1_client.send_goal_async(arm_1_traj)
            future_2 = self.arm_2_client.send_goal_async(arm_2_traj)
            rclpy.spin_until_future_complete(self.node, future_1)
            rclpy.spin_until_future_complete(self.node, future_2)
            goal_handle_1 = future_1.result()
            goal_handle_2 = future_2.result()
            if not goal_handle_1.accepted:
                self.node.get_logger().error('arm_1 goal rejected by hardware controller')
            if not goal_handle_2.accepted:
                self.node.get_logger().error('arm_2 goal rejected by hardware controller')

        elif mode == 'async':
            # Fire and forget; caller manages concurrency via threads
            self.arm_1_client.send_goal_async(arm_1_traj)
            self.arm_2_client.send_goal_async(arm_2_traj)

    def execute_single(self, robot_trajectory, arm_name):
        """Strip and dispatch a single arm's trajectory. Used in async threaded execution."""
        traj = self._extract_arm(robot_trajectory, arm_name)
        client = self.arm_1_client if arm_name == 'arm_1' else self.arm_2_client
        future = client.send_goal_async(traj)
        rclpy.spin_until_future_complete(self.node, future)
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error(
                f'{arm_name} goal rejected by hardware controller'
            )
            return
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self.node, result_future)

    def _extract_arm(self, robot_trajectory, arm_name):
        prefix = f'{arm_name}_'
        traj = JointTrajectory()

        # Collect indices of joints belonging to this arm
        indices = [
            i for i, name in enumerate(robot_trajectory.joint_names)
            if name.startswith(prefix)
        ]
        # Strip prefix from joint names
        traj.joint_names = [
            robot_trajectory.joint_names[i].removeprefix(prefix)
            for i in indices
        ]

        # Extract the corresponding position slice from each waypoint
        for point in robot_trajectory.points:
            new_point = JointTrajectoryPoint()
            new_point.positions = [point.positions[i] for i in indices]
            new_point.time_from_start = point.time_from_start
            traj.points.append(new_point)

        return traj
```

---

## The Sync Mode Dispatch: Acceptance vs. Execution

`send_goal_async` is non-blocking: both goal messages are sent to their respective hardware controllers before either `spin_until_future_complete` call. The futures resolve when the hardware controller acknowledges receipt and accepts the goal, the initial handshake. They do not resolve when the trajectory finishes executing.

```python
future_1 = self.arm_1_client.send_goal_async(arm_1_traj)
future_2 = self.arm_2_client.send_goal_async(arm_2_traj)
rclpy.spin_until_future_complete(self.node, future_1)
rclpy.spin_until_future_complete(self.node, future_2)
```

This means: both arms receive their goal goals as quickly as the network allows. The `spin_until_future_complete(future_1)` before `spin_until_future_complete(future_2)` only serialises the Python thread that is waiting for acknowledgements. The hardware controllers begin executing their trajectories as soon as they accept the goal, regardless of which acknowledgement the Python thread is waiting for.

The practical consequence: both arms start executing nearly simultaneously, but the start of arm_2's execution lags arm_1's by the time it takes for the ROSBridge WebSocket to complete a round-trip for each goal. The offset is set at dispatch and is constant for the duration of the trajectory. Both arms execute at the same rate; they are simply offset in time by the dispatch latency.

This is an irreducible consequence of dispatching two independent goals over a network stack. Both arms receive the same time-parameterised trajectory from the `dual` planner and execute it at the same speed; the offset between them is the inter-dispatch interval.

---

## Async Mode: Per-Arm Execution in Parallel Threads

For asynchronous mode, each arm is planned independently and produces its own 6-DOF trajectory. The proxy's `_extract_arm` method is still used to strip prefixes, but splitting is not needed because each trajectory already contains only one arm's joints. `execute_single` is dispatched in parallel threads:

```python
from threading import Thread

# Both trajectories are already 6-DOF, prefixed (arm_1_ prefix on arm_1's joints)
thread_1 = Thread(target=proxy.execute_single, args=(plan_result_arm_1.trajectory, 'arm_1'))
thread_2 = Thread(target=proxy.execute_single, args=(plan_result_arm_2.trajectory, 'arm_2'))
thread_1.start()
thread_2.start()
thread_1.join()
thread_2.join()
```

Each thread blocks on `spin_until_future_complete` independently. The arms execute concurrently at the hardware level. There is no shared clock, no common trajectory, no synchronisation constraint.

---

## Failure Handling 

### Goal rejection

If the hardware controller rejects a goal (`goal_handle.accepted == False`), the proxy logs the error. In sync mode, both goals have already been dispatched before either acknowledgement is checked. A rejection from arm_1 does not cancel arm_2's goal, and vice versa. This is a deliberate choice: partial execution is preferable to a silent no-op, and the planning layer that called the proxy is responsible for deciding how to handle the failure.

### Action server unavailability

The current implementation does not call `wait_for_server()` before dispatching. If the hardware action server is not running, for example if the Niryo driver has not started or the ROSBridge connection has dropped, `send_goal_async` will block indefinitely. Adding a `wait_for_server(timeout_sec=5.0)` guard before dispatch is the correct fix. This is listed as a known gap in the future work.

### Execution timeout

Once a goal is accepted, the proxy monitors wall-clock time against a configurable timeout (`trajectory_timeout_sec: 120.0`). If exceeded, the proxy cancels the goal and aborts:

```python
elapsed = (self.get_clock().now() - start_time).nanoseconds / 1e9
if elapsed > self.traj_timeout:
    hw_goal_handle.cancel_goal_async()
    goal_handle.abort()
```

This is the only execution-time check. It catches the case of a stalled hardware controller or a disconnected driver but does not detect anything about the robot's actual motion.

### Open-loop execution

Once the goal is accepted by the hardware controller, MoveIt2 and the proxy are out of the loop. The Niryo controller tracks the trajectory waypoints using its internal PID. The planning scene continues updating from `/joint_states` at 15 Hz during execution, but nothing reads the planning scene for execution safety. An obstacle added to the scene after planning completes will not halt execution. A joint state drift that puts the robot on a collision course mid-trajectory will not be detected.

This is not specific to the `TrajectoryProxy`. It is an architectural property of MoveIt2's execution layer: GitHub issue moveit/moveit#2631 identifies that the `ExecuteTrajectory` action capability bypasses `PlanExecution` and goes directly to `TrajectoryExecutionManager`, which does not include collision monitoring. The planning guarantee, that the trajectory was collision-free in the planning scene at planning time, is the only guarantee the system provides.

---

## Plan for improvement 

**Pre-dispatch state validation.** The proxy currently dispatches a trajectory without first checking whether the robot's actual joint state matches the trajectory's planned start state. If the robot has moved between the planning call completing and the dispatch, for example due to a stale joint state in the planning scene, a manual joint move during debugging, or a ROSBridge retransmit causing the previous command to replay, the hardware controller receives a goal whose start state does not match where the robot actually is. It interpolates from the current position to the first waypoint, which produces a jerk or a hardware fault depending on the magnitude of the discrepancy. A check of the form `current_state - trajectory.points[0].positions < threshold` before `send_goal_async` would catch this before it reaches the hardware.

**Simultaneous goal dispatch.** The sequential acceptance handshake imposes a 20–50 ms floor on inter-arm start timing that is irreducible within the current software stack. The proximate cause is the ROSBridge WebSocket round-trip latency. This could be eliminated by a hardware-level synchronisation signal, a shared trigger that both controllers respond to simultaneously rather than two independent goal messages arriving in sequence. Within the ROS2/MoveIt2 stack as deployed, the 20–50 ms offset is a fixed cost of the architecture.
