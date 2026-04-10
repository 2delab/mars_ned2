---
layout: single
title: "The Trajectory Proxy "
date: 2026-03-20
classes: wide
author_profile: false
---

# Distributing trajectories 

MoveIt2 generates trajectories for a unified 12-DOF robot. The hardware expects two separate 6-DOF trajectory commands, delivered to independent action servers in different namespaces. The `TrajectoryProxy` is the layer that performs this translation — splitting, stripping, and dispatching planned trajectories to the correct hardware controllers.

---

## The Problem

After planning, MoveIt2 produces a `RobotTrajectory` containing waypoints for all joints in the planning group. For the `dual` group, this is 12 joint positions per waypoint, named with prefixes:

```
trajectory.joint_names = [
    'arm_1_joint_1', 'arm_1_joint_2', ..., 'arm_1_joint_6',
    'arm_2_joint_1', 'arm_2_joint_2', ..., 'arm_2_joint_6'
]
trajectory.points = [
    {positions: [a1j1, a1j2, ..., a1j6, a2j1, a2j2, ..., a2j6], time_from_start: t},
    ...
]
```

The Niryo hardware action server at `/arm_1/joint_trajectory_controller/follow_joint_trajectory` expects:

```
trajectory.joint_names = ['joint_1', 'joint_2', ..., 'joint_6']  # no prefix
trajectory.points = [
    {positions: [j1, j2, j3, j4, j5, j6], time_from_start: t},
    ...
]
```

Two mismatches: wrong topic namespace, wrong joint names.

---

## The TrajectoryProxy Architecture

```
MoveIt2 executor
      │
      │  RobotTrajectory (12-DOF, prefixed joint names)
      ▼
TrajectoryProxy
      │
      ├── split()    → arm_1 trajectory (6-DOF, prefixed)
      │                + arm_2 trajectory (6-DOF, prefixed)
      │
      ├── strip()    → arm_1 trajectory (6-DOF, unprefixed: 'joint_1'...'joint_6')
      │                + arm_2 trajectory (6-DOF, unprefixed)
      │
      ├── dispatch arm_1 → /arm_1/joint_trajectory_controller/follow_joint_trajectory
      └── dispatch arm_2 → /arm_2/joint_trajectory_controller/follow_joint_trajectory
```

---

## Implementation

```python
# Pseudocode: TrajectoryProxy

class TrajectoryProxy:
    def __init__(self, node):
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
            # Dispatch sequentially, as fast as possible
            future_1 = self.arm_1_client.send_goal_async(arm_1_traj)
            future_2 = self.arm_2_client.send_goal_async(arm_2_traj)
            # Wait for both to complete
            rclpy.spin_until_future_complete(node, future_1)
            rclpy.spin_until_future_complete(node, future_2)

        elif mode == 'async':
            # Dispatch to both; do not wait
            self.arm_1_client.send_goal_async(arm_1_traj)
            self.arm_2_client.send_goal_async(arm_2_traj)

    def _extract_arm(self, robot_trajectory, arm_name):
        prefix = f'{arm_name}_'
        traj = JointTrajectory()

        # Filter joint names belonging to this arm, strip prefix
        indices = [
            i for i, name in enumerate(robot_trajectory.joint_names)
            if name.startswith(prefix)
        ]
        traj.joint_names = [
            robot_trajectory.joint_names[i].removeprefix(prefix)
            for i in indices
        ]

        # Extract corresponding positions from each waypoint
        for point in robot_trajectory.points:
            new_point = JointTrajectoryPoint()
            new_point.positions = [point.positions[i] for i in indices]
            new_point.time_from_start = point.time_from_start
            traj.points.append(new_point)

        return traj
```

---

## The Dispatch Latency

The proxy dispatches to arm_1 first, then arm_2. Both `send_goal_async` calls are non-blocking, so the inter-arm dispatch time is the time between the two calls — typically 1–5 ms in practice, but dependent on ROS2 executor load.

On hardware, each `send_goal_async` initiates a network round-trip through the ROSBridge WebSocket. The actual inter-arm start offset measured on the Niryo NED2 is 20–50 ms. This is the source of the phase shift observable in the synchronised motion results — not a planning error, but a hardware communication constraint.

---

## Per-Arm Trajectory for Async Mode

For asynchronous mode, each arm is planned individually and produces its own 6-DOF trajectory. The proxy's `_extract_arm` method is still used (to strip prefixes), but splitting is not needed because each trajectory already contains only one arm's joints.

```python
# Pseudocode: async single-arm execution via proxy
arm_1_traj = plan_result_arm_1.trajectory   # already 6-DOF, prefixed
arm_2_traj = plan_result_arm_2.trajectory   # already 6-DOF, prefixed

# Strip and dispatch independently in parallel threads
thread_1 = Thread(target=proxy.execute_single, args=(arm_1_traj, 'arm_1'))
thread_2 = Thread(target=proxy.execute_single, args=(arm_2_traj, 'arm_2'))
thread_1.start(); thread_2.start()
thread_1.join(); thread_2.join()
```

---

## Why This Pattern Exists

The `TrajectoryProxy` pattern encapsulates a hardware-specific concern — namespace and joint name conventions — that would otherwise propagate through every layer of the application code. Without it, every planning call would need to manually split trajectories, strip prefixes, and manage action client dispatch. With it, the application layer deals only with `RobotTrajectory` objects and coordination mode semantics.

This is the standard adapter pattern applied to robotics: translate between the planning stack's representation and the hardware stack's interface at a single well-defined boundary.
