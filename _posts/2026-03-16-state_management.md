---
layout: single
title: "State Management"
header:
  teaser: /assets/images/posts/state_management.png
date: 2026-03-16
classes: wide
author_profile: false
---

# JointStateManager: Bridging the Hardware-Planning Gap

The `JointStateManager` is the node that aggregates two namespace-isolated arms into a single coherent system state. Without it, MoveIt2 cannot plan for both arms simultaneously. 

---

## Purpose

I had prevoiusly assumed that MoveIt2 could talk directly to the Niryo NED2 hardware drivers. On paper this is reasonable: MoveIt2 supports `ros2_control`, the NED2 ships with ROS2 drivers, and the connection should be straightforward. It is not.

The Niryo drivers publish joint states under namespace-relative topics using **unprefixed** joint names:

```
/arm_1/joint_states  → {name: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6]}
/arm_2/joint_states  → {name: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6]}
```

MoveIt2's `PlanningSceneMonitor` requires a single `/joint_states` topic with **prefixed** names covering the full robot:

```
/joint_states → {name: [arm_1_joint_1, ..., arm_1_joint_6, arm_2_joint_1, ..., arm_2_joint_6]}
```

There is no parameter in `moveit_controllers.yaml` or `moveit_py_params.yaml` that makes MoveIt2 accept namespaced hardware topics directly.

---

## Approaches Considered

Three options were evaluated before settling on the custom aggregation node.

### Option 1: ROS2 Topic Remapping

ROS2 supports remapping topics at launch:

```bash
ros2 run niryo_ned2_driver driver_node --ros-args \
  --remap /arm_1/joint_states:=/joint_states
```

This collapses arm_1's topic onto `/joint_states`. The problem: arm_2 publishes the same joint names (`joint_1`…`joint_6`). When both arms are remapped to the same topic, the second publisher's messages overwrite the first at the subscriber. The planning scene sees only one arm's state. MoveIt2 has no knowledge of the second arm's configuration and plans as if it does not exist. Rejected.

### Option 2: Per-Arm Robot State Publishers

Each arm could be given its own Robot State Publisher and its own `move_group` instance running in a separate namespace:

```
/arm_1/move_group  → planning scene contains only arm_1 geometry
/arm_2/move_group  → planning scene contains only arm_2 geometry
```

This works for single-arm planning. It does not work for a shared workspace. With two independent planning scenes, there is no mechanism for arm_1's planner to check whether its planned trajectory collides with arm_2's current position. Each planner can independently generate trajectories that are collision-free for its own arm and unsafe when both arms execute concurrently. For a system where the arms' reach envelopes overlap by design, this is not acceptable. Rejected.

### Option 3: Custom Aggregation Node

An approach that can satisfy all constraints simultaneously should have:

- **Single `/joint_states` topic**: one consumer (the Robot State Publisher)
- **Prefixed names**: `arm_1_joint_1`…`arm_2_joint_6` as required by MoveIt2
- **Single RSP and single `move_group`**: shared planning scene, shared collision world, inter-arm collision checking by construction

This is what `JointStateManager` implements.

---

## Implementation

```python
# src/mars_ned2_bringup/mars_ned2_bringup/joint_state_manager.py

import threading
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointStateManager(Node):
    def __init__(self):
        super().__init__('joint_state_manager')

        self.arm_states = {'arm_1': None, 'arm_2': None}
        self.lock = threading.Lock()

        # Subscribe to both arms' hardware state streams
        self.sub_1 = self.create_subscription(
            JointState, '/arm_1/joint_states',
            lambda msg: self.callback(msg, 'arm_1'), 10)
        self.sub_2 = self.create_subscription(
            JointState, '/arm_2/joint_states',
            lambda msg: self.callback(msg, 'arm_2'), 10)

        # Publish unified state on the topic MoveIt2 and RSP expect
        self.pub = self.create_publisher(JointState, '/joint_states', 10)

        # Timer-driven publication at 15 Hz
        self.timer = self.create_timer(1 / 15.0, self.publish_unified)

    def callback(self, msg, arm_name):
        with self.lock:
            prefixed = JointState()
            prefixed.name = [f'{arm_name}_{j}' for j in msg.name]
            prefixed.position = msg.position
            prefixed.velocity = msg.velocity
            prefixed.effort = msg.effort
            self.arm_states[arm_name] = prefixed

    def publish_unified(self):
        with self.lock:
            # Startup guard: withhold until both arms have reported at least once
            if None in self.arm_states.values():
                return

            unified = JointState()
            unified.header.stamp = self.get_clock().now().to_msg()
            for state in self.arm_states.values():
                unified.name.extend(state.name)
                unified.position.extend(state.position)
                unified.velocity.extend(state.velocity)
                unified.effort.extend(state.effort)

            # Inject passive joints absent from the hardware driver
            unified.name.extend(PASSIVE_JOINTS)
            unified.position.extend([0.0] * len(PASSIVE_JOINTS))
            unified.velocity.extend([0.0] * len(PASSIVE_JOINTS))
            unified.effort.extend([0.0] * len(PASSIVE_JOINTS))

        self.pub.publish(unified)


PASSIVE_JOINTS = [
    'arm_1_mors_1', 'arm_1_mors_2',
    'arm_2_mors_1', 'arm_2_mors_2',
]


def main():
    rclpy.init()
    node = JointStateManager()
    rclpy.spin(node)
    rclpy.shutdown()
```

The translation is symmetric. The forward path prefixes hardware names before merging; if MoveIt2 later generates a trajectory for `arm_1`, the joint names carry the `arm_1_` prefix and the `TrajectoryProxy` strips it before forwarding to the hardware controller.

---


## The MORS Passive Joints

The Niryo NED2 dual arm URDF describes four passive joints for the gripper mechanism (`arm_1_mors_1`, `arm_1_mors_2`, `arm_2_mors_1`, `arm_2_mors_2`). These joints are not actuated and the hardware driver does not publish values for them. however the URDF describes the full mechanical model including passive linkages for full collision avoidnace, while the driver publishes only the actuated joints it controls.

Without the injection, RSP logs:

```
[robot_state_publisher]: Missing joint state for arm_1_mors_1
```

RSP stops computing transforms for the sub-tree downstream of the missing joint. The gripper links, including the tool frame that MoveIt2 uses as the planning end-effector, are excluded from the TF tree. MoveIt2's IK solver cannot resolve Cartesian goals because the tool frame has no known transform relative to the robot base. The fix is to inject these joints at fixed zero values on every publish cycle. They are passive; zero is always physically correct.

The result: `/joint_states` carries 16 DOF at 15 Hz (12 active joints plus 4 passive MORS joints), providing RSP with a complete state to compute the full TF tree.

---

## Why 15 Hz

The NED2 hardware drivers publish at approximately 50 Hz. The `JointStateManager` publishes at 15 Hz, lower than the source rate, by design.

At 15 Hz, the planning scene may reflect a robot configuration up to 66.7 ms stale at the moment planning begins. This is set by `publish_frequency: 15.0` in `mars_ned2.launch.py`.

The relevant constraint is not the source rate but the planning-to-execution window. OMPL planning for our dual-arm trajectory takes 100–500 ms. so 67 ms is well within that window meaning by the time the planner returns a trajectory, the scene will have been updated at least once since planning started. Increasing the rate above 15 Hz would add CPU overhead to both the manager and the `PlanningSceneMonitor` without improving planning accuracy, since the hardware is the resolution ceiling.

---

## Design Philosophy 

The design goal is that no downstream consumer requires modification. MoveIt2, the Robot State Publisher, and RViz2 all receive standard ROS2 messages on standard topic names. The namespace complexity, two arms, two namespaces, two naming conventions, is fully contained within the `JointStateManager`.
---


